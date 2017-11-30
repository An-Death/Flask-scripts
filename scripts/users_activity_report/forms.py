from datetime import datetime, timedelta

from flask_wtf import Form
from wtforms import DateTimeField
from wtforms.validators import DataRequired

_dt = datetime.now()
_timedelta = timedelta(weeks=12)
_dt_from = _dt - _timedelta
_dt = _dt.strftime('%Y-%m-%d %H:%M:%S')
_dt_from = _dt_from.strftime('%Y-%m-%d %H:%M:%S')


class ChoseDateForm(Form):
    date_from = DateTimeField('From', validators=[DataRequired()], default=_dt_from)
    date_to = DateTimeField('To', validators=[DataRequired()], default=_dt)
