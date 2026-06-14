from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度需在3-20字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码最少6位')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    real_name = StringField('真实姓名', validators=[
        DataRequired(message='真实姓名不能为空')
    ])
    student_id = StringField('学号', validators=[
        DataRequired(message='学号不能为空')
    ])
    phone = StringField('手机号', validators=[
        DataRequired(message='手机号不能为空')
    ])
    email = StringField('邮箱', validators=[
        Optional(),
        Email(message='请输入有效的邮箱地址')
    ])
    wechat = StringField('微信号', validators=[Optional()])
    region = SelectField('校区', choices=[
        ('北区', '北区'),
        ('南区', '南区'),
        ('其他', '其他')
    ], validators=[DataRequired(message='请选择校区')])
    submit = SubmitField('注册')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空')
    ])
    submit = SubmitField('登录')


class ProfileForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=20, message='用户名长度需在3-20字符之间')
    ])
    real_name = StringField('真实姓名', validators=[
        DataRequired(message='真实姓名不能为空')
    ])
    student_id = StringField('学号', validators=[
        DataRequired(message='学号不能为空')
    ])
    phone = StringField('手机号', validators=[
        DataRequired(message='手机号不能为空')
    ])
    email = StringField('邮箱', validators=[
        Optional(),
        Email(message='请输入有效的邮箱地址')
    ])
    wechat = StringField('微信号', validators=[Optional()])
    region = SelectField('校区', choices=[
        ('北区', '北区'),
        ('南区', '南区'),
        ('其他', '其他')
    ], validators=[DataRequired(message='请选择校区')])
    submit = SubmitField('保存修改')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[
        DataRequired(message='请输入原密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, message='新密码最少6位')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请确认新密码'),
        EqualTo('new_password', message='两次输入的新密码不一致')
    ])
    submit = SubmitField('修改密码')
