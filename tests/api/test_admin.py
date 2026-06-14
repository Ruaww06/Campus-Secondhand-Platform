"""test_admin.py — 仪表盘、封禁/解封、删除商品、下架、分类 CRUD、日志。

覆盖 ER 关系: R8 包含商品, R11 记录操作
"""

import pytest

from tests.conftest import (
    create_user, create_category, create_goods, create_goods_image,
    create_order, create_admin_log, login_user,
)
from tests.conftest import login_admin  # noqa: F811 - reimport for clarity
from app.models import User, Goods, Category, OrderInfo, AdminLog, GoodsImage


def _admin():
    """快捷创建管理员并返回 (admin_user, client 的 session 不便在此设置)。"""
    return create_user(username=f'adm_{__import__("secrets").token_hex(4)}',
                       role='admin')


class TestDashboard:
    def test_dashboard_shows_stats(self, client):
        """仪表盘显示统计数字。"""
        admin = _admin()
        login_admin(client, admin)

        resp = client.get('/admin/dashboard')

        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        # 页面应该渲染成功，包含关键区域
        assert '统计' in text or '仪表' in text or 'dashboard' in text.lower()


class TestUserManagement:
    def test_ban_user(self, client):
        """封禁用户 → status=banned, 产生日志。"""
        admin = _admin()
        user = create_user()
        login_admin(client, admin)

        client.post(f'/admin/user/{user.user_id}/ban', follow_redirects=True)

        assert User.query.get(user.user_id).status == 'banned'
        log = AdminLog.query.filter_by(
            action='ban_user', target_type='user', target_id=user.user_id
        ).first()
        assert log is not None
        assert log.admin_id == admin.user_id

    def test_cannot_ban_admin(self, client):
        """封禁管理员 → 拒绝。"""
        admin = _admin()
        login_admin(client, admin)

        resp = client.post(f'/admin/user/{admin.user_id}/ban',
                           follow_redirects=True)

        assert '不能封禁管理员' in resp.get_data(as_text=True)
        assert User.query.get(admin.user_id).status == 'active'

    def test_unban_user(self, client):
        """解封用户 → status=active, 产生日志。"""
        admin = _admin()
        user = create_user(status='banned')
        login_admin(client, admin)

        client.post(f'/admin/user/{user.user_id}/unban', follow_redirects=True)

        assert User.query.get(user.user_id).status == 'active'
        log = AdminLog.query.filter_by(
            action='unban_user', target_type='user', target_id=user.user_id
        ).first()
        assert log is not None


class TestGoodsManagement:
    def test_delete_goods_with_images(self, client):
        """管理员删除商品 → goods + images 物理删除，产生日志。"""
        admin = _admin()
        seller = create_user()
        goods = create_goods(seller)
        img = create_goods_image(goods)
        login_admin(client, admin)

        client.post(f'/admin/goods/{goods.goods_id}/delete',
                    follow_redirects=True)

        assert Goods.query.get(goods.goods_id) is None
        assert GoodsImage.query.get(img.image_id) is None
        log = AdminLog.query.filter_by(
            action='delete_goods', target_type='goods', target_id=goods.goods_id
        ).first()
        assert log is not None

    def test_force_off_shelf(self, client):
        """管理员强制下架商品 → status=off_shelf, 产生日志。"""
        admin = _admin()
        seller = create_user()
        goods = create_goods(seller)
        login_admin(client, admin)

        client.post(f'/admin/goods/{goods.goods_id}/off_shelf',
                    follow_redirects=True)

        assert Goods.query.get(goods.goods_id).status == 'off_shelf'
        log = AdminLog.query.filter_by(
            action='off_shelf_goods', target_type='goods',
            target_id=goods.goods_id
        ).first()
        assert log is not None


class TestCategoryManagement:
    def test_create_category(self, client):
        """创建分类 → 落库 + 日志。"""
        admin = _admin()
        login_admin(client, admin)

        client.post('/admin/category/create', data={
            'category_name': '测试分类',
            'description': '描述',
            'sort_order': '1',
        }, follow_redirects=True)

        cat = Category.query.filter_by(category_name='测试分类').first()
        assert cat is not None
        log = AdminLog.query.filter_by(
            action='create_category', target_type='category',
            target_id=cat.category_id
        ).first()
        assert log is not None

    def test_create_duplicate_category_name_rejected(self, client):
        """分类名重复 → 拒绝。"""
        admin = _admin()
        create_category(name='唯一分类')
        login_admin(client, admin)

        resp = client.post('/admin/category/create', data={
            'category_name': '唯一分类',
        }, follow_redirects=True)

        assert '已存在' in resp.get_data(as_text=True)
        assert Category.query.filter_by(category_name='唯一分类').count() == 1

    def test_edit_category(self, client):
        """编辑分类 → 更新 + 日志。"""
        admin = _admin()
        cat = create_category(name='旧名')
        login_admin(client, admin)

        client.post(f'/admin/category/{cat.category_id}/edit', data={
            'category_name': '新分类名',
            'description': '新描述',
            'sort_order': '5',
        }, follow_redirects=True)

        c = Category.query.get(cat.category_id)
        assert c.category_name == '新分类名'
        assert c.sort_order == 5
        log = AdminLog.query.filter_by(
            action='edit_category', target_type='category',
            target_id=cat.category_id
        ).first()
        assert log is not None

    def test_delete_empty_category_success(self, client):
        """删除无商品引用的分类 → 成功 + 日志。"""
        admin = _admin()
        cat = create_category()
        login_admin(client, admin)

        client.post(f'/admin/category/{cat.category_id}/delete',
                    follow_redirects=True)

        assert Category.query.get(cat.category_id) is None
        log = AdminLog.query.filter_by(
            action='delete_category', target_type='category',
            target_id=cat.category_id
        ).first()
        assert log is not None

    def test_delete_category_with_goods_rejected(self, client):
        """删除有商品引用的分类 → 拒绝（ON DELETE RESTRICT）。"""
        admin = _admin()
        seller = create_user()
        cat = create_category()
        create_goods(seller, category=cat)
        login_admin(client, admin)

        resp = client.post(f'/admin/category/{cat.category_id}/delete',
                           follow_redirects=True)

        assert '无法删除' in resp.get_data(as_text=True)
        assert Category.query.get(cat.category_id) is not None


class TestListView:
    def test_view_users_list(self, client):
        """查看用户列表。"""
        admin = _admin()
        create_user()
        login_admin(client, admin)

        resp = client.get('/admin/users')

        assert resp.status_code == 200

    def test_view_goods_list(self, client):
        """查看商品列表。"""
        admin = _admin()
        login_admin(client, admin)

        resp = client.get('/admin/goods')

        assert resp.status_code == 200

    def test_view_orders_list(self, client):
        """查看订单列表。"""
        admin = _admin()
        login_admin(client, admin)

        resp = client.get('/admin/orders')

        assert resp.status_code == 200

    def test_view_logs_with_filters(self, client):
        """查看日志列表，支持按 action 和日期筛选。"""
        admin = _admin()
        login_admin(client, admin)
        create_admin_log(admin, action='ban_user', target_type='user',
                         target_id=1, detail='封禁测试')

        resp = client.get('/admin/logs?action=ban_user')

        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert 'ban_user' in text or '封禁' in text
