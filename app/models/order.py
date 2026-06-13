from sqlalchemy import Index
from app import db


class OrderInfo(db.Model):
    __tablename__ = 'order_info'
    __table_args__ = (
        Index('idx_buyer', 'buyer_id'),
        Index('idx_seller', 'seller_id'),
        Index('idx_goods', 'goods_id'),
        Index('idx_status', 'status'),
        {'mysql_charset': 'utf8mb4'}
    )

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(50), nullable=False, unique=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                         nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                          nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.goods_id', ondelete='CASCADE'),
                         nullable=False)
    status = db.Column(db.Enum('pending', 'confirmed', 'completed', 'cancelled'),
                       default='pending')
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # === 成员B补充区域：OrderInfo relationship ===
    goods = db.relationship('Goods', backref='orders', lazy=True)
    review = db.relationship('Review', back_populates='order', uselist=False, lazy=True)
    # === 成员B补充结束 ===
