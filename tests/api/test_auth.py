"""test_auth.py — 注册、登录、登出、资料编辑、修改密码。"""

import pytest
from app.models import User
from werkzeug.security import check_password_hash

from tests.conftest import create_user, login_user


class TestRegister:
    def test_register_success_auto_login(self, client):
        """注册成功 → 自动登录 → 302 到首页。"""
        resp = client.post('/auth/register', data={
            'username': 'newuser_001',
            'password': 'pass123456',
            'confirm_password': 'pass123456',
            'real_name': '张同学',
            'student_id': 'STU_REG_001',
            'phone': '13800001111',
            'email': 'zhang@example.com',
            'wechat': 'zhang_wx',
            'region': '北区',
        }, follow_redirects=False)

        assert resp.status_code == 302
        assert '/auth/login' not in (resp.headers.get('Location') or '')
        user = User.query.filter_by(username='newuser_001').first()
        assert user is not None
        assert user.status == 'active'
        assert user.role == 'user'

        # 验证 session 已设置
        with client.session_transaction() as sess:
            assert sess.get('user_id') == user.user_id

    def test_register_duplicate_username_fails(self, client):
        """重复用户名注册 → 200 停留在注册页。"""
        create_user(username='dup_user')

        resp = client.post('/auth/register', data={
            'username': 'dup_user',
            'password': 'pass123456',
            'confirm_password': 'pass123456',
            'real_name': '重复',
            'student_id': 'STU_DUP_002',
            'phone': '13800002222',
            'region': '北区',
        }, follow_redirects=True)

        assert '已被注册' in resp.get_data(as_text=True)
        assert User.query.filter_by(username='dup_user').count() == 1

    def test_login_success(self, client):
        """正确凭据登录 → 302 跳转首页，session 已设。"""
        user = create_user(username='login_user', password='correct')

        resp = client.post('/auth/login', data={
            'username': 'login_user',
            'password': 'correct',
        }, follow_redirects=False)

        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess.get('user_id') == user.user_id

    def test_login_wrong_password(self, client):
        """错误密码 → 200 停留，session 无 user_id。"""
        create_user(username='wrong_pw_user', password='correct')

        resp = client.post('/auth/login', data={
            'username': 'wrong_pw_user',
            'password': 'wrong_pw',
        })

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess.get('user_id') is None

    def test_login_banned_user_fails(self, client):
        """被封禁用户登录 → 200，session 无 user_id。"""
        create_user(username='banned_login', status='banned')

        resp = client.post('/auth/login', data={
            'username': 'banned_login',
            'password': 'password123',
        })

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess.get('user_id') is None

    def test_login_next_redirect(self, client):
        """带 ?next= → 登录成功跳转到目标页。"""
        user = create_user(username='next_user', password='pw')

        resp = client.post(
            f'/auth/login?next=/my',
            data={'username': 'next_user', 'password': 'pw'},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert '/my' in (resp.headers.get('Location') or '')

    def test_logout_clears_session(self, client):
        """登出 → session 清空，302 到首页。"""
        user = create_user()
        login_user(client, user)

        resp = client.get('/auth/logout', follow_redirects=False)

        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess.get('user_id') is None


class TestProfileAndPassword:
    def test_edit_profile_updates_fields(self, client):
        """编辑资料 → 字段落库，session username 更新。"""
        user = create_user(username='profile_edit')
        login_user(client, user)

        client.post('/auth/profile/edit', data={
            'username': 'profile_new_name',
            'real_name': '新名字',
            'student_id': user.student_id,
            'phone': '13900000000',
            'email': 'new@example.com',
            'wechat': 'new_wx',
            'region': '南区',
        }, follow_redirects=True)

        updated = User.query.get(user.user_id)
        assert updated.username == 'profile_new_name'
        assert updated.real_name == '新名字'
        assert updated.phone == '13900000000'
        assert updated.email == 'new@example.com'
        assert updated.wechat == 'new_wx'
        assert updated.region == '南区'

        with client.session_transaction() as sess:
            assert sess.get('username') == 'profile_new_name'

    def test_edit_profile_duplicate_username_rejected(self, client):
        """编辑时改用已被占用的用户名 → 拒绝。"""
        other = create_user(username='taken_name')
        user = create_user(username='edit_me')
        login_user(client, user)

        resp = client.post('/auth/profile/edit', data={
            'username': 'taken_name',
            'real_name': user.real_name,
            'student_id': user.student_id,
            'phone': user.phone,
            'region': user.region,
        }, follow_redirects=True)

        assert '已被占用' in resp.get_data(as_text=True)
        assert User.query.get(user.user_id).username == 'edit_me'

    def test_change_password_success(self, client):
        """修改密码 → 旧密码失效，新密码可验证。"""
        user = create_user(username='chpw', password='old_pass')
        login_user(client, user)

        client.post('/auth/change-password', data={
            'old_password': 'old_pass',
            'new_password': 'new_pass_123',
            'confirm_password': 'new_pass_123',
        }, follow_redirects=True)

        updated = User.query.get(user.user_id)
        assert check_password_hash(updated.password, 'new_pass_123')

    def test_change_password_wrong_old_fails(self, client):
        """旧密码错误 → 修改失败，密码不变。"""
        user = create_user(username='chpw_fail', password='old_pass')
        login_user(client, user)
        old_hash = user.password

        client.post('/auth/change-password', data={
            'old_password': 'wrong_old',
            'new_password': 'new_pass_123',
            'confirm_password': 'new_pass_123',
        })

        assert User.query.get(user.user_id).password == old_hash
