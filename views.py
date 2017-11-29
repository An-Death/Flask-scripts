from pathlib import Path

from flask import redirect, url_for, request, send_file
from flask import render_template, flash
from scr.projects.project import Project as P

from forms import LoginForm
from main import app
from models.models import *
from scripts.param_table import scr
from scripts.users_activity_report.users_report import get_table


# todo разнести вьюхи по различным приложениям
@app.route('/')
def index():
    return redirect(url_for('scripts'))


@app.route('/login', methods = ['GET', 'POST'])
def login():
    __title__ = 'LogIn'
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for name="{}" remember = "{}" '.format(form.login.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', vars=locals(), form=form)

@app.route(r'/scripts/param_table/<regex("[0-9]+|''"):network_id>', methods=['GET', 'POST'])
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.query.filter(Project.supported == 1).all()
    if 'well_name' not in request.values.keys():
        if not network_id:
            return render_template('param_table.html', vars=locals())
        else:
            n_id = Project.query.filter(Project.network_id == network_id).one()
            serv = Server.query.filter(Server.id == n_id.server_id).one()
            prj = P(serv.name)
            session = prj.sql_sessionmaker()
            wells = scr.get_active_wells(session, network_id)
            return render_template('param_table.html', vars=locals())
    else:
        req = request
        prj_name = request.values.get('project_name')
        prj = [prj for prj in projects if prj.name_ru == prj_name]
        server = prj[0].server
        shortcuts = server.shortcuts
        short = shortcuts.split(',')[0]
        well_name = request.values.get('well_name')
        list_records = request.values.get('records', '1,11,12').split(',')
        # scr.main(short, well_name)
        # return redirect(url_for('download', method='param_table_{}'.format(well_name)))
        return download('param_table', short, well_name)


@app.route('/scripts/user_report/<regex("[0-9]+|''"):network_id>', methods=['POST', 'GET'])
def user_report(network_id=None):
    __title__ = 'User Report'
    if request.method == 'GET':
        project = Project.query.filter(Project.network_id == network_id).first()
    else:
        post = True
        n_id = Project.query.filter(Project.network_id == network_id).one()
        serv = Server.query.filter(Server.id == n_id.server_id).one()
        table = get_table(P(serv.shortcuts.split(',')[0]).sql_sessionmaker())
        table = table.to_html()
    return render_template('user_report.html', vars=locals())


@app.route('/scripts')
def scripts():
    __title__ = 'Scripts'
    links = {
        'param_table': url_for('param_table', network_id=''),
        'user_report': url_for('user_report', network_id=2)  # Пока выставлен БКЕ
    }
    return render_template('scripts.html', vars=locals())


# @app.route('/download/<string:method>')
def download(method, shortcut=None, well_name=None, file_name=None):
    # todo Загружаем последний фаил из нужной папки
    if method == 'user_report':
        file_path = '/home/as/vagrant/support_scripts/scr/user_activity_report/reports/GTI-online.xlsx'
        return send_file(file_path, as_attachment=True,
                         mimetype='text/xlsx; charset=utf-8',
                         attachment_filename='Отчёт GTI-Online.xlsx'.encode('utf-8'))
    elif method == 'param_table' and shortcut and well_name:
        return redirect(url_for('download_param_table', shortcut=shortcut, well_name=well_name))


@app.route('/download_param_table/<shortcut>/<well_name>', methods=['GET','POST'])
def download_param_table(shortcut=None, well_name=None):
    __title__ = 'Download param table'
    if request.method == 'GET':
        key = True
        return render_template('download_param_table.html', vars=locals())
    elif request.method == 'POST':
        shortcut, well_name = request.values.get('shortcut'), request.values.get('well_name')
        # todo Вынести выполнение функции в отдельный тред
        # todo Отлавливать остановки
        # todo Возвращать фаил в браузер после выполнения
        scr.main(shortcut, well_name)  # Скрипт формирует и сохраняет фаил в шару
        return render_template('download_param_table.html', vars=locals())


@app.route('/download_param_table/download/<well_name>')
def download_pt(well_name):
    file_name = '{}.xlsx'.format(well_name).replace(' ', '_')
    file_path = Path('/home/as/share/tables/param_for_customer') # for test
    file_path = file_path if file_path.exists() else Path('/share') # for docker
    file_path = file_path.joinpath(file_name)
    file_name = file_name.encode('utf-8')
    return send_file(file_path.__str__(), as_attachment=True,
                     mimetype='text/xlsx; charset=utf-8',
                     attachment_filename=file_name)


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))
    # return render_template('page_not_found.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # Base.session.rollback()
    # todo Написать отправку ошибок на почту
    app.db_session.rollback()
    flash('Произошла ошибка сообщите адинистратору!')
    return redirect(url_for('index'))
    # return render_template('500.html'), 500
