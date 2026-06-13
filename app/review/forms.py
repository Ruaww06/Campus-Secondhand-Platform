from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional


class ReviewForm(FlaskForm):
    """评价表单。"""
    order_id = IntegerField('订单ID', validators=[DataRequired()])
    rating = IntegerField('评分', validators=[
        DataRequired(message='请选择评分'),
        NumberRange(min=1, max=5, message='评分必须在1-5之间')
    ])
    content = TextAreaField('评价内容', validators=[Optional()])
    submit = SubmitField('提交评价')
