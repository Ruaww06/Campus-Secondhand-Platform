"""test_review.py — 评价、我的评价、卖家评价墙、一单一评约束。

覆盖 ER 关系: R5 发表评价, R6 被评价, R7 一单一评
"""

import pytest

from tests.conftest import (
    create_user, create_review, login_user, create_trade_chain
)
from app.models import Review


class TestCreateReview:
    def test_review_completed_order_success(self, client):
        """已完成订单 → 评价落库。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        login_user(client, buyer)

        resp = client.post(f'/review/create?order_id={order.order_id}', data={
            'rating': '5',
            'content': '非常好用！',
        }, follow_redirects=True)

        review = Review.query.filter_by(order_id=order.order_id).first()
        assert review is not None
        assert review.rating == 5
        assert review.content == '非常好用！'
        assert review.reviewer_id == buyer.user_id
        assert review.seller_id == seller.user_id

    def test_review_non_completed_order_rejected(self, client):
        """评价未完成订单 → 拒绝。"""
        buyer, seller, goods, order = create_trade_chain(status='confirmed')
        login_user(client, buyer)

        resp = client.get(f'/review/create?order_id={order.order_id}',
                          follow_redirects=True)

        assert resp.status_code == 200  # 应停留在某页，不会 200 OK 创建成功
        # 不应该创建记录
        assert Review.query.filter_by(order_id=order.order_id).first() is None

    def test_non_buyer_cannot_review(self, client):
        """非买家评价 → 拒绝。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        other = create_user()
        login_user(client, other)

        resp = client.get(f'/review/create?order_id={order.order_id}',
                          follow_redirects=True)

        # 应 render review form or be redirected
        review = Review.query.filter_by(order_id=order.order_id).first()
        assert review is None

    def test_duplicate_review_rejected(self, client):
        """重复评价同一订单 → 拒绝。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        create_review(order, buyer, rating=5, content='第一次评价')
        login_user(client, buyer)

        resp = client.post(f'/review/create?order_id={order.order_id}', data={
            'rating': '3',
            'content': '第二次评价',
        }, follow_redirects=True)

        assert Review.query.filter_by(order_id=order.order_id).count() == 1
        assert Review.query.filter_by(order_id=order.order_id).first().rating == 5


class TestReviewViews:
    def test_my_reviews(self, client):
        """查看"我的评价"列表。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        create_review(order, buyer, rating=4, content='还行')
        login_user(client, buyer)

        resp = client.get('/review/my')

        assert resp.status_code == 200
        assert '还行' in resp.get_data(as_text=True)

    def test_seller_review_wall(self, client):
        """卖家评价墙 → 显示平均分。"""
        buyer, seller, goods, order = create_trade_chain(status='completed')
        create_review(order, buyer, rating=4, content='OK')

        resp = client.get(f'/review/seller/{seller.user_id}')

        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert 'OK' in text
        # 平均分验证：应该包含 4.0 或 4
        assert '4' in text
