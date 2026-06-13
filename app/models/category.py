from app import db


class Category(db.Model):
    __tablename__ = 'category'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # A完整负责
    goods = db.relationship('Goods', backref='category', lazy=True)
