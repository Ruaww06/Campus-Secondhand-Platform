from functools import wraps
from flask import session, redirect, url_for, abort, request, flash
from app import db


def login_required(f):
    """未登录用户重定向到登录页，登录后返回原页面；已登录但被禁用户清 session 并提示。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        from app.models import User
        user = db.session.get(User, session['user_id'])
        if not user or user.status == 'banned':
            session.clear()
            flash('账号已被禁用，请重新登录', 'error')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """非管理员返回 403；已登录但被禁用户清 session 并提示。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        from app.models import User
        user = db.session.get(User, session['user_id'])
        if not user or user.status == 'banned':
            session.clear()
            flash('账号已被禁用，请重新登录', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
