from sqlalchemy import Index
from app import db


class AdminLog(db.Model):
    __tablename__ = 'admin_log'
    __table_args__ = (
        Index('idx_admin', 'admin_id'),
        Index('idx_action', 'action'),
        Index('idx_target', 'target_type', 'target_id'),
        Index('idx_created_at', 'created_at'),
        {'mysql_charset': 'utf8mb4'}
    )

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'),
                         nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # === 成员C补充区域：AdminLog relationship ===
    admin = db.relationship('User', backref='admin_logs')
    # === 成员C补充结束 ===
