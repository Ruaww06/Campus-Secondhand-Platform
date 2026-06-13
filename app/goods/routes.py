from flask import render_template, redirect, url_for, flash, request, session, jsonify
from app.goods import goods_bp
from app.goods.forms import GoodsForm, SearchForm
from app import db
from app.models import Goods, GoodsImage, Category, Favorite
from app.decorators import login_required
from app.utils import allowed_file, save_upload_file, delete_upload_file


def _set_category_choices(form):
    """Helper: populate category_id choices (used by GoodsForm and SearchForm)."""
    categories = Category.query.order_by(Category.sort_order).all()
    form.category_id.choices = [(c.category_id, c.category_name) for c in categories]


def _set_search_category_choices(form):
    """Helper: populate category_id choices with an '全部' default."""
    categories = Category.query.order_by(Category.sort_order).all()
    form.category_id.choices = [('', '全部分类')] + [
        (str(c.category_id), c.category_name) for c in categories
    ]


# ---------------------------------------------------------------------------
# A1  首页
# ---------------------------------------------------------------------------
@goods_bp.route('/')
def index():
    """商品列表首页，支持搜索/筛选/排序/分页。"""
    # --- 读取查询参数 ---
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    region = request.args.get('region', '')
    condition_level = request.args.get('condition_level', '')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)

    # --- 构建查询 ---
    query = Goods.query.filter(Goods.status == 'on_sale')

    if q:
        query = query.filter(Goods.title.contains(q) | Goods.description.contains(q))
    if category_id:
        query = query.filter(Goods.category_id == category_id)
    if min_price is not None:
        query = query.filter(Goods.price >= min_price)
    if max_price is not None:
        query = query.filter(Goods.price <= max_price)
    if region:
        query = query.filter(Goods.region == region)
    if condition_level:
        query = query.filter(Goods.condition_level == condition_level)

    # --- 排序 ---
    sort_map = {
        'price_asc': Goods.price.asc(),
        'price_desc': Goods.price.desc(),
        'popular': Goods.view_count.desc(),
    }
    query = query.order_by(sort_map.get(sort, Goods.created_at.desc()))

    pagination = query.paginate(page=page, per_page=12, error_out=False)

    # --- 搜索表单（回填当前筛选条件） ---
    search_form = SearchForm()
    _set_search_category_choices(search_form)
    search_form.q.data = q
    search_form.category_id.data = str(category_id) if category_id else ''
    search_form.min_price.data = str(request.args.get('min_price', ''))
    search_form.max_price.data = str(request.args.get('max_price', ''))
    search_form.region.data = region
    search_form.condition_level.data = condition_level
    search_form.sort.data = sort

    return render_template('goods/index.html',
                           goods=pagination.items,
                           pagination=pagination,
                           form=search_form)


# ---------------------------------------------------------------------------
# A2  搜索（重定向到首页）
# ---------------------------------------------------------------------------
@goods_bp.route('/search')
def search():
    """接收搜索参数并重定向到首页。"""
    args = {}
    for key in ('q', 'category_id', 'min_price', 'max_price',
                'region', 'condition_level', 'sort', 'page'):
        val = request.args.get(key)
        if val:
            args[key] = val

    if args:
        return redirect(url_for('goods.index', **args))
    return redirect(url_for('goods.index'))


# ---------------------------------------------------------------------------
# A3  发布商品
# ---------------------------------------------------------------------------
@goods_bp.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    """发布新商品。"""
    form = GoodsForm()
    _set_category_choices(form)

    if form.validate_on_submit():
        uploaded_images = [f for f in form.images.data if f and f.filename]
        if not uploaded_images:
            flash('请至少上传一张商品图片', 'error')
            return render_template('goods/publish.html', form=form)

        goods = Goods(
            seller_id=session['user_id'],
            title=form.title.data,
            category_id=form.category_id.data,
            description=form.description.data or None,
            price=form.price.data,
            original_price=form.original_price.data or None,
            region=form.region.data,
            condition_level=form.condition_level.data,
            contact_phone=form.contact_phone.data or None,
            contact_wechat=form.contact_wechat.data or None,
            status='on_sale'
        )
        db.session.add(goods)
        db.session.commit()

        # 保存上传的图片
        is_first = True
        for file in uploaded_images:
            try:
                path = save_upload_file(file, f'goods_{goods.goods_id}')
            except ValueError:
                flash('包含不支持的文件类型，已跳过', 'warning')
                continue
            img = GoodsImage(
                goods_id=goods.goods_id,
                image_url=path,
                is_main=1 if is_first else 0
            )
            db.session.add(img)
            is_first = False
        db.session.commit()

        flash('商品发布成功！', 'success')
        return redirect(url_for('goods.detail', goods_id=goods.goods_id))

    return render_template('goods/publish.html', form=form)


