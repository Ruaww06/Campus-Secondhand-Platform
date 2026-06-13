import secrets
from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, session, abort
from app.order import order_bp
from app import db
from app.models import OrderInfo, Goods, User
from app.decorators import login_required


def _generate_order_no():
    """生成唯一订单号: YYYYMMDDHHmmss + 6位随机十六进制"""
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    rand_hex = secrets.token_hex(3)  # 6 hex chars
    return f"{now}{rand_hex}"


@order_bp.route('/create', methods=['POST'])
@login_required
def create():
    goods_id = request.form.get('goods_id', type=int)
    goods = Goods.query.get_or_404(goods_id)

    # 不能购买自己的商品
    if goods.seller_id == session['user_id']:
        flash('不能购买自己发布的商品', 'error')
        return redirect(url_for('goods.detail', goods_id=goods_id))

    # 商品必须在售
    if goods.status != 'on_sale':
        flash('该商品当前不可购买', 'error')
        return redirect(url_for('goods.detail', goods_id=goods_id))

    # 创建订单
    order = OrderInfo(
        order_no=_generate_order_no(),
        buyer_id=session['user_id'],
        seller_id=goods.seller_id,
        goods_id=goods.goods_id,
        status='pending',
        remark=request.form.get('remark') or None
    )
    db.session.add(order)

    # 标记商品为已售
    goods.status = 'sold'

    db.session.commit()

    flash('下单成功，请等待卖家确认', 'success')
    return redirect(url_for('order.detail', order_id=order.order_id))


@order_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    order = OrderInfo.query.get_or_404(order_id)

    # 验证用户是买家或卖家
    if order.buyer_id != session['user_id'] and order.seller_id != session['user_id']:
        abort(403)

    return render_template('order/detail.html', order=order)


@order_bp.route('/purchases')
@login_required
def my_purchases():
    page = request.args.get('page', 1, type=int)
    pagination = OrderInfo.query \
        .filter_by(buyer_id=session['user_id']) \
        .order_by(OrderInfo.created_at.desc()) \
        .paginate(page=page, per_page=15, error_out=False)

    return render_template('order/my_purchases.html',
                           orders=pagination.items,
                           pagination=pagination)


@order_bp.route('/sales')
@login_required
def my_sales():
    page = request.args.get('page', 1, type=int)
    pagination = OrderInfo.query \
        .filter_by(seller_id=session['user_id']) \
        .order_by(OrderInfo.created_at.desc()) \
        .paginate(page=page, per_page=15, error_out=False)

    return render_template('order/my_sales.html',
                           orders=pagination.items,
                           pagination=pagination)


@order_bp.route('/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm(order_id):
    order = OrderInfo.query.get_or_404(order_id)

    # 验证是卖家
    if order.seller_id != session['user_id']:
        abort(403)

    # 验证订单状态为 pending
    if order.status != 'pending':
        flash('当前订单状态不可确认', 'error')
        return redirect(url_for('order.detail', order_id=order_id))

    order.status = 'confirmed'
    order.goods.status = 'sold'
    db.session.commit()

    flash('订单已确认', 'success')
    return redirect(url_for('order.my_sales'))


@order_bp.route('/<int:order_id>/complete', methods=['POST'])
@login_required
def complete(order_id):
    order = OrderInfo.query.get_or_404(order_id)

    # 验证是买家
    if order.buyer_id != session['user_id']:
        abort(403)

    # 验证订单状态为 confirmed
    if order.status != 'confirmed':
        flash('当前订单状态不可完成', 'error')
        return redirect(url_for('order.detail', order_id=order_id))

    order.status = 'completed'
    db.session.commit()

    flash('订单已完成，快去评价吧！', 'success')
    return redirect(url_for('review.create_review', order_id=order_id))


@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel(order_id):
    order = OrderInfo.query.get_or_404(order_id)

    # 验证是买家
    if order.buyer_id != session['user_id']:
        abort(403)

    # 只能在 pending 状态取消
    if order.status != 'pending':
        flash('当前订单状态不可取消', 'error')
        return redirect(url_for('order.detail', order_id=order_id))

    order.status = 'cancelled'
    # 恢复商品为在售状态
    order.goods.status = 'on_sale'
    db.session.commit()

    flash('订单已取消', 'success')

    if session['user_id'] == order.buyer_id:
        return redirect(url_for('order.my_purchases'))
    else:
        return redirect(url_for('order.my_sales'))
