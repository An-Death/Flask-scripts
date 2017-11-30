from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms.validators import DataRequired


class ChoseDateForm(FlaskForm):
    date_from = DateField('From', validators=[DataRequired()])
    date_to = DateField('To', validators=[DataRequired()])
