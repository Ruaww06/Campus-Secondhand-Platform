from flask import request, redirect, url_for, flash, render_template, session, jsonify
from app import db
from app.favorite import favorite_bp
from app.models import Favorite, Goods
from app.decorators import login_required


def _is_ajax():
    """判断请求是否来自 AJAX / fetch。"""
    return (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.content_type == 'application/json'
            or request.accept_mimetypes.best == 'application/json')


@favorite_bp.route('/add', methods=['POST'])
@login_required
def add_favorite():
    """添加商品到收藏。"""
    goods_id = request.form.get('goods_id', type=int)
    if not goods_id:
        if _is_ajax():
            return jsonify(success=False, message='商品ID无效')
        flash('商品ID无效', 'error')
        return redirect(url_for('goods.index'))

    goods = Goods.query.get(goods_id)
    if not goods:
        if _is_ajax():
            return jsonify(success=False, message='商品不存在')
        flash('商品不存在', 'error')
        return redirect(url_for('goods.index'))

    user_id = session['user_id']
    existing = Favorite.query.filter_by(user_id=user_id, goods_id=goods_id).first()
    if existing:
        if _is_ajax():
            return jsonify(success=False, message='已经收藏过了')
        flash('该商品已在收藏夹中', 'info')
        return redirect(url_for('goods.detail', goods_id=goods_id))

    favorite = Favorite(user_id=user_id, goods_id=goods_id)
    db.session.add(favorite)
    db.session.commit()

    if _is_ajax():
        return jsonify(success=True, message='收藏成功')
    flash('收藏成功', 'success')
    return redirect(url_for('goods.detail', goods_id=goods_id))


@favorite_bp.route('/remove', methods=['POST'])
@login_required
def remove_favorite():
    """从收藏夹移除商品。"""
    goods_id = request.form.get('goods_id', type=int)
    if not goods_id:
        if _is_ajax():
            return jsonify(success=False, message='商品ID无效')
        flash('商品ID无效', 'error')
        return redirect(url_for('favorite.my_favorites'))

    user_id = session['user_id']
    favorite = Favorite.query.filter_by(user_id=user_id, goods_id=goods_id).first()
    if not favorite:
        if _is_ajax():
            return jsonify(success=False, message='收藏记录不存在')
        flash('收藏记录不存在', 'error')
        return redirect(url_for('favorite.my_favorites'))

    db.session.delete(favorite)
    db.session.commit()

    if _is_ajax():
        return jsonify(success=True, message='已取消收藏')
    flash('已取消收藏', 'success')
    return redirect(url_for('favorite.my_favorites'))


@favorite_bp.route('/my')
@login_required
def my_favorites():
    """我的收藏列表。"""
    user_id = session['user_id']
    favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
    return render_template('favorite/my_favorites.html', favorites=favorites)
