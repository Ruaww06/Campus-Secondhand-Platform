"""test_permissions.py — 越权、封禁踢出、未登录跳转。"""

import pytest

from tests.conftest import create_user, login_user


class TestBannedUserRedirect:
    def test_banned_user_redirected_login_required(self, client):
        """被封禁用户访问 @login_required 路由 → 302 到登录页。"""
        banned = create_user(username='banned_lr', status='banned')

        with client.session_transaction() as sess:
            sess['user_id'] = banned.user_id
            sess['role'] = 'user'

        resp = client.get('/publish', follow_redirects=False)

        assert resp.status_code == 302
        assert '/auth/login' in (resp.headers.get('Location') or '')

    def test_banned_user_redirected_admin_required(self, client):
        """被封禁用户访问 @admin_required 路由 → 302 到登录页。"""
        banned = create_user(username='banned_ar', status='banned')

        with client.session_transaction() as sess:
            sess['user_id'] = banned.user_id
            sess['role'] = 'admin'

        resp = client.get('/admin/dashboard', follow_redirects=False)

        assert resp.status_code == 302
        assert '/auth/login' in (resp.headers.get('Location') or '')

    def test_unauthenticated_redirect_to_login(self, client):
        """未登录访问受保护路由 → 302 到 /auth/login。"""
        resp = client.get('/publish', follow_redirects=False)
        assert resp.status_code == 302
        assert '/auth/login' in (resp.headers.get('Location') or '')

    def test_normal_user_access_admin_returns_403(self, client):
        """普通用户访问 admin 路由 → 403。"""
        user = create_user()
        login_user(client, user)

        resp = client.get('/admin/dashboard', follow_redirects=False)
        assert resp.status_code == 403
