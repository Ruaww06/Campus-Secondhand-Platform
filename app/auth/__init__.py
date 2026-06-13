from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_app(app):
    from . import routes
    app.register_blueprint(auth_bp)
