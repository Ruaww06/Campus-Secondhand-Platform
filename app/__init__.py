import importlib
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
csrf = CSRFProtect()


def create_app(config_override=None):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object('app.config.Config')
    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    csrf.init_app(app)

    # 全局错误处理
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # 自动激活已存在的蓝图模块
    _modules = ['goods', 'auth', 'order', 'favorite', 'review', 'admin']
    for mod_name in _modules:
        try:
            mod = importlib.import_module(f'app.{mod_name}')
            mod.init_app(app)
        except ImportError:
            pass  # 模块尚未创建，跳过

    # 模板全局函数
    @app.template_global()
    def condition_class(condition_level):
        mapping = {
            'new': 'bg-success',
            'like_new': 'bg-info',
            'used': 'bg-warning',
            'old': 'bg-secondary'
        }
        return mapping.get(condition_level, 'bg-secondary')

    @app.template_global()
    def is_favorited(goods_id):
        from flask import session
        from app.models import Favorite
        user_id = session.get('user_id')
        if not user_id:
            return False
        return Favorite.query.filter_by(user_id=user_id, goods_id=goods_id).first() is not None

    @app.template_global()
    def get_reviews_by_goods(goods_id):
        from app.models import Review, OrderInfo
        return Review.query.join(OrderInfo).filter(
            OrderInfo.goods_id == goods_id
        ).order_by(Review.created_at.desc()).all()

    # 上下文处理器：注入分类列表
    @app.context_processor
    def inject_categories():
        try:
            from app.models import Category
            categories = Category.query.order_by(Category.sort_order.asc()).all()
        except Exception:
            categories = []
        return dict(categories=categories)

    return app