# ---------------------------------------------------------------------------
# A4  商品详情
# ---------------------------------------------------------------------------
@goods_bp.route('/<int:goods_id>')
def detail(goods_id):
    """商品详情页。"""
    goods = Goods.query.get_or_404(goods_id)

    # 增加浏览量
    goods.view_count += 1
    db.session.commit()

    seller = goods.seller

    # 判断当前用户是否已收藏
    is_favorited = False
    if session.get('user_id'):
        is_favorited = Favorite.query.filter_by(
            user_id=session['user_id'],
            goods_id=goods_id
        ).first() is not None

    # 相关商品：同分类、在售、排除当前
    related_goods = Goods.query.filter(
        Goods.category_id == goods.category_id,
        Goods.status == 'on_sale',
        Goods.goods_id != goods_id
    ).order_by(Goods.created_at.desc()).limit(4).all()

    return render_template('goods/detail.html',
                           goods=goods,
                           seller=seller,
                           is_favorited=is_favorited,
                           related_goods=related_goods)


# ---------------------------------------------------------------------------
# A5  我的发布
# ---------------------------------------------------------------------------
@goods_bp.route('/my')
@login_required
def my_goods():
    """当前用户发布的商品列表。"""
    page = request.args.get('page', 1, type=int)
    pagination = Goods.query.filter_by(seller_id=session['user_id'])\
        .order_by(Goods.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)

    return render_template('goods/my_goods.html',
                           goods=pagination.items,
                           pagination=pagination)


