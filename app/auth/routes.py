from flask import render_template, redirect, url_for, flash, request, session
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm, ProfileForm, ChangePasswordForm
from app import db
from app.models import User
from app.decorators import login_required
from werkzeug.security import generate_password_hash, check_password_hash


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('该用户名已被注册', 'error')
            return render_template('auth/register.html', form=form)

        # 检查学号是否已存在
        existing_student = User.query.filter_by(student_id=form.student_id.data).first()
        if existing_student:
            flash('该学号已被注册', 'error')
            return render_template('auth/register.html', form=form)

        # 创建用户
        user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            real_name=form.real_name.data,
            student_id=form.student_id.data,
            phone=form.phone.data,
            email=form.email.data or None,
            wechat=form.wechat.data or None,
            region=form.region.data,
            role='user',
            status='active'
        )
        db.session.add(user)
        db.session.commit()

        # 设置会话
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.role

        flash('注册成功，欢迎加入！', 'success')
        return redirect(url_for('goods.index'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None:
            flash('用户名或密码错误', 'error')
            return render_template('auth/login.html', form=form)

        if user.status != 'active':
            flash('账号已被禁用', 'error')
            return render_template('auth/login.html', form=form)

        if not check_password_hash(user.password, form.password.data):
            flash('用户名或密码错误', 'error')
            return render_template('auth/login.html', form=form)

        # 登录成功，设置会话
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.role

        flash('登录成功', 'success')

        # 处理 next 参数跳转（支持 GET 和 POST）
        next_url = request.form.get('next') or request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('goods.index'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('您已退出登录', 'info')
    return redirect(url_for('goods.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('auth/profile.html', user=user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    form = ProfileForm()

    if form.validate_on_submit():
        # 唯一性校验：排除自身
        existing_username = User.query.filter(
            User.username == form.username.data,
            User.user_id != user.user_id
        ).first()
        if existing_username:
            flash('用户名已被占用', 'error')
            return render_template('auth/edit_profile.html', form=form)

        existing_student = User.query.filter(
            User.student_id == form.student_id.data,
            User.user_id != user.user_id
        ).first()
        if existing_student:
            flash('学号已被注册', 'error')
            return render_template('auth/edit_profile.html', form=form)

        user.username = form.username.data
        user.real_name = form.real_name.data
        user.student_id = form.student_id.data
        user.phone = form.phone.data
        user.email = form.email.data or None
        user.wechat = form.wechat.data or None
        user.region = form.region.data
        db.session.commit()
        # 更新 session 中的 username
        session['username'] = user.username
        flash('资料更新成功', 'success')
        return redirect(url_for('auth.profile'))

    # GET 请求：填充当前用户信息
    form.username.data = user.username
    form.real_name.data = user.real_name
    form.student_id.data = user.student_id
    form.phone.data = user.phone
    form.email.data = user.email
    form.wechat.data = user.wechat
    form.region.data = user.region

    return render_template('auth/edit_profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # 验证原密码
        if not check_password_hash(user.password, form.old_password.data):
            flash('原密码不正确', 'error')
            return render_template('auth/change_password.html', form=form)

        # 更新为新密码
        user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)
