from flask import Blueprint

goods_bp = Blueprint('goods', __name__, url_prefix='/')


def init_app(app):
    from . import routes
    app.register_blueprint(goods_bp)
