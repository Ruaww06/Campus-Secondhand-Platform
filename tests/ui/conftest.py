"""UI 测试 — Playwright + pytest-flask live_server。

核心原则：
- live_server 运行在独立线程，无法共享测试线程的数据库事务
- 因此 _prepare_* 使用独立引擎连接 + READ COMMITTED 直接提交到 MySQL
- 测试间通过 TRUNCATE 表实现隔离（而非事务回滚）

运行：pytest tests/ui/ -v
"""

import secrets

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import create_app, db as _db
from app.models import User, Category, Goods, AdminLog

# 测试数据库 URI
TEST_DB_URI = 'mysql+pymysql://root:@localhost:3306/campus_secondhand_test'

# 所有需要截断的表（按外键依赖顺序：先子后父）
TRUNCATE_ORDER = [
    'admin_log', 'review', 'favorite', 'goods_image',
    'order_info', 'goods', 'category', 'user',
]


# =============================================================================
# 独立引擎 —— 绕过测试会话，直接操作 MySQL
# =============================================================================

def _independent_engine():
    return create_engine(TEST_DB_URI, isolation_level='READ COMMITTED')


def _raw_session():
    return sessionmaker(bind=_independent_engine())()


# =============================================================================
# Session 级 fixture
# =============================================================================

@pytest.fixture(scope='session')
def app():
    _app = create_app(config_override={
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': TEST_DB_URI,
        'LIVESERVER_PORT': 5555,
        'SQLALCHEMY_ENGINE_OPTIONS': {'pool_pre_ping': True},
    })
    with _app.app_context():
        _db.create_all()
    yield _app
    with _app.app_context():
        _db.drop_all()


# =============================================================================
# 每测试前后：截断所有表
# =============================================================================

@pytest.fixture(autouse=True)
def _table_cleanup(app):
    """测试前截断所有表，确保干净起点。"""
    with app.app_context():
        engine = create_engine(
            TEST_DB_URI,
            pool_pre_ping=True,
            pool_recycle=300,  # 5 分钟回收连接，防止 timeout
        )
        with engine.connect() as conn:
            # 禁用外键检查以便截断
            conn.exec_driver_sql('SET FOREIGN_KEY_CHECKS = 0')
            for table in TRUNCATE_ORDER:
                conn.exec_driver_sql(f'TRUNCATE TABLE `{table}`')
            conn.exec_driver_sql('SET FOREIGN_KEY_CHECKS = 1')
            conn.commit()
        engine.dispose()
    yield


# =============================================================================
# 数据准备函数（通过独立连接直接写入 MySQL，live_server 可见）
# =============================================================================

def _prepare_user(app, username=None, password='password123', role='user',
                  status='active'):
    """创建用户，返回 (user_id, username)。"""
    from werkzeug.security import generate_password_hash
    if username is None:
        username = f'ui_user_{secrets.token_hex(4)}'

    session = _raw_session()
    user = User(
        username=username,
        password=generate_password_hash(password),
        real_name='UI 测试用户',
        student_id=f'STU_UI_{secrets.token_hex(6).upper()}',
        phone='13800000000',
        region='北区',
        role=role,
        status=status,
    )
    session.add(user)
    session.commit()
    uid = user.user_id
    session.close()
    session.bind.dispose()
    return uid, username


def _prepare_category(app, name=None):
    """创建分类，返回 category_id。"""
    if name is None:
        name = f'UI分类_{secrets.token_hex(4)}'

    session = _raw_session()
    cat = Category(category_name=name, sort_order=0)
    session.add(cat)
    session.commit()
    cid = cat.category_id
    session.close()
    session.bind.dispose()
    return cid


def _prepare_goods(app, seller_id, category_id=None, title=None,
                   status='on_sale'):
    """创建商品，返回 goods_id。"""
    if title is None:
        title = f'UI商品_{secrets.token_hex(4)}'

    session = _raw_session()
    if category_id is None:
        cat = session.query(Category).first()
        category_id = cat.category_id if cat else _prepare_category(app)
    goods = Goods(
        seller_id=seller_id,
        category_id=category_id,
        title=title,
        price=99.00,
        region='北区',
        condition_level='new',
        status=status,
    )
    session.add(goods)
    session.commit()
    gid = goods.goods_id
    session.close()
    session.bind.dispose()
    return gid
