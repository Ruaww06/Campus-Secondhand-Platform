from sqlalchemy import Index
from app import db


class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = (
        Index('idx_region', 'region'),
        {'mysql_charset': 'utf8mb4'}
    )

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    student_id = db.Column(db.String(20), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    wechat = db.Column(db.String(50), nullable=True)
    region = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum('user', 'admin'), default='user')
    status = db.Column(db.Enum('active', 'banned'), default='active')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # === 成员B补充区域：User relationship ===
    goods = db.relationship('Goods', backref='seller', lazy=True)
    orders_buyer = db.relationship('OrderInfo', foreign_keys='OrderInfo.buyer_id',
                                   backref='buyer', lazy=True)
    orders_seller = db.relationship('OrderInfo', foreign_keys='OrderInfo.seller_id',
                                    backref='seller', lazy=True)
    # === 成员B补充结束 ===
