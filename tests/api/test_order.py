"""test_order.py — 下单、确认、完成、取消、订单列表、权限。

覆盖 ER 关系: R2 购买, R3 售出, R10 订单-商品
"""

import pytest

from tests.conftest import (
    create_user, create_category, create_goods, create_order, login_user,
    create_trade_chain
)
from app.models import Goods, OrderInfo


class TestCreateOrder:
    def test_create_order_sets_goods_sold(self, client):
        """买家下单 → goods 变 sold，订单落库。"""
        seller = create_user()
        buyer = create_user()
        goods = create_goods(seller, category=create_category())
        login_user(client, buyer)

        resp = client.post('/order/create', data={
            'goods_id': str(goods.goods_id),
        }, follow_redirects=False)

        assert resp.status_code == 302
        assert Goods.query.get(goods.goods_id).status == 'sold'
        order = OrderInfo.query.filter_by(goods_id=goods.goods_id).first()
        assert order is not None
        assert order.buyer_id == buyer.user_id
        assert order.seller_id == seller.user_id
        assert order.status == 'pending'

    def test_cannot_buy_own_goods(self, client):
        """买自己的商品 → 拒绝。"""
        user = create_user()
        goods = create_goods(user, category=create_category())
        login_user(client, user)

        resp = client.post('/order/create', data={
            'goods_id': str(goods.goods_id),
        }, follow_redirects=True)

        assert '不能购买自己' in resp.get_data(as_text=True)
        assert Goods.query.get(goods.goods_id).status == 'on_sale'

    def test_cannot_buy_off_shelf_goods(self, client):
        """买已下架商品 → 拒绝。"""
        seller = create_user()
        buyer = create_user()
        goods = create_goods(seller, category=create_category(),
                             status='off_shelf')
        login_user(client, buyer)

        resp = client.post('/order/create', data={
            'goods_id': str(goods.goods_id),
        }, follow_redirects=True)

        assert '不可购买' in resp.get_data(as_text=True)


class TestOrderLifecycle:
    def test_seller_confirm_order(self, client):
        """卖家确认 → pending → confirmed。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')
        login_user(client, seller)

        resp = client.post(f'/order/{order.order_id}/confirm',
                           follow_redirects=True)

        assert resp.status_code == 200
        assert OrderInfo.query.get(order.order_id).status == 'confirmed'

    def test_non_seller_cannot_confirm(self, client):
        """非卖家确认 → 403。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')
        other = create_user()
        login_user(client, other)

        resp = client.post(f'/order/{order.order_id}/confirm',
                           follow_redirects=False)

        assert resp.status_code == 403

    def test_buyer_complete_order(self, client):
        """买家完成 → confirmed → completed。"""
        buyer, seller, goods, order = create_trade_chain(status='confirmed')
        login_user(client, buyer)

        resp = client.post(f'/order/{order.order_id}/complete',
                           follow_redirects=False)

        assert resp.status_code == 302
        assert OrderInfo.query.get(order.order_id).status == 'completed'

    def test_non_buyer_cannot_complete(self, client):
        """非买家完成 → 403。"""
        buyer, seller, goods, order = create_trade_chain(status='confirmed')
        other = create_user()
        login_user(client, other)

        resp = client.post(f'/order/{order.order_id}/complete',
                           follow_redirects=False)

        assert resp.status_code == 403

    def test_buyer_cancel_pending_order(self, client):
        """买家取消 → order cancelled, goods 恢复 on_sale。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')
        login_user(client, buyer)

        client.post(f'/order/{order.order_id}/cancel', follow_redirects=True)

        assert OrderInfo.query.get(order.order_id).status == 'cancelled'
        assert Goods.query.get(goods.goods_id).status == 'on_sale'

    def test_cannot_cancel_completed_order(self, client):
        """已完成订单不可取消。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        login_user(client, buyer)

        resp = client.post(f'/order/{order.order_id}/cancel',
                           follow_redirects=True)

        assert '不可取消' in resp.get_data(as_text=True)
        assert OrderInfo.query.get(order.order_id).status == 'completed'

    def test_non_buyer_cannot_cancel(self, client):
        """非买家取消 → 403。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')
        other = create_user()
        login_user(client, other)

        resp = client.post(f'/order/{order.order_id}/cancel',
                           follow_redirects=False)

        assert resp.status_code == 403


class TestOrderViews:
    def test_view_purchases(self, client):
        """查看购买列表。"""
        buyer = create_user()
        seller = create_user()
        goods = create_goods(seller, category=create_category(), title='已买商品')
        create_order(buyer, goods)
        login_user(client, buyer)

        resp = client.get('/order/purchases')

        assert resp.status_code == 200
        assert '已买商品' in resp.get_data(as_text=True)

    def test_view_sales(self, client):
        """查看售出列表。"""
        buyer = create_user()
        seller = create_user()
        goods = create_goods(seller, category=create_category(), title='已售商品')
        create_order(buyer, goods)
        login_user(client, seller)

        resp = client.get('/order/sales')

        assert resp.status_code == 200
        assert '已售商品' in resp.get_data(as_text=True)

    def test_order_detail_visible_to_buyer_and_seller(self, client):
        """订单详情：买卖方均可查看。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')

        login_user(client, buyer)
        assert client.get(f'/order/{order.order_id}').status_code == 200

        login_user(client, seller)
        assert client.get(f'/order/{order.order_id}').status_code == 200

    def test_order_detail_forbidden_to_third_party(self, client):
        """订单详情：第三方 → 403。"""
        buyer, seller, goods, order = create_trade_chain(status='pending')
        other = create_user()
        login_user(client, other)

        resp = client.get(f'/order/{order.order_id}')

        assert resp.status_code == 403