# ---------------------------------------------------------------------------
# A6  编辑商品
# ---------------------------------------------------------------------------
@goods_bp.route('/<int:goods_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(goods_id):
    """编辑已发布的商品。"""
    goods = Goods.query.get_or_404(goods_id)

    # 验证所有权：仅卖家本人或管理员可编辑
    if goods.seller_id != session['user_id'] and session.get('role') != 'admin':
        flash('无权编辑该商品', 'error')
        return redirect(url_for('goods.my_goods'))

    form = GoodsForm(obj=goods)
    _set_category_choices(form)

    if form.validate_on_submit():
        goods.title = form.title.data
        goods.category_id = form.category_id.data
        goods.description = form.description.data or None
        goods.price = form.price.data
        goods.original_price = form.original_price.data or None
        goods.region = form.region.data
        goods.condition_level = form.condition_level.data
        goods.contact_phone = form.contact_phone.data or None
        goods.contact_wechat = form.contact_wechat.data or None
        # 图片管理由 A12 单独处理，此处不修改
        db.session.commit()
        flash('商品信息已更新', 'success')
        return redirect(url_for('goods.my_goods'))

    return render_template('goods/edit.html', form=form, goods=goods)


# ---------------------------------------------------------------------------
# A7  下架商品
# ---------------------------------------------------------------------------
@goods_bp.route('/<int:goods_id>/off_shelf', methods=['POST'])
@login_required
def off_shelf(goods_id):
    """将商品下架。"""
    goods = Goods.query.get_or_404(goods_id)

    if goods.seller_id != session['user_id']:
        flash('无权操作该商品', 'error')
        return redirect(url_for('goods.my_goods'))

    goods.status = 'off_shelf'
    db.session.commit()
    flash('商品已下架', 'success')
    return redirect(url_for('goods.my_goods'))


# ---------------------------------------------------------------------------
# A8  重新上架
# ---------------------------------------------------------------------------
@goods_bp.route('/<int:goods_id>/on_sale', methods=['POST'])
@login_required
def on_sale(goods_id):
    """将已下架商品重新上架。"""
    goods = Goods.query.get_or_404(goods_id)

    if goods.seller_id != session['user_id']:
        flash('无权操作该商品', 'error')
        return redirect(url_for('goods.my_goods'))

    goods.status = 'on_sale'
    db.session.commit()
    flash('商品已重新上架', 'success')
    return redirect(url_for('goods.my_goods'))


# ---------------------------------------------------------------------------
# A12  图片管理 API（均返回 JSON）
# ---------------------------------------------------------------------------

@goods_bp.route('/<int:goods_id>/images/delete', methods=['POST'])
@login_required
def delete_image(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    if goods.seller_id != session['user_id']:
        return jsonify(success=False, message='无权操作'), 403

    data = request.get_json() or {}
    image_id = data.get('image_id')
    img = GoodsImage.query.filter_by(image_id=image_id, goods_id=goods_id).first()
    if not img:
        return jsonify(success=False, message='图片不存在'), 404

    delete_upload_file(img.image_url)
    db.session.delete(img)

    remaining = GoodsImage.query.filter_by(goods_id=goods_id)\
        .order_by(GoodsImage.sort_order).all()
    if not any(r.is_main for r in remaining) and remaining:
        remaining[0].is_main = 1

    db.session.commit()
    return jsonify(success=True, message='图片已删除')


@goods_bp.route('/<int:goods_id>/images/set_main', methods=['POST'])
@login_required
def set_main_image(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    if goods.seller_id != session['user_id']:
        return jsonify(success=False, message='无权操作'), 403

    data = request.get_json() or {}
    image_id = data.get('image_id')
    img = GoodsImage.query.filter_by(image_id=image_id, goods_id=goods_id).first()
    if not img:
        return jsonify(success=False, message='图片不存在'), 404

    GoodsImage.query.filter_by(goods_id=goods_id).update({'is_main': 0})
    img.is_main = 1
    db.session.commit()
    return jsonify(success=True, message='已设为主图')


@goods_bp.route('/<int:goods_id>/images/reorder', methods=['POST'])
@login_required
def reorder_images(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    if goods.seller_id != session['user_id']:
        return jsonify(success=False, message='无权操作'), 403

    data = request.get_json() or {}
    ordered_ids = data.get('image_ids', [])
    existing_ids = {img.image_id for img in goods.images}

    if set(ordered_ids) != existing_ids or len(ordered_ids) != len(existing_ids):
        return jsonify(success=False, message='图片ID列表不匹配'), 400

    for idx, img_id in enumerate(ordered_ids):
        GoodsImage.query.filter_by(image_id=img_id, goods_id=goods_id)\
            .update({'sort_order': idx})

    db.session.commit()
    return jsonify(success=True, message='排序已更新')


@goods_bp.route('/<int:goods_id>/images/add', methods=['POST'])
@login_required
def add_images(goods_id):
    goods = Goods.query.get_or_404(goods_id)
    if goods.seller_id != session['user_id']:
        return jsonify(success=False, message='无权操作'), 403

    files = request.files.getlist('images')
    if not files or all(not f.filename for f in files):
        return jsonify(success=False, message='未选择文件'), 400

    has_existing = GoodsImage.query.filter_by(goods_id=goods_id).count() > 0
    max_order = db.session.query(db.func.max(GoodsImage.sort_order))\
        .filter_by(goods_id=goods_id).scalar() or -1

    count = 0
    for file in files:
        if file and file.filename:
            try:
                path = save_upload_file(file, f'goods_{goods_id}')
            except ValueError:
                continue
            max_order += 1
            img = GoodsImage(
                goods_id=goods_id,
                image_url=path,
                is_main=1 if (not has_existing and count == 0) else 0,
                sort_order=max_order
            )
            db.session.add(img)
            count += 1

    db.session.commit()
    return jsonify(success=True, count=count, message=f'成功上传 {count} 张图片')
