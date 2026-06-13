from flask import request, redirect, url_for, flash, render_template, session
from app import db
from app.admin import admin_bp
from app.models import User, Goods, Category, OrderInfo, AdminLog, Review
from app.decorators import admin_required


def _log_action(action, target_type=None, target_id=None, detail=None):
    """记录管理员操作日志。"""
    log = AdminLog(
        admin_id=session['user_id'],
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail
    )
    db.session.add(log)
    db.session.commit()


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """管理后台仪表盘。"""
    stats = {
        'user_count': User.query.count(),
        'goods_count': Goods.query.count(),
        'order_count': OrderInfo.query.count(),
        'review_count': Review.query.count(),
        'pending_orders': OrderInfo.query.filter_by(status='pending').count(),
        'today_orders': OrderInfo.query.filter(
            db.func.date(OrderInfo.created_at) == db.func.current_date()
        ).count(),
    }
    recent_orders = OrderInfo.query.order_by(OrderInfo.created_at.desc()).limit(5).all()
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, recent_logs=recent_logs)


@admin_bp.route('/users')
@admin_required
def users():
    """用户管理列表。"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin/users.html', pagination=pagination)


@admin_bp.route('/user/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(user_id):
    """封禁用户。"""
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('不能封禁管理员账号', 'error')
        return redirect(url_for('admin.users'))
    user.status = 'banned'
    db.session.commit()
    _log_action('ban_user', 'user', user_id, f'封禁用户 {user.username}')
    flash(f'用户 {user.username} 已封禁', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(user_id):
    """解封用户。"""
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    db.session.commit()
    _log_action('unban_user', 'user', user_id, f'解封用户 {user.username}')
    flash(f'用户 {user.username} 已解封', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/goods')
@admin_required
def admin_goods():
    """商品管理列表。"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = Goods.query.order_by(Goods.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin/goods.html', pagination=pagination)


@admin_bp.route('/goods/<int:goods_id>/delete', methods=['POST'])
@admin_required
def delete_goods(goods_id):
    """删除商品及其物理图片。"""
    from app.utils import delete_upload_file
    goods = Goods.query.get_or_404(goods_id)
    for img in goods.images:
        delete_upload_file(img.image_url)
    db.session.delete(goods)
    db.session.commit()
    _log_action('delete_goods', 'goods', goods_id, f'删除商品 {goods.title}')
    flash('商品已删除', 'success')
    return redirect(url_for('admin.admin_goods'))


@admin_bp.route('/goods/<int:goods_id>/off_shelf', methods=['POST'])
@admin_required
def off_shelf_goods(goods_id):
    """下架商品。"""
    goods = Goods.query.get_or_404(goods_id)
    goods.status = 'off_shelf'
    db.session.commit()
    _log_action('off_shelf_goods', 'goods', goods_id, f'下架商品 {goods.title}')
    flash('商品已下架', 'success')
    return redirect(url_for('admin.admin_goods'))


@admin_bp.route('/categories')
@admin_required
def categories():
    """分类管理列表。"""
    cats = Category.query.order_by(Category.sort_order.asc()).all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/category/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    """创建分类。"""
    if request.method == 'POST':
        name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip() or None
        sort_order = request.form.get('sort_order', 0, type=int)
        if not name:
            flash('分类名称不能为空', 'error')
            return redirect(url_for('admin.create_category'))
        if Category.query.filter_by(category_name=name).first():
            flash('分类名称已存在', 'error')
            return redirect(url_for('admin.create_category'))
        cat = Category(category_name=name, description=description, sort_order=sort_order)
        db.session.add(cat)
        db.session.commit()
        _log_action('create_category', 'category', cat.category_id, f'创建分类 {name}')
        flash('分类创建成功', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)


@admin_bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """编辑分类。"""
    cat = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip() or None
        sort_order = request.form.get('sort_order', 0, type=int)
        if not name:
            flash('分类名称不能为空', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        existing = Category.query.filter(Category.category_name == name, Category.category_id != category_id).first()
        if existing:
            flash('分类名称已存在', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        cat.category_name = name
        cat.description = description
        cat.sort_order = sort_order
        db.session.commit()
        _log_action('edit_category', 'category', category_id, f'编辑分类 {name}')
        flash('分类更新成功', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=cat)


@admin_bp.route('/category/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    """删除分类。"""
    cat = Category.query.get_or_404(category_id)
    if Goods.query.filter_by(category_id=category_id).first():
        flash('该分类下存在商品，无法删除', 'error')
        return redirect(url_for('admin.categories'))
    db.session.delete(cat)
    db.session.commit()
    _log_action('delete_category', 'category', category_id, f'删除分类 {cat.category_name}')
    flash('分类已删除', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/orders')
@admin_required
def admin_orders():
    """订单管理（只读）。"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = OrderInfo.query.order_by(OrderInfo.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin/orders.html', pagination=pagination)


@admin_bp.route('/logs')
@admin_required
def admin_logs():
    """操作日志，支持按操作类型和日期范围筛选。"""
    page = request.args.get('page', 1, type=int)
    per_page = 30
    action_filter = request.args.get('action', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = AdminLog.query
    if action_filter:
        query = query.filter(AdminLog.action == action_filter)
    if date_from:
        query = query.filter(AdminLog.created_at >= date_from)
    if date_to:
        query = query.filter(AdminLog.created_at <= date_to + ' 23:59:59')

    pagination = query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    action_types = [row[0] for row in db.session.query(AdminLog.action).distinct().all()]

    return render_template('admin/logs.html', pagination=pagination,
                           action_filter=action_filter, date_from=date_from,
                           date_to=date_to, action_types=action_types)
