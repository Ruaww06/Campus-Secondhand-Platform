USE campus_secondhand;

-- 商品分类
INSERT INTO `category` (`category_name`, `description`, `sort_order`) VALUES
('教材书籍', '各类教材、参考书、考试资料', 1),
('电子产品', '手机、电脑、平板、配件等', 2),
('生活用品', '日用品、小家电、床上用品等', 3),
('服装鞋帽', '衣服、鞋子、包包、配饰', 4),
('运动户外', '运动器材、户外装备、健身用品', 5),
('其他', '不属于以上分类的物品', 6);

-- 测试用户（密码均为 werkzeug scrypt 加密后的 '123456'）
INSERT INTO `user` (`username`, `password`, `real_name`, `student_id`, `phone`, `email`, `wechat`, `region`, `role`, `status`) VALUES
('admin', 'scrypt:32768:8:1$V0uviXt82I2sEn2f$ed7e932277c286f8042b4f02b7eccaf9af75b8c10e9809b1260b1b5443e5c1c1d720ebe4b28ea1a4a43d64c25781a21238d917099d0a92a4efec1cdb95d696a7', '管理员', '2024000001', '13800000001', 'admin@campus.edu', 'admin_wx', '北区', 'admin', 'active'),
('zhangsan', 'scrypt:32768:8:1$V4e22BEUoBW1JQXk$2dd5b3949e0a18aa39cb652cce8496d3a6a75ff00a348e673eda9a388c7790c04be0b6cd16ecdbfa866e64df1b30304b059a3a890d87b0042762363a7d1ec80c', '张三', '2022010001', '13800138000', 'zhangsan@campus.edu', 'zs_wx', '北区', 'user', 'active'),
('lisi', 'scrypt:32768:8:1$MmJy6sFcAQyg9Oud$6e4a7c1adc723ddafd8623f33b2641eee3b971b8e62b76f82468a778c9259f34e59d50fb15845ea5225bb3d98794809b8f5ebdd6e0d2baa593db3bf72f3ef28d', '李四', '2022010002', '13800138001', 'lisi@campus.edu', 'ls_wx', '南区', 'user', 'active'),
('wangwu', 'scrypt:32768:8:1$jFZjTtfm8qTF5NZD$62a12f1d96038ae4ab8d3689f460c0b100e078ba397a6adc560e77e63b5c084f5ba15624353de9ea32371e1d88d8ea9ec0613c45a1b0a4535e00d2410bbeaa60', '王五', '2022010003', '13800138002', 'wangwu@campus.edu', 'ww_wx', '北区', 'user', 'active');

-- 测试商品
INSERT INTO `goods` (`seller_id`, `category_id`, `title`, `description`, `price`, `original_price`, `region`, `condition_level`, `status`, `view_count`, `contact_phone`, `contact_wechat`) VALUES
(2, 1, '高等数学同济第七版', '九成新，少量笔记，适合大一新生', 25.00, 59.00, '北区', 'like_new', 'on_sale', 15, '13800138000', 'zs_wx'),
(2, 2, 'iPad Air 4 64G 深空灰', '电池健康95%，带原装充电器，无磕碰', 2800.00, 4799.00, '北区', 'used', 'on_sale', 42, '13800138000', 'zs_wx'),
(3, 3, '宜家台灯', '使用半年，功能完好，暖光', 35.00, 99.00, '南区', 'used', 'on_sale', 8, '13800138001', 'ls_wx'),
(3, 4, '耐克运动鞋 42码', '穿过两次，几乎全新，原盒在', 200.00, 599.00, '南区', 'like_new', 'on_sale', 23, '13800138001', 'ls_wx'),
(4, 2, '罗技机械键盘 K845', '红轴，使用一年，按键全部正常', 150.00, 299.00, '北区', 'used', 'on_sale', 31, '13800138002', 'ww_wx'),
(4, 5, '瑜伽垫', '加厚防滑，几乎没用过', 30.00, 89.00, '北区', 'like_new', 'on_sale', 12, '13800138002', 'ww_wx');

-- 测试商品图片（使用 default-goods.svg 作为占位）
INSERT INTO `goods_image` (`goods_id`, `image_url`, `is_main`, `sort_order`) VALUES
(1, '/static/img/default-goods.svg', 1, 0),
(1, '/static/img/default-goods.svg', 0, 1),
(2, '/static/img/default-goods.svg', 1, 0),
(2, '/static/img/default-goods.svg', 0, 1),
(2, '/static/img/default-goods.svg', 0, 2),
(3, '/static/img/default-goods.svg', 1, 0),
(4, '/static/img/default-goods.svg', 1, 0),
(5, '/static/img/default-goods.svg', 1, 0),
(5, '/static/img/default-goods.svg', 0, 1);

-- 测试订单
INSERT INTO `order_info` (`order_no`, `buyer_id`, `seller_id`, `goods_id`, `status`, `remark`) VALUES
('ORD202505270001', 3, 2, 1, 'completed', '请尽快发货'),
('ORD202505270002', 4, 2, 2, 'confirmed', '面交'),
('ORD202505270003', 2, 3, 3, 'pending', NULL);

-- 测试评价
INSERT INTO `review` (`order_id`, `reviewer_id`, `seller_id`, `rating`, `content`) VALUES
(1, 3, 2, 5, '书保存得很好，笔记也很清晰，感谢学长！');
