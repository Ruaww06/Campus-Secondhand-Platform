from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, TextAreaField, DecimalField,
                     MultipleFileField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class GoodsForm(FlaskForm):
    title = StringField('商品名称', validators=[
        DataRequired(message='请输入商品名称'),
        Length(max=100, message='商品名称最多100字符')
    ])
    category_id = SelectField('商品分类', coerce=int, choices=[],
                              validators=[DataRequired(message='请选择商品分类')])
    description = TextAreaField('商品描述', validators=[Optional()])
    price = DecimalField('售价', validators=[
        DataRequired(message='请输入售价'),
        NumberRange(min=0, message='价格不能为负数')
    ])
    original_price = DecimalField('原价', validators=[
        Optional(),
        NumberRange(min=0, message='价格不能为负数')
    ])
    region = SelectField('校区', choices=[
        ('北区', '北区'),
        ('南区', '南区'),
        ('其他', '其他')
    ], validators=[DataRequired(message='请选择校区')])
    condition_level = SelectField('新旧程度', choices=[
        ('new', '全新'),
        ('like_new', '几乎全新'),
        ('used', '轻微使用'),
        ('old', '明显使用')
    ], validators=[DataRequired(message='请选择新旧程度')])
    contact_phone = StringField('联系电话', validators=[
        Optional(),
        Length(max=15, message='联系电话最多15字符')
    ])
    contact_wechat = StringField('微信号', validators=[
        Optional(),
        Length(max=50, message='微信号最多50字符')
    ])
    images = MultipleFileField('商品图片', validators=[Optional()])
    submit = SubmitField('发布商品')


class SearchForm(FlaskForm):
    q = StringField('搜索关键词')
    category_id = SelectField('分类', choices=[])          # populated dynamically
    min_price = StringField('最低价')
    max_price = StringField('最高价')
    region = SelectField('校区', choices=[
        ('', '全部校区'),
        ('北区', '北区'),
        ('南区', '南区'),
        ('其他', '其他')
    ])
    condition_level = SelectField('新旧程度', choices=[
        ('', '全部'),
        ('new', '全新'),
        ('like_new', '几乎全新'),
        ('used', '轻微使用'),
        ('old', '明显使用')
    ])
    sort = SelectField('排序', choices=[
        ('newest', '最新发布'),
        ('price_asc', '价格从低到高'),
        ('price_desc', '价格从高到低'),
        ('popular', '最多浏览')
    ])
