from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, FieldList, StringField, RadioField, DateField
from wtforms.validators import DataRequired



class ParamTableForm(FlaskForm):
    project = RadioField('ProjectName', validators=[DataRequired()])
    well = SelectField('WellName', validators=[DataRequired()])
    records = FieldList('Records', 'records', validators=[], default=(1,11,12))
    limit_selector = SelectField('Limits',
                                label='limit_selector',
                                validators=[DataRequired()],
                                choices={'weeks':'weeks',
                                          'days':'days',
                                          'custom':'custom',
                                          'full':'full'},
                                default='weeks')
    limit_value = IntegerField('LimitValue', label='limit_value', validators=[DataRequired()])
    limit_custom_from = DateField('From', validators=[DataRequired()])
    limit_custom_to = DateField('To', validators=[DataRequired()])
