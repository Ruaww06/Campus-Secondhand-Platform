# 校园二手交易平台

数据库课程期末大作业，基于 Flask + MySQL 的校园二手交易 Web 应用。

## 前置准备

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建数据库

登录 MySQL 执行建表脚本：

```bash
mysql -u root -p < schema.sql
```

这会创建 `campus_secondhand` 数据库和全部 8 张表。

### 4. （可选）灌入种子数据

```bash
mysql -u root -p < init_data.sql
```

包含默认分类（教材书籍、电子产品、生活用品等）和示例商品数据，方便快速体验。

## 启动应用

```bash
python run.py
```

浏览器打开 `http://127.0.0.1:8000`。

## 默认账号

| 角色 | 用户名 | 密码 |
|:---|:---|:---|
| 管理员 | `admin` | `admin123` |

（仅当执行了 `init_data.sql` 时生效；否则自行注册）

## 项目结构

```
├── app/
│   ├── __init__.py          # Flask 工厂函数
│   ├── config.py            # 配置
│   ├── decorators.py        # @login_required / @admin_required
│   ├── utils.py             # 文件上传工具
│   ├── models/              # 8 张表的 ORM 模型
│   ├── auth/                # 注册/登录/资料编辑/改密码
│   ├── goods/               # 发布/编辑/上下架/图片管理/搜索
│   ├── order/               # 下单/确认/完成/取消
│   ├── favorite/            # 收藏
│   ├── review/              # 评价
│   ├── admin/               # 管理后台
│   ├── templates/           # Jinja2 模板
│   └── static/              # CSS/JS/上传文件
├── tests/                   # 测试（见下方说明）
├── schema.sql               # 建表脚本
├── init_data.sql            # 种子数据
├── requirements.txt         # Python 依赖
└── run.py                   # 入口
```

## 运行测试

```bash
# 创建测试库
mysql -u root -e "CREATE DATABASE IF NOT EXISTS campus_secondhand_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 跑测试
pytest tests/api/ -v     # API 层 79 条
pytest tests/ui/ -v      # UI 层 10 条（需 Playwright）
```
