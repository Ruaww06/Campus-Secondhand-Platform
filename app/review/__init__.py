from flask import Blueprint

review_bp = Blueprint('review', __name__, url_prefix='/review')


def init_app(app):
    from . import routes
    app.register_blueprint(review_bp)
