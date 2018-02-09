import asyncio

from flask import redirect, url_for, request
from flask import render_template, flash

from app import app
from forms import LoginForm
from models.models import *
from scripts.ims_params_info.views import ims
from scripts.param_table.views import pt
from scripts.speed_test.views import st
from scripts.users_activity_report.forms import ChoseDateForm
from scripts.users_activity_report.views import at

app.register_blueprint(pt)
app.register_blueprint(at)
app.register_blueprint(st)
app.register_blueprint(ims)

setattr(app, 'loop', asyncio.get_event_loop())


@app.route('/')
def index():
    return redirect(url_for('main'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    __title__ = 'LogIn'
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for name="{}" remember = "{}" '.format(form.login.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', vars=locals(), form=form)


@app.route('/main.html')
def main():
    """:returns
    List of supported and unsupported projects
    """
    __title__ = 'Выберете проект:'
    sup_dict = {'Поддержка': Project.query.filter_by(supported=0),
                'Сопровождение': Project.query.filter_by(supported=1)}
    return render_template('main.html', vars=locals())


@app.route('/<int:network_id>/info')
def project_info(network_id):
    __title__ = 'Project info'
    project = Project.get(network_id)
    wells = project.get_active_wells()
    speed_server = 'Online' if project.speed_test_server_status() else 'Offline'

    return render_template('project_info.html', vars=locals())


@app.route('/<int:network_id>/speed_server')
def speed_server(network_id):
    project = Project.get(network_id)
    if project.speed_test_server_status():
        project.stop_speed_test_server()
    else:
        project.run_speed_test_server()
    return redirect(url_for('project_info', network_id=network_id))

@app.route('/<int:network_id>/edit')
def project_edit(network_id):
    project = Project.get(network_id=network_id)
    __title__ = f'{project.name} INFO'
    return render_template('project_edit.html', vars=locals())


@app.route('/<int:network_id>/<int:well_id>/info')
def well_info(network_id, well_id):
    project = Project.get(network_id)
    well = project.get_well_by_id(well_id)
    __title__ = f'{project.name}>>{well.name}'
    gbox = well.gbox
    return render_template('well_info.html', vars=locals())

@app.route('/scripts')
# @cache.cached(timeout=60)
def scripts():
    __title__ = 'Scripts'
    projects = Project.all_supported()
    form = ChoseDateForm(request.form)
    links = {
        'activity table': 'user_activity_table.user_report',
        'param table': 'param_table.param_table',
        'speed test': 'speed_test.speed_test'
    }
    return render_template('scripts.html', vars=locals())


# @app.errorhandler(404)
# def page_not_found(error):
#     return redirect(url_for('index'))
#     # return render_template('page_not_found.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # Base.session.rollback()
    # todo Написать отправку ошибок на почту
    # app.db_session.rollback()
    flash('Произошла ошибка сообщите адинистратору!')
    return redirect(url_for('index'))
    # return render_template('500.html'), 500
