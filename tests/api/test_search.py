"""test_search.py — 首页列表、搜索筛选、排序、分页、详情页。"""

import pytest

from tests.conftest import create_user, create_category, create_goods, login_user


class TestSearch:
    def test_home_lists_on_sale_goods(self, client):
        """首页只列出 on_sale 商品。"""
        seller = create_user()
        cat = create_category()
        g1 = create_goods(seller, category=cat, title='已上架商品', price=10)
        g2 = create_goods(seller, category=cat, title='已下架商品', price=20,
                          status='off_shelf')
        g3 = create_goods(seller, category=cat, title='已售商品', price=30,
                          status='sold')

        resp = client.get('/')
        text = resp.get_data(as_text=True)

        assert '已上架商品' in text
        assert '已下架商品' not in text
        assert '已售商品' not in text

    def test_keyword_search(self, client):
        """关键词搜索匹配标题。"""
        seller = create_user()
        cat = create_category()
        create_goods(seller, category=cat, title='Python编程书')
        create_goods(seller, category=cat, title='Java入门')

        resp = client.get('/?q=Python')

        text = resp.get_data(as_text=True)
        assert 'Python编程书' in text
        assert 'Java入门' not in text

    def test_filter_by_category(self, client):
        """按分类筛选。"""
        seller = create_user()
        cat_a = create_category(name='教材')
        cat_b = create_category(name='电子产品')
        create_goods(seller, category=cat_a, title='高等数学')
        create_goods(seller, category=cat_b, title='机械键盘')

        resp = client.get(f'/?category_id={cat_a.category_id}')

        text = resp.get_data(as_text=True)
        assert '高等数学' in text
        assert '机械键盘' not in text

    def test_filter_by_price_range(self, client):
        """按价格区间筛选。"""
        seller = create_user()
        cat = create_category()
        create_goods(seller, category=cat, title='便宜货', price=5)
        create_goods(seller, category=cat, title='中等', price=50)
        create_goods(seller, category=cat, title='贵', price=200)

        resp = client.get('/?min_price=10&max_price=100')

        text = resp.get_data(as_text=True)
        assert '中等' in text
        assert '便宜货' not in text
        assert '贵' not in text

    def test_sort_by_price_asc(self, client):
        """按价格升序排列。"""
        seller = create_user()
        cat = create_category()
        create_goods(seller, category=cat, title='贵商品', price=200)
        create_goods(seller, category=cat, title='便宜商品', price=10)

        resp = client.get('/?sort=price_asc')
        text = resp.get_data(as_text=True)

        idx_cheap = text.find('便宜商品')
        idx_exp = text.find('贵商品')
        assert idx_cheap != -1 and idx_exp != -1
        assert idx_cheap < idx_exp

    def test_detail_page_view_count_increments(self, client):
        """详情页 → view_count +1。"""
        seller = create_user()
        goods = create_goods(seller, category=create_category())
        old_count = goods.view_count

        client.get(f'/{goods.goods_id}')

        from app.models import Goods
        assert Goods.query.get(goods.goods_id).view_count == old_count + 1

    def test_detail_page_shows_related_goods(self, client):
        """详情页展示同分类相关推荐（排除自身）。"""
        seller = create_user()
        cat = create_category()
        g1 = create_goods(seller, category=cat, title='目标商品')
        g2 = create_goods(seller, category=cat, title='相关商品')

        resp = client.get(f'/{g1.goods_id}')
        text = resp.get_data(as_text=True)

        assert '相关商品' in text

    def test_search_params_preserved_in_form(self, client):
        """搜索参数回填到搜索表单。"""
        resp = client.get('/?q=test&region=北区&sort=price_desc')
        text = resp.get_data(as_text=True)

        assert 'value="test"' in text
        # 区域 select 应选中
        assert '北区' in text
