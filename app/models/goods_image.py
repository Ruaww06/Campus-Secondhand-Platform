from sqlalchemy import CheckConstraint, Index
from app import db


class GoodsImage(db.Model):
    __tablename__ = 'goods_image'
    __table_args__ = (
        CheckConstraint('is_main IN (0, 1)', name='chk_is_main_bool'),
        Index('idx_goods', 'goods_id'),
        {'mysql_charset': 'utf8mb4'}
    )

    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.goods_id', ondelete='CASCADE'),
                         nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_main = db.Column(db.SmallInteger, default=0)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # A完整负责
    # goods relationship 已在 Goods 中通过 backref 定义
