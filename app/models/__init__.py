from flask_sqlalchemy import SQLAlchemy
from app import create_app

# 注意：db 实例在 app/__init__.py 中创建并 init_app
# 此处仅做重新导出，方便模型文件导入
from app import db

from app.models.user import User
from app.models.category import Category
from app.models.goods import Goods
from app.models.goods_image import GoodsImage
from app.models.order import OrderInfo
from app.models.favorite import Favorite
from app.models.review import Review
from app.models.admin_log import AdminLog

__all__ = [
    'db', 'User', 'Category', 'Goods', 'GoodsImage',
    'OrderInfo', 'Favorite', 'Review', 'AdminLog'
]
