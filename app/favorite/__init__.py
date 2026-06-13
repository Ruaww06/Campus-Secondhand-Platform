from flask import Blueprint

favorite_bp = Blueprint('favorite', __name__, url_prefix='/favorite')


def init_app(app):
    from flask import session
    from app.models import Favorite

    @app.template_global()
    def is_favorited(goods_id):
        if 'user_id' not in session:
            return False
        return Favorite.query.filter_by(
            user_id=session['user_id'], goods_id=goods_id
        ).first() is not None

    from . import routes
    app.register_blueprint(favorite_bp)
