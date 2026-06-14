"""test_favorite.py — 收藏、取消收藏、收藏列表、防重复、AJAX 模式。"""

import json

import pytest

from tests.conftest import create_user, create_category, create_goods, create_favorite, login_user
from app.models import Favorite


class TestFavorite:
    def test_add_favorite_creates_record(self, client):
        """收藏商品 → 记录落库。"""
        user = create_user()
        goods = create_goods(create_user(), category=create_category())
        login_user(client, user)

        resp = client.post('/favorite/add', data={'goods_id': str(goods.goods_id)},
                           follow_redirects=True)

        assert resp.status_code == 200
        fav = Favorite.query.filter_by(user_id=user.user_id,
                                       goods_id=goods.goods_id).first()
        assert fav is not None

    def test_duplicate_favorite_rejected(self, client):
        """重复收藏同一商品 → 拒绝。"""
        user = create_user()
        goods = create_goods(create_user(), category=create_category())
        create_favorite(user, goods)
        login_user(client, user)

        resp = client.post('/favorite/add', data={'goods_id': str(goods.goods_id)},
                           follow_redirects=True)

        assert resp.status_code == 200
        assert Favorite.query.filter_by(user_id=user.user_id,
                                        goods_id=goods.goods_id).count() == 1

    def test_remove_favorite_deletes_record(self, client):
        """取消收藏 → 记录删除。"""
        user = create_user()
        goods = create_goods(create_user(), category=create_category())
        create_favorite(user, goods)
        login_user(client, user)

        resp = client.post('/favorite/remove',
                           data={'goods_id': str(goods.goods_id)},
                           follow_redirects=True)

        assert resp.status_code == 200
        assert Favorite.query.filter_by(user_id=user.user_id,
                                        goods_id=goods.goods_id).first() is None

    def test_view_favorite_list(self, client):
        """查看收藏列表。"""
        user = create_user()
        goods = create_goods(create_user(), category=create_category())
        create_favorite(user, goods)
        login_user(client, user)

        resp = client.get('/favorite/my')

        assert resp.status_code == 200
        assert goods.title in resp.get_data(as_text=True)

    def test_ajax_add_returns_json(self, client):
        """AJAX 收藏请求 → 返回 JSON。"""
        user = create_user()
        goods = create_goods(create_user(), category=create_category())
        login_user(client, user)

        resp = client.post('/favorite/add',
                           data={'goods_id': str(goods.goods_id)},
                           headers={'X-Requested-With': 'XMLHttpRequest'})

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data.get('success') is True
