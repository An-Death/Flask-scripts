from datetime import datetime, timedelta

from flask import Blueprint, request, render_template
from scr.projects.project import Project as P

from models.models import *
from .forms import ChoseDateForm
from .users_report import get_table

at = Blueprint('user_activity_table', __name__, url_prefix='/scripts/user_activity_table')


@at.route('/<regex("[0-9]+|''"):network_id>', methods=['POST', 'GET'])
def user_report(network_id=None):
    __title__ = 'User Report'
    form = ChoseDateForm(request.form)
    # todo сделать дату старта и стопа на начало месяца каждый раз!
    _dt = datetime.now()
    _timedelta = timedelta(weeks=12)
    _dt_from = _dt - _timedelta
    _dt = _dt.strftime('%Y-%m-%d')
    _dt_from = _dt_from.strftime('%Y-%m-%d')

    if form.validate_on_submit():
        post = True
        n_id = Project.query.filter(Project.network_id == network_id).one()
        serv = Server.query.filter(Server.id == n_id.server_id).one()
        table = get_table(P(serv.shortcuts.split(',')[0]).sql_sessionmaker())
        table = table.to_html()
    else:
        project = Project.query.filter(Project.network_id == network_id).first()
    return render_template('users_activiry_report/user_report.html', vars=locals())
