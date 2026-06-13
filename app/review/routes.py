from flask import request, redirect, url_for, flash, render_template, session
from app import db
from app.review import review_bp
from app.review.forms import ReviewForm
from app.models import Review, OrderInfo, Goods
from app.decorators import login_required


def get_reviews_by_goods(goods_id):
    """通过商品ID查询关联评价列表（供 render_goods_reviews 宏使用）。"""
    return Review.query.join(OrderInfo).filter(
        OrderInfo.goods_id == goods_id
    ).order_by(Review.created_at.desc()).all()


@review_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_review():
    """发表评价。"""
    form = ReviewForm()
    order_id = request.args.get('order_id', type=int)
    if order_id:
        form.order_id.data = order_id

    if form.validate_on_submit():
        order = OrderInfo.query.get(form.order_id.data)
        if not order:
            flash('订单不存在', 'error')
            return redirect(url_for('order.my_purchases'))

        if order.buyer_id != session['user_id']:
            flash('无权评价该订单', 'error')
            return redirect(url_for('order.my_purchases'))

        if order.status != 'completed':
            flash('订单未完成，暂不能评价', 'error')
            return redirect(url_for('order.my_purchases'))

        existing = Review.query.filter_by(order_id=order.order_id).first()
        if existing:
            flash('该订单已评价', 'error')
            return redirect(url_for('review.my_reviews'))

        review = Review(
            order_id=order.order_id,
            reviewer_id=session['user_id'],
            seller_id=order.seller_id,
            rating=form.rating.data,
            content=form.content.data or None
        )
        db.session.add(review)
        db.session.commit()
        flash('评价成功', 'success')
        return redirect(url_for('review.my_reviews'))

    return render_template('review/create.html', form=form, order_id=order_id)


@review_bp.route('/my')
@login_required
def my_reviews():
    """我发表的评价列表。"""
    reviews = Review.query.filter_by(reviewer_id=session['user_id']).order_by(Review.created_at.desc()).all()
    return render_template('review/my_reviews.html', reviews=reviews)


@review_bp.route('/seller/<int:seller_id>')
def seller_reviews(seller_id):
    """查看卖家收到的评价。"""
    from app.models import User
    seller = User.query.get_or_404(seller_id)
    reviews = Review.query.filter_by(seller_id=seller_id).order_by(Review.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=seller_id).scalar()
    return render_template('review/seller_reviews.html', seller=seller, reviews=reviews, avg_rating=avg_rating)
