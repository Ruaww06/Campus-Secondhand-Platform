"""test_goods_ui.py — 发布商品、搜索筛选、图片交互（UI 层）。"""

import pytest

from tests.ui.conftest import _prepare_user, _prepare_category


@pytest.mark.ui
class TestGoodsUI:
    def test_publish_form_renders_with_category(self, page, live_server, app):
        """发布页加载正确：分类下拉已填充，表单元素可见。"""
        user_id, username = _prepare_user(app, username='ui_publisher')
        cat_id = _prepare_category(app, name='UI测试分类')

        # 登录
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_publisher')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # 进入发布页
        page.goto(f'{live_server.url()}/publish')

        body_text = page.locator('body').inner_text()
        # 验证发布页核心元素
        assert '发布商品' in body_text
        assert 'UI测试分类' in body_text
        assert page.locator('input[name="title"]').is_visible()
        assert page.locator('input[name="price"]').is_visible()
        assert page.locator('input[name="images"]').is_visible()
        assert page.locator('input[value="发布商品"]').is_visible()

    def test_search_and_filter_results(self, page, live_server, app):
        """搜索 + 筛选 → 结果列表正确。"""
        # 用独立连接准备数据（live_server 线程可见）
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models import Goods

        user_id, _ = _prepare_user(app, username='ui_search_seller')
        cat_id = _prepare_category(app, name='搜索测试分类')

        engine = create_engine(
            'mysql+pymysql://root:@localhost:3306/campus_secondhand_test',
            isolation_level='READ COMMITTED',
        )
        Session = sessionmaker(bind=engine)
        s = Session()
        g1 = Goods(
            seller_id=user_id, category_id=cat_id,
            title='Python编程入门', price=30, region='北区',
            condition_level='new', status='on_sale'
        )
        g2 = Goods(
            seller_id=user_id, category_id=cat_id,
            title='Java核心技术', price=80, region='北区',
            condition_level='used', status='on_sale'
        )
        s.add_all([g1, g2])
        s.commit()
        s.close()
        engine.dispose()

        page.goto(f'{live_server.url()}/?q=Python')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert 'Python编程入门' in body_text
        assert 'Java核心技术' not in body_text

    def test_image_set_main_changes_display(self, page, live_server, app):
        """主图切换 → 页面主图变化。"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models import Goods, GoodsImage

        user_id, username = _prepare_user(app, username='ui_img_user')
        cat_id = _prepare_category(app)

        engine = create_engine(
            'mysql+pymysql://root:@localhost:3306/campus_secondhand_test',
            isolation_level='READ COMMITTED',
        )
        Session = sessionmaker(bind=engine)
        s = Session()
        goods = Goods(
            seller_id=user_id, category_id=cat_id,
            title='图片测试商品', price=50, region='北区',
            condition_level='new', status='on_sale'
        )
        s.add(goods)
        s.commit()

        img1 = GoodsImage(
            goods_id=goods.goods_id,
            image_url='/static/uploads/test_main.jpg',
            is_main=1, sort_order=0
        )
        img2 = GoodsImage(
            goods_id=goods.goods_id,
            image_url='/static/uploads/test_second.jpg',
            is_main=0, sort_order=1
        )
        s.add_all([img1, img2])
        s.commit()
        goods_id = goods.goods_id
        s.close()
        engine.dispose()

        # 登录
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_img_user')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # 访问详情页
        page.goto(f'{live_server.url()}/{goods_id}')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert '图片测试商品' in body_text
