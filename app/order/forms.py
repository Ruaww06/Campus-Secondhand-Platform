from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class OrderCreateForm(FlaskForm):
    remark = StringField('订单备注', validators=[
        Optional(),
        Length(max=255, message='备注最多255字符')
    ])
    submit = SubmitField('确认下单')
