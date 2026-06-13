from flask import Blueprint

order_bp = Blueprint('order', __name__, url_prefix='/order')


def init_app(app):
    from . import routes
    app.register_blueprint(order_bp)
