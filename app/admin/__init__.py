from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def init_app(app):
    from . import routes
    app.register_blueprint(admin_bp)
