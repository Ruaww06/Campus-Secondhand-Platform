from sqlalchemy import Index
from sqlalchemy.ext.hybrid import hybrid_property
from app import db


class Goods(db.Model):
    __tablename__ = 'goods'
    __table_args__ = (
        Index('idx_seller', 'seller_id'),
        Index('idx_category', 'category_id'),
        Index('idx_region', 'region'),
        Index('idx_status', 'status'),
        Index('idx_price', 'price'),
        Index('idx_created_at', 'created_at'),
        {'mysql_charset': 'utf8mb4'}
    )

    goods_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                          nullable=False)
    category_id = db.Column(db.Integer,
                            db.ForeignKey('category.category_id', ondelete='RESTRICT'),
                            nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    original_price = db.Column(db.Numeric(10, 2), nullable=True)
    region = db.Column(db.String(50), nullable=False)
    condition_level = db.Column(db.Enum('new', 'like_new', 'used', 'old'), default='used')
    status = db.Column(db.Enum('on_sale', 'sold', 'off_shelf'), default='on_sale')
    view_count = db.Column(db.Integer, default=0)
    contact_phone = db.Column(db.String(15), nullable=True)
    contact_wechat = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # A完整负责的relationship
    images = db.relationship('GoodsImage', backref='goods', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='GoodsImage.sort_order')

    @hybrid_property
    def main_image_url(self):
        """返回主图路径，无图返回None。"""
        for img in self.images:
            if img.is_main:
                return img.image_url
        if self.images:
            return self.images[0].image_url
        return None

    @property
    def condition_label(self):
        """返回中文新旧程度标签。"""
        mapping = {
            'new': '全新',
            'like_new': '几乎全新',
            'used': '轻微使用',
            'old': '明显使用'
        }
        return mapping.get(self.condition_level, '未知')
