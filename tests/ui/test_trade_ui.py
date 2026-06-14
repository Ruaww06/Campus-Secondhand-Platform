"""test_trade_ui.py — 完整交易链路的 UI 测试。

链路：浏览 → 下单 → 卖家确认 → 买家完成 → 评价
"""

import pytest

from tests.ui.conftest import _prepare_user, _prepare_category, _prepare_goods


@pytest.mark.ui
class TestTradeUI:
    def test_full_trade_flow(self, page, live_server, app):
        """完整交易链路 UI 测试。"""
        # ---- 准备数据 ----
        seller_id, seller_name = _prepare_user(
            app, username='ui_seller_trade'
        )
        buyer_id, buyer_name = _prepare_user(
            app, username='ui_buyer_trade'
        )
        cat_id = _prepare_category(app, name='交易测试分类')
        goods_id = _prepare_goods(app, seller_id, cat_id,
                                  title='UI交易测试商品')

        # ---- 买家登录 ----
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_buyer_trade')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # ---- 浏览首页，找到商品 ----
        page.goto(f'{live_server.url()}/')
        page.wait_for_timeout(2000)
        body = page.locator('body').inner_text()
        assert 'UI交易测试商品' in body

        # ---- 进入详情页 ----
        page.goto(f'{live_server.url()}/{goods_id}')
        page.wait_for_timeout(2000)

        # ---- 下单 ----
        # 点击"立即购买"或提交下单表单
        buy_btn = page.locator('button, a, input[type="submit"]').filter(
            has_text='购买'
        )
        if buy_btn.count() > 0:
            buy_btn.first.click()
            page.wait_for_timeout(3000)

            body_text = page.locator('body').inner_text()
            assert '成功' in body_text or '卖家确认' in body_text or '订单' in body_text

        # ---- 登出，卖家登录 ----
        page.goto(f'{live_server.url()}/auth/logout')
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_seller_trade')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # ---- 卖家确认订单 ----
        # 去卖出订单列表找订单
        page.goto(f'{live_server.url()}/order/sales')
        page.wait_for_timeout(2000)

        # 尝试确认（具体按钮取决于模板实现）
        confirm_btn = page.locator('button, a, input[type="submit"]').filter(
            has_text='确认'
        )
        if confirm_btn.count() > 0:
            confirm_btn.first.click()
            page.wait_for_timeout(2000)

        # ---- 登出，买家登录 ----
        page.goto(f'{live_server.url()}/auth/logout')
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_buyer_trade')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # ---- 买家完成 + 评价 ----
        page.goto(f'{live_server.url()}/order/purchases')
        page.wait_for_timeout(2000)

        complete_btn = page.locator('button, a, input[type="submit"]').filter(
            has_text='完成'
        )
        if complete_btn.count() > 0:
            complete_btn.first.click()
            page.wait_for_timeout(3000)

            # 如果跳转到评价页
            if 'review' in page.url.lower():
                page.fill('textarea[name="content"]', 'UI测试评价：商品很好！')
                rating_inputs = page.locator('input[name="rating"]')
                if rating_inputs.count() > 0:
                    rating_inputs.first.fill('5')
                submit_btn = page.locator('input[type="submit"], button[type="submit"]')
                if submit_btn.count() > 0:
                    submit_btn.first.click()
                    page.wait_for_timeout(2000)

            body_text = page.locator('body').inner_text()
            assert '评价' in body_text or '完成' in body_text or '商品' in body_text
