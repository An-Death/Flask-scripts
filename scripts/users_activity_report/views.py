from pathlib import Path

from flask import Blueprint, request, render_template, send_from_directory, flash, redirect, url_for

from app import app
from models.models import *
from .forms import ChoseDateForm
from .users_report import get_table

at = Blueprint('user_activity_table', __name__, url_prefix='/scripts/user_activity_table')


@at.route('/')
@at.route('/<int:network_id>', methods=['GET', 'POST'])
def user_report(network_id=None):
    __title__ = 'User Report'
    form = ChoseDateForm(request.form)
    projects = Project.all_supported()

    if form.validate_on_submit():
        project = Project.get(network_id)
        period_start = form.date_from
        period_stop = form.date_to
        serv = Server.query.filter(Server.id == project.server_id).one()
        table = get_table(project.sqlsession)
        table = table.to_html()
        return render_template('users_activity_report/table.html', vars=locals())
        # todo Заставить формировать отчёт
    return render_template('users_activity_report/user_report.html', vars=locals())


@at.route('/upload/<path:network_id>/<path:file_name>')
def upload(network_id, file_name):
    file_path = app.config['USER_ACTIVITY_DIR_PATH']
    file_path = Path(file_path).joinpath(f'{network_id}')
    if file_path.exists():
        file_name = f'{file_name}.xlsx'
        attachment_filename = 'Отчёт GTI-online.xlsx'.encode('utf-8')
        return send_from_directory(file_path, file_name,
                                   as_attachment=True,
                                   mimetype='text/xlsx; charset=utf-8',
                                   attachment_filename=attachment_filename)

    else:
        flash(f'Файла отчёта {file_name} нет, создайте фаил.')
        return redirect(url_for('.user_report', network_id=network_id))
