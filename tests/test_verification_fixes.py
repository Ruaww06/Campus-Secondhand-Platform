"""针对 SPEC 验证过程中修复点的回归测试 — 适配 pytest + 事务回滚。"""

import pytest

from tests.conftest import create_user, login_user


class TestBannedUserRedirect:
    def test_banned_user_is_redirected_by_login_required(self, client):
        """被禁用户访问受保护路由时应被重定向到登录页。"""
        banned = create_user(username='banned_lr_fix', status='banned')

        with client.session_transaction() as sess:
            sess['user_id'] = banned.user_id
            sess['role'] = banned.role

        resp = client.get('/publish', follow_redirects=False)
        assert resp.status_code == 302
        assert '/auth/login' in (resp.headers.get('Location') or '')

    def test_banned_user_is_redirected_by_admin_required(self, client):
        """被禁用户访问 admin 路由时应被重定向到登录页。"""
        banned = create_user(username='banned_ar_fix', status='banned')

        with client.session_transaction() as sess:
            sess['user_id'] = banned.user_id
            sess['role'] = 'admin'

        resp = client.get('/admin/dashboard', follow_redirects=False)
        assert resp.status_code == 302
        assert '/auth/login' in (resp.headers.get('Location') or '')

    def test_publish_without_image_fails(self, client):
        """发布商品时未上传图片应返回发布页并给出提示。"""
        user = create_user()
        login_user(client, user)

        resp = client.post(
            '/publish',
            data={
                'title': '测试商品_无图回归',
                'price': '9.99',
                'category_id': '1',
                'region': '北区',
                'condition_level': 'new',
                'description': '',
                'original_price': '',
                'contact_phone': '',
                'contact_wechat': '',
            },
            content_type='multipart/form-data',
            follow_redirects=False
        )
        assert resp.status_code == 200
        from app.models import Goods
        goods = Goods.query.filter_by(title='测试商品_无图回归').first()
        assert goods is None
