from flask import Blueprint, request, render_template, send_file, url_for, redirect, flash
from sqlalchemy.exc import OperationalError

from app import app
from models.models import *
from scripts.param_table import scr
from scripts.param_table.scr import DateLimit

pt = Blueprint('param_table', __name__, url_prefix='/scripts/param_table')


@pt.route('/')
@pt.route('/<int:network_id>')
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.query.filter(Project.supported == 1).all()
    if not network_id:
        # Return list of {projects}
        return render_template('param_table/param_table.html', vars=locals())
    else:
        # Get project from list by network_id
        project = [project for project in projects if project.network_id == network_id][0]
        try:
            # Getting active wells from current project
            wells = project.get_active_wells()
        except OperationalError:
            flash(f'База данных проекта {project.name_ru} недоступна!')
            return redirect(url_for('.param_table', network_id=None))
        finally:
            return render_template('param_table/param_table.html', vars=locals())


@pt.route('/<int:network_id>/<regex("\d+|''"):well_id>', methods=['GET', 'POST'])
def prepare_table(network_id=None, well_id=None):
    """
    Вьюха для проверки подготовки объектов для создания таблицы.

    Работает как GET, так и POST. При GET передаётся network_id нужного проекта и id скважины
    Вьюха проверяет:
        1. Наличие скважины по id
        2. Наличие соответствующих таблиц WITS_RECORD{}_IDX_{} и DATA для выбранной скважины
    :param network_id:
    :param well_id:
    :return:
    """
    project = Project.query.filter(Project.network_id == network_id).one()
    well_id = request.values.get('well_id') if request.method == 'POST' else well_id

    # Get data from POST request if they are... else default
    list_of_records = scr.return_list_from_str(request.values.get('records', [1, 11, 12]))
    limit = request.values.get('limit', 'weeks')
    limit_value = request.values.get('limit_value', 2)
    # Prepare date limits
    dt = DateLimit(limit_value, limit)
    # if no limits in POST request set default limits
    limit_from = request.values.get('limit_from', dt.begin)
    limit_to = request.values.get('limit_to', dt.end)

    record_tables = {}
    well = project.get_well_by_id(well_id)

    # Start checking user input
    # Are well does exist?
    if not well:
        flash(f'Скважины с id:{well_id} на проекте {project.name_ru} нет!')
        return redirect(url_for('.param_table', network_id=network_id))
    else:
        well = well[0]
    # Well exist... well keep checking
    for record in list_of_records[:]:
        tables = well.check_record_tables(record)
        if tables is None:
            flash(f'Таблиц с данными для рекода: {record} '
                  f'- Не существует. Удаляем рекорд: {record} из списка: {list_of_records}')
            list_of_records.remove(record)
        else:
            # Saving sqla.Tables in dict
            record_tables[record] = tables
    # List is empty?
    if not list_of_records:
        flash(f'Отсутствуют данные в скважние {well.name}\n'
              f'Проверьте скважину или список рекордов: {request.values.get("records", [1, 11, 12])}')
        return redirect(url_for('.param_table', network_id=network_id))
    # List is not empty...
    for r, tables in record_tables.items():
        q = project.session.query(tables['idx']).filter(tables['idx'].c.date > limit_from).filter(
            tables['idx'].c.date < limit_to)
        if q.count() < 0:
            flash(f'Отсутствуют данные в таблицe: {tables["idx"]} ... '
                  f'Удаляем рекорд: {r} из списка: {list_of_records}')
            list_of_records.remove(r)
    if not list_of_records:
        flash(f'Отсутствуют данные в скважние {well.name} \n'
              f'Проверьте скважину или список рекордов: {request.values.get("records", [1, 11, 12])}')
        return redirect(url_for('.param_table', network_id=network_id))

    # if all checks is clear do:
    well_name = well.name or well.alias
    shortcut = project.shortcut
    return redirect(url_for('param_table.download_param_table', shortcut=shortcut, well_name=well_name))

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
    # file_path = Path('/home/as/share/tables/param_for_customer')  # for test
    # file_path = file_path if file_path.exists() else Path('/share')  # for docker
    file_path = app.config.PARAM_TABLE_DIR_PATH
    file_path = file_path.joinpath(file_name)
    file_name = file_name.encode('utf-8')
    # todo Поменять на send_from_directory!!!!!!
    return send_file(file_path.__str__(), as_attachment=True,
                     mimetype='text/xlsx; charset=utf-8',
                     attachment_filename=file_name)
