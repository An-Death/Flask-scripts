from flask import Blueprint, request, render_template, send_from_directory

from app import app
from models.models import *
from .forms import ChoseDateForm
from .user_activity_report import main, create_report

at = Blueprint('user_activity_table', __name__, url_prefix='/scripts/user_activity_table')


@at.route('/')
@at.route('/<int:network_id>', methods=['GET', 'POST'])
def user_report(network_id=None):
    __title__ = 'User Report'
    form = ChoseDateForm(request.form)
    projects = Project.all_supported()

    if form.validate_on_submit():
        ready = True  # def are_file_ready?
        project = Project.get(network_id)
        period_start = form.data.get('date_from')
        period_stop = form.data.get('date_to')
        check = form.data.get('check')
        file_name = f'{network_id}/{period_start}_{period_stop}.xlsx'
        # создаём таблицы
        user_table, video_table, total_table = main(project.sqlsession, period_start, period_stop)
        if check:
            return render_template('users_activity_table/table.html', vars=locals())
        # записываем в фаил
        create_report(app.config['USER_ACTIVITY_DIR_PATH'] + file_name, user_table, video_table, total_table)
        # return redirect(url_for('.upload', file_name=file_name))

    return render_template('users_activity_table/user_report.html', vars=locals())


@at.route('/upload/<path:file_name>')
def upload(file_name):
    file_path = app.config['USER_ACTIVITY_DIR_PATH']
    attachment_filename = 'Отчёт GTI-online.xlsx'.encode('utf-8')
    return send_from_directory(file_path, file_name,
                               as_attachment=True,
                               mimetype='text/xlsx; charset=utf-8',
                               attachment_filename=attachment_filename)
