from pathlib import Path

from flask import Blueprint, request, render_template, send_file, url_for, redirect
from scr.projects.project import Project as P

from models.models import *
from scripts.param_table import scr

pt = Blueprint('param_table', __name__, url_prefix='/scripts/param_table')


@pt.route('/<regex("[0-9]+|''"):network_id>', methods=['GET', 'POST'])
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.query.filter(Project.supported == 1).all()
    if 'well_name' not in request.values.keys():
        if not network_id:
            return render_template('param_table/param_table.html', vars=locals())
        else:
            n_id = Project.query.filter(Project.network_id == network_id).one()
            serv = Server.query.filter(Server.id == n_id.server_id).one()
            prj = P(serv.name)
            session = prj.sql_sessionmaker()
            wells = scr.get_active_wells(session, network_id)
            return render_template('param_table/param_table.html', vars=locals())
    else:
        prj_name = request.values.get('project_name')
        prj = [prj for prj in projects if prj.name_ru == prj_name]
        server = prj[0].server
        shortcuts = server.shortcuts
        short = shortcuts.split(',')[0]
        well_name = request.values.get('well_name')
        list_records = request.values.get('records', '1,11,12').split(',')
        return redirect(url_for('param_table.download_param_table', shortcut=short, well_name=well_name))



@pt.route('/download_param_table/<shortcut>/<well_name>', methods=['GET', 'POST'])
def download_param_table(shortcut=None, well_name=None):
    __title__ = 'Download param table'
    if request.method == 'GET':
        key = True
        return render_template('param_table/download_param_table.html', vars=locals())
    elif request.method == 'POST':
        shortcut, well_name = request.values.get('shortcut'), request.values.get('well_name')
        # todo Вынести выполнение функции в отдельный тред
        # todo Отлавливать остановки
        # todo Возвращать фаил в браузер после выполнения
        scr.main(shortcut, well_name)  # Скрипт формирует и сохраняет фаил в шару
        return render_template('param_table/download_param_table.html', vars=locals())


@pt.route('/download_param_table/download/<well_name>')
def download_pt(well_name):
    file_name = '{}.xlsx'.format(well_name).replace(' ', '_')
    file_path = Path('/home/as/share/tables/param_for_customer')  # for test
    file_path = file_path if file_path.exists() else Path('/share')  # for docker
    file_path = file_path.joinpath(file_name)
    file_name = file_name.encode('utf-8')
    # todo Поменять на send_from_directory!!!!!!
    return send_file(file_path.__str__(), as_attachment=True,
                     mimetype='text/xlsx; charset=utf-8',
                     attachment_filename=file_name)
