import asyncio

from flask import redirect, url_for, request
from flask import render_template, flash

from app import app
from forms import LoginForm
from models.models import *
from scripts.param_table.views import pt
from scripts.speed_test.views import st
from scripts.users_activity_report.forms import ChoseDateForm
from scripts.users_activity_report.views import at

app.register_blueprint(pt)
app.register_blueprint(at)
app.register_blueprint(st)

setattr(app, 'loop', asyncio.get_event_loop())


@app.route('/')
def index():
    return redirect(url_for('scripts'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    __title__ = 'LogIn'
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for name="{}" remember = "{}" '.format(form.login.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', vars=locals(), form=form)


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


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('index'))
    # return render_template('page_not_found.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # Base.session.rollback()
    # todo Написать отправку ошибок на почту
    # app.db_session.rollback()
    flash('Произошла ошибка сообщите адинистратору!')
    return redirect(url_for('index'))
    # return render_template('500.html'), 500
