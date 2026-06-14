"""全链路 E2E 测试 — 共享 fixtures 与工厂函数。

所有测试用例彻底独立：每个用例通过事务回滚（SAVEPOINT + ROLLBACK）隔离。
"""

import secrets

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash

from app import create_app
from app import db as _db
from app.models import (
    User, Category, Goods, GoodsImage, OrderInfo, Favorite, Review, AdminLog
)


# =============================================================================
# Session 级 fixtures
# =============================================================================

@pytest.fixture(scope='session')
def app():
    """创建 Flask app，切到独立测试库，建表。Session 级仅执行一次。"""
    _app = create_app(config_override={
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI':
            'mysql+pymysql://root:@localhost:3306/campus_secondhand_test',
    })
    with _app.app_context():
        _db.create_all()
    yield _app
    with _app.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def _transaction(app):
    """每个测试函数运行在一个数据库事务中，函数结束时自动回滚。

    实现原理：
    1. 开启一个真实的数据库连接和事务
    2. 将 db.session 替换为绑定到该连接的新 scoped_session
    3. 测试结束后回滚事务，数据库恢复到测试前状态
    """
    connection = _db.engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    _db.session = scoped_session(session_factory)

    yield

    _db.session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    """Flask test client。"""
    with app.test_client() as c:
        yield c


# =============================================================================
# Session 操作辅助
# =============================================================================

def login_user(client, user):
    """绕过登录表单，直接在 session 中设置用户身份。"""
    with client.session_transaction() as sess:
        sess['user_id'] = user.user_id
        sess['username'] = user.username
        sess['role'] = user.role


def login_admin(client, admin_user):
    """绕过登录表单，设置管理员 session。"""
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user.user_id
        sess['username'] = admin_user.username
        sess['role'] = 'admin'


# =============================================================================
# 工厂函数 — 每个工厂创建一条记录并 commit
# =============================================================================

def create_user(username=None, password='password123', role='user',
                status='active', **kwargs):
    """创建用户。username 为 None 时自动生成唯一用户名。"""
    if username is None:
        username = f'user_{secrets.token_hex(5)}'
    user = User(
        username=username,
        password=generate_password_hash(password),
        real_name=kwargs.get('real_name', 'Test User'),
        student_id=kwargs.get('student_id',
                              f'STU_{secrets.token_hex(6).upper()}'),
        phone=kwargs.get('phone', '13800000000'),
        email=kwargs.get('email', None),
        wechat=kwargs.get('wechat', None),
        region=kwargs.get('region', '北区'),
        role=role,
        status=status,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


def create_category(name=None, sort_order=0):
    """创建分类。name 为 None 时自动生成唯一分类名。"""
    if name is None:
        name = f'分类_{secrets.token_hex(4)}'
    cat = Category(
        category_name=name,
        description=f'{name} 的描述',
        sort_order=sort_order,
    )
    _db.session.add(cat)
    _db.session.commit()
    return cat


def create_goods(seller, category=None, title=None, price=99.00,
                 status='on_sale', **kwargs):
    """创建商品。category 为 None 时自动创建分类。"""
    if category is None:
        category = create_category()
    if title is None:
        title = f'商品_{secrets.token_hex(4)}'
    goods = Goods(
        seller_id=seller.user_id,
        category_id=category.category_id,
        title=title,
        description=kwargs.get('description', ''),
        price=price,
        original_price=kwargs.get('original_price', None),
        region=kwargs.get('region', '北区'),
        condition_level=kwargs.get('condition_level', 'new'),
        status=status,
        contact_phone=kwargs.get('contact_phone', None),
        contact_wechat=kwargs.get('contact_wechat', None),
    )
    _db.session.add(goods)
    _db.session.commit()
    return goods


def create_goods_image(goods, image_url=None, is_main=0, sort_order=0):
    """为商品创建一条图片记录（不写物理文件）。"""
    if image_url is None:
        image_url = f'/static/uploads/goods_{goods.goods_id}/test_{secrets.token_hex(4)}.jpg'
    img = GoodsImage(
        goods_id=goods.goods_id,
        image_url=image_url,
        is_main=is_main,
        sort_order=sort_order,
    )
    _db.session.add(img)
    _db.session.commit()
    return img


def create_order(buyer, goods, status='pending', remark=None):
    """创建订单。自动生成唯一 order_no。goods 状态见业务逻辑调整。"""
    order_no = f'TEST_{secrets.token_hex(8)}'
    order = OrderInfo(
        order_no=order_no,
        buyer_id=buyer.user_id,
        seller_id=goods.seller_id,
        goods_id=goods.goods_id,
        status=status,
        remark=remark,
    )
    _db.session.add(order)
    _db.session.commit()
    return order


def create_favorite(user, goods):
    """收藏商品。"""
    fav = Favorite(
        user_id=user.user_id,
        goods_id=goods.goods_id,
    )
    _db.session.add(fav)
    _db.session.commit()
    return fav


def create_review(order, reviewer, rating=5, content='好评'):
    """为订单创建评价。reviewer 必须是订单的买家。"""
    review = Review(
        order_id=order.order_id,
        reviewer_id=reviewer.user_id,
        seller_id=order.seller_id,
        rating=rating,
        content=content,
    )
    _db.session.add(review)
    _db.session.commit()
    return review


def create_admin_log(admin_user, action, target_type=None, target_id=None,
                     detail=None):
    """创建管理员操作日志。"""
    log = AdminLog(
        admin_id=admin_user.user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    _db.session.add(log)
    _db.session.commit()
    return log


# =============================================================================
# 常用数据工厂快捷函数
# =============================================================================

def create_test_users():
    """创建一组测试用户，返回 (买家, 卖家, 管理员)。"""
    buyer = create_user(username=f'buyer_{secrets.token_hex(4)}')
    seller = create_user(username=f'seller_{secrets.token_hex(4)}')
    admin = create_user(username=f'admin_{secrets.token_hex(4)}', role='admin')
    return buyer, seller, admin


def create_trade_chain(status='completed'):
    """创建一条完整交易链路，返回 (买家, 卖家, 商品, 订单)。

    status 可选: 'pending', 'confirmed', 'completed', 'cancelled'
    """
    seller = create_user(username=f'seller_{secrets.token_hex(4)}')
    buyer = create_user(username=f'buyer_{secrets.token_hex(4)}')
    cat = create_category()
    goods = create_goods(seller, category=cat, status='on_sale')
    order = create_order(buyer, goods, status=status)
    # 根据状态调整 goods.status
    if status in ('pending', 'confirmed'):
        goods.status = 'sold'
    elif status == 'cancelled':
        goods.status = 'on_sale'
    elif status == 'completed':
        goods.status = 'sold'
    _db.session.commit()
    return buyer, seller, goods, order
