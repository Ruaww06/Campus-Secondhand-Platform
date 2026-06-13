from sqlalchemy import Index, UniqueConstraint
from app import db


class Favorite(db.Model):
    __tablename__ = 'favorite'
    __table_args__ = (
        UniqueConstraint('user_id', 'goods_id', name='uk_user_goods'),
        Index('idx_goods', 'goods_id'),
        {'mysql_charset': 'utf8mb4'}
    )

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                        nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.goods_id', ondelete='CASCADE'),
                         nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # === 成员C补充区域：Favorite relationship ===
    user = db.relationship('User', backref='favorites')
    goods = db.relationship('Goods', backref='favorites')
    # === 成员C补充结束 ===
