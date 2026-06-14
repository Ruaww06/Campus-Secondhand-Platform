"""test_goods.py — 发布、编辑、上下架、图片管理。

覆盖 ER 关系: R1 发布, R8 分类, R9 图片管理
"""

import json
from io import BytesIO

import pytest

from tests.conftest import (
    create_user, create_category, create_goods, create_goods_image, login_user
)
from app.models import Goods, GoodsImage


class TestPublish:
    def test_publish_with_image_success(self, client):
        """上传图片 + 发布 → goods on_sale 落库。"""
        user = create_user()
        cat = create_category()
        login_user(client, user)

        data = {
            'title': '新商品',
            'price': '99.00',
            'category_id': str(cat.category_id),
            'region': '北区',
            'condition_level': 'new',
            'description': '描述内容',
        }
        data['images'] = (BytesIO(b'fake-jpeg-data'), 'photo.jpg')

        resp = client.post('/publish', data=data,
                           content_type='multipart/form-data',
                           follow_redirects=False)

        goods = Goods.query.filter_by(title='新商品').first()
        assert goods is not None, "商品应落库"
        assert goods.status == 'on_sale'
        assert goods.seller_id == user.user_id
        assert len(goods.images) >= 1
        assert any(img.is_main for img in goods.images)
        assert resp.status_code == 302

    def test_publish_without_image_fails(self, client):
        """未传图 → 拒绝，停留在发布页。"""
        user = create_user()
        cat = create_category()
        login_user(client, user)

        resp = client.post('/publish', data={
            'title': '无图商品',
            'price': '9.99',
            'category_id': str(cat.category_id),
            'region': '北区',
            'condition_level': 'new',
        }, follow_redirects=True)

        assert '至少上传一张' in resp.get_data(as_text=True)
        assert Goods.query.filter_by(title='无图商品').first() is None


class TestEdit:
    def test_seller_can_edit_own_goods(self, client):
        """卖家编辑自己商品 → 字段更新。"""
        user = create_user()
        goods = create_goods(user, title='旧标题', price=50)
        login_user(client, user)

        client.post(f'/{goods.goods_id}/edit', data={
            'title': '新标题',
            'price': '88.88',
            'category_id': str(goods.category_id),
            'region': '南区',
            'condition_level': 'like_new',
        }, follow_redirects=True)

        g = Goods.query.get(goods.goods_id)
        assert g.title == '新标题'
        assert str(g.price) == '88.88'
        assert g.region == '南区'
        assert g.condition_level == 'like_new'

    def test_non_seller_cannot_edit(self, client):
        """非卖家编辑 → 重定向到 /my。"""
        owner = create_user()
        other = create_user()
        goods = create_goods(owner)
        login_user(client, other)

        resp = client.post(f'/{goods.goods_id}/edit', data={
            'title': '篡改',
            'price': '1.00',
            'category_id': str(goods.category_id),
            'region': '北区',
            'condition_level': 'old',
        }, follow_redirects=True)

        assert '无权编辑' in resp.get_data(as_text=True)
        assert Goods.query.get(goods.goods_id).title != '篡改'


class TestStatusToggle:
    def test_off_shelf(self, client):
        """下架商品 → status = off_shelf。"""
        user = create_user()
        goods = create_goods(user)
        login_user(client, user)

        client.post(f'/{goods.goods_id}/off_shelf', follow_redirects=True)

        assert Goods.query.get(goods.goods_id).status == 'off_shelf'

    def test_re_list(self, client):
        """重新上架 → status = on_sale。"""
        user = create_user()
        goods = create_goods(user, status='off_shelf')
        login_user(client, user)

        client.post(f'/{goods.goods_id}/on_sale', follow_redirects=True)

        assert Goods.query.get(goods.goods_id).status == 'on_sale'

    def test_non_seller_cannot_off_shelf(self, client):
        """非卖家下架 → 拒绝。"""
        owner = create_user()
        other = create_user()
        goods = create_goods(owner)
        login_user(client, other)

        client.post(f'/{goods.goods_id}/off_shelf', follow_redirects=True)

        assert Goods.query.get(goods.goods_id).status == 'on_sale'


