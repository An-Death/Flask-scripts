from datetime import datetime, timedelta

from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms.validators import DataRequired

# По умолчанию берётся начало текущего месца и 01 число трем месяцами ранее (квартал)
default_dt_from = lambda: (datetime.today() - timedelta(weeks=12)).replace(day=1)
default_dt_to = lambda: datetime.today().replace(day=1)

class ChoseDateForm(FlaskForm):
    date_from = DateField('Начало', validators=[DataRequired()], default=default_dt_from)
    date_to = DateField('Конец', validators=[DataRequired()], default=default_dt_to)
