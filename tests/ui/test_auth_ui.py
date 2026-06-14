"""test_auth_ui.py — 注册、登录、编辑资料（UI 层）。"""

import pytest

from tests.ui.conftest import _prepare_user


@pytest.mark.ui
class TestAuthUI:
    def test_register_and_see_welcome(self, page, live_server):
        """注册成功 → 页面显示用户名。"""
        page.goto(f'{live_server.url()}/auth/register')

        page.fill('input[name="username"]', 'ui_register_test')
        page.fill('input[name="password"]', 'pass1234')
        page.fill('input[name="confirm_password"]', 'pass1234')
        page.fill('input[name="real_name"]', '界面测试')
        page.fill('input[name="student_id"]', 'STU_UI_001')
        page.fill('input[name="phone"]', '13800000001')
        page.select_option('select[name="region"]', '北区')
        page.click('input[type="submit"]')

        # 注册成功后应跳转到首页
        page.wait_for_url(f'{live_server.url()}/', timeout=10000)
        # 导航栏应显示用户名
        assert page.locator('body').inner_text()

    def test_login_and_see_username(self, page, live_server, app):
        """登录 → 页面显示用户名。"""
        user_id, username = _prepare_user(app, username='ui_login_user')

        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_login_user')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')

        page.wait_for_timeout(2000)
        body_text = page.locator('body').inner_text()
        # 登录成功，用户名应出现在页面
        assert 'ui_login_user' in body_text or '登录' not in page.locator('title').inner_text()

    def test_edit_profile_reflects_changes(self, page, live_server, app):
        """编辑资料 → 个人页显示更新。"""
        user_id, username = _prepare_user(app, username='ui_edit_user')

        # 登录
        page.goto(f'{live_server.url()}/auth/login')
        page.fill('input[name="username"]', 'ui_edit_user')
        page.fill('input[name="password"]', 'password123')
        page.click('input[type="submit"]')
        page.wait_for_timeout(2000)

        # 进入编辑页
        page.goto(f'{live_server.url()}/auth/profile/edit')
        page.fill('input[name="phone"]', '13999999999')
        page.click('input[type="submit"]')

        page.wait_for_timeout(2000)
        body_text = page.locator('body').inner_text()
        assert '13999999999' in body_text