class TestImageManagement:
    def test_add_image_increases_count(self, client):
        """追加图片 → 图片数量 +1。"""
        user = create_user()
        goods = create_goods(user)
        create_goods_image(goods, is_main=1)
        login_user(client, user)
        old_count = len(goods.images)

        data = {}
        data['images'] = (BytesIO(b'fake-data'), 'added.jpg')
        resp = client.post(
            f'/{goods.goods_id}/images/add',
            data=data,
            content_type='multipart/form-data',
        )

        resp_data = json.loads(resp.data)
        assert resp_data['success'] is True
        assert len(Goods.query.get(goods.goods_id).images) == old_count + 1

    def test_delete_image_decrements_count(self, client):
        """删除图片 → 数量 -1。"""
        user = create_user()
        goods = create_goods(user)
        img = create_goods_image(goods, is_main=1)
        login_user(client, user)

        resp = client.post(
            f'/{goods.goods_id}/images/delete',
            data=json.dumps({'image_id': img.image_id}),
            content_type='application/json',
        )

        assert json.loads(resp.data)['success'] is True
        assert GoodsImage.query.get(img.image_id) is None

    def test_set_main_image(self, client):
        """设主图 → is_main 正确切换。"""
        user = create_user()
        goods = create_goods(user)
        img1 = create_goods_image(goods, is_main=1, sort_order=0)
        img2 = create_goods_image(goods, is_main=0, sort_order=1)
        login_user(client, user)

        client.post(
            f'/{goods.goods_id}/images/set_main',
            data=json.dumps({'image_id': img2.image_id}),
            content_type='application/json',
        )

        assert GoodsImage.query.get(img1.image_id).is_main == 0
        assert GoodsImage.query.get(img2.image_id).is_main == 1

    def test_delete_main_promotes_next(self, client):
        """删除主图 → 下一张自动提升为主图。"""
        user = create_user()
        goods = create_goods(user)
        img1 = create_goods_image(goods, is_main=1, sort_order=0)
        img2 = create_goods_image(goods, is_main=0, sort_order=1)
        login_user(client, user)

        client.post(
            f'/{goods.goods_id}/images/delete',
            data=json.dumps({'image_id': img1.image_id}),
            content_type='application/json',
        )

        assert GoodsImage.query.get(img2.image_id).is_main == 1

    def test_reorder_images(self, client):
        """调整排序 → sort_order 更新。"""
        user = create_user()
        goods = create_goods(user)
        img1 = create_goods_image(goods, sort_order=0)
        img2 = create_goods_image(goods, sort_order=1)
        img3 = create_goods_image(goods, sort_order=2)
        login_user(client, user)

        new_order = [img3.image_id, img1.image_id, img2.image_id]
        resp = client.post(
            f'/{goods.goods_id}/images/reorder',
            data=json.dumps({'image_ids': new_order}),
            content_type='application/json',
        )

        assert json.loads(resp.data)['success'] is True
        assert GoodsImage.query.get(img3.image_id).sort_order == 0
        assert GoodsImage.query.get(img1.image_id).sort_order == 1
        assert GoodsImage.query.get(img2.image_id).sort_order == 2

    def test_reorder_incomplete_list_rejected(self, client):
        """传不完整 ID 列表 → 拒绝。"""
        user = create_user()
        goods = create_goods(user)
        img1 = create_goods_image(goods, sort_order=0)
        img2 = create_goods_image(goods, sort_order=1)
        login_user(client, user)

        resp = client.post(
            f'/{goods.goods_id}/images/reorder',
            data=json.dumps({'image_ids': [img1.image_id]}),  # 少了 img2
            content_type='application/json',
        )

        assert json.loads(resp.data)['success'] is False
