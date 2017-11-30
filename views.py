from flask import redirect, url_for, send_file
from flask import render_template, flash

from forms import LoginForm
from main import app
from scripts.param_table.views import pt
from scripts.users_activity_report.views import at

app.register_blueprint(pt)
app.register_blueprint(at)

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




@app.route('/scripts')
def scripts():
    __title__ = 'Scripts'
    links = {
        'param_table': url_for('param_table.param_table', network_id=''),
        'user_report': url_for('user_activity_report.user_report', network_id=2)  # Пока выставлен БКЕ
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
        return redirect(url_for('param_table.download_param_table', shortcut=shortcut, well_name=well_name))



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
