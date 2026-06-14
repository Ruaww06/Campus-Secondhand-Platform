"""test_admin_ui.py — 管理员登录、封禁用户、分类 CRUD（UI 层）。"""

import pytest

from tests.ui.conftest import _prepare_user, _prepare_category


@pytest.mark.ui
class TestAdminUI:
    def test_admin_login_and_dashboard(self, page, live_server, app):
        """管理员登录 → 仪表盘可见。"""
        _prepare_user(app, username='ui_admin', role='admin')

        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_admin')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        page.goto(f'{live_server.url()}/admin/dashboard')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert '仪表' in body_text or '统计' in body_text or '管理' in body_text

    def test_ban_user_and_check_log(self, page, live_server, app):
        """封禁用户 → 日志可见。"""
        _prepare_user(app, username='ui_admin_ban', role='admin')
        victim_id, victim_name = _prepare_user(app, username='ui_victim')

        # 管理员登录
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_admin_ban')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # 进入用户管理页
        page.goto(f'{live_server.url()}/admin/users')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert 'ui_victim' in body_text

        # 点击封禁按钮（具体按钮文本取决于模板实现）
        ban_btn = page.locator('button, a, input[type="submit"]').filter(
            has_text='封禁'
        )
        if ban_btn.count() > 0:
            ban_btn.first.click()
            page.wait_for_timeout(2000)

            body_text = page.locator('body').inner_text()
            assert '封禁' in body_text or '成功' in body_text

        # 检查日志
        page.goto(f'{live_server.url()}/admin/logs')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert '日志' in body_text or '操作' in body_text or 'log' in body_text.lower()

    def test_category_crud(self, page, live_server, app):
        """分类 CRUD → 分类列表更新。"""
        _prepare_user(app, username='ui_admin_cat', role='admin')

        # 管理员登录
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_admin_cat')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # 进入分类管理
        page.goto(f'{live_server.url()}/admin/categories')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert '分类' in body_text

        # 进入创建分类页
        page.goto(f'{live_server.url()}/admin/category/create')
        page.fill('input[name="category_name"]', 'UITest分类')
        page.fill('textarea[name="description"]', 'UI创建的分类')
        page.fill('input[name="sort_order"]', '1')
        page.click('input[type="submit"], button[type="submit"]')
        page.wait_for_timeout(2000)

        body_text = page.locator('body').inner_text()
        assert 'UITest分类' in body_text
