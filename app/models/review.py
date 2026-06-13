from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from app import db


class Review(db.Model):
    __tablename__ = 'review'
    __table_args__ = (
        UniqueConstraint('order_id', name='uk_order'),
        CheckConstraint('rating BETWEEN 1 AND 5', name='chk_rating_range'),
        Index('idx_seller', 'seller_id'),
        Index('idx_reviewer', 'reviewer_id'),
        {'mysql_charset': 'utf8mb4'}
    )

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order_info.order_id', ondelete='CASCADE'),
                         nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                            nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                          nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # === 成员C补充区域：Review relationship ===
    order = db.relationship('OrderInfo', back_populates='review', uselist=False)
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='reviews_received')
    # === 成员C补充结束 ===
