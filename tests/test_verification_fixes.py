"""针对 SPEC 验证过程中修复点的回归测试。"""
import os
import sys
import unittest

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Goods, GoodsImage


class VerificationFixesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['WTF_CSRF_ENABLED'] = False  # 测试时关闭 CSRF
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        # 创建测试用户
        self.active_user = User(
            username='test_active_user',
            password='hashed',
            real_name='Active',
            student_id='TEST_ACTIVE_001',
            phone='13800000001',
            region='东区',
            role='user',
            status='active'
        )
        self.banned_user = User(
            username='test_banned_user',
            password='hashed',
            real_name='Banned',
            student_id='TEST_BANNED_001',
            phone='13800000002',
            region='东区',
            role='user',
            status='banned'
        )
        db.session.add_all([self.active_user, self.banned_user])
        db.session.commit()

    def tearDown(self):
        # 清理测试数据
        GoodsImage.query.filter(
            GoodsImage.goods_id.in_(
                db.session.query(Goods.goods_id).filter(
                    Goods.seller_id.in_([self.active_user.user_id, self.banned_user.user_id])
                )
            )
        ).delete(synchronize_session=False)
        Goods.query.filter(
            Goods.seller_id.in_([self.active_user.user_id, self.banned_user.user_id])
        ).delete(synchronize_session=False)
        db.session.delete(self.active_user)
        db.session.delete(self.banned_user)
        db.session.commit()

    def test_banned_user_is_redirected_by_login_required(self):
        """被禁用户访问受保护路由时应被重定向到登录页。"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.banned_user.user_id
            sess['role'] = self.banned_user.role

        # /goods/publish 受 @login_required 保护
        resp = self.client.get('/publish', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login', resp.headers.get('Location', ''))

    def test_banned_user_is_redirected_by_admin_required(self):
        """被禁用户访问 admin 路由时应被重定向到登录页。"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.banned_user.user_id
            sess['role'] = 'admin'  # 模拟 session 中仍是 admin（被 ban 后应失效）

        resp = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login', resp.headers.get('Location', ''))

    def test_publish_without_image_fails(self):
        """发布商品时未上传图片应返回发布页并给出提示。"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.active_user.user_id
            sess['role'] = self.active_user.role

        resp = self.client.post(
            '/publish',
            data={
                'title': '测试商品',
                'price': '9.99',
                'category_id': '1',
                'region': '东区',
                'condition_level': 'new',
                'description': '',
                'original_price': '',
                'contact_phone': '',
                'contact_wechat': '',
            },
            content_type='multipart/form-data',
            follow_redirects=False
        )
        # 未上传图片时不应重定向到商品详情，应停留在发布页
        self.assertEqual(resp.status_code, 200)
        # 发布的商品不应被写入数据库
        goods = Goods.query.filter_by(title='测试商品').first()
        self.assertIsNone(goods)


if __name__ == '__main__':
    unittest.main(verbosity=2)
