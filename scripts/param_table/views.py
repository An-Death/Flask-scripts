from pathlib import Path

from flask import Blueprint, request, render_template, url_for, redirect, flash, abort
from flask import send_from_directory
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import exc

from app import app
from models.models import *
from scripts.param_table import scr
from scripts.param_table.scr import DateLimit

pt = Blueprint('param_table', __name__, url_prefix='/scripts/param_table')


def redirect_url(default='/'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


@pt.route('/')
@pt.route('/<int:network_id>')
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.all_supported()
    # todo Переписать вьюху и шаблоны
    if not network_id:
        # Return list of {projects}=
        # projects = Project.all_supported()
        return render_template('param_table/param_table.html', vars=locals())
    else:
        project = Project.get(network_id)
        try:
            # Getting active wells from current project
            wells = project.get_active_wells()
        except OperationalError:
            flash(f'База данных проекта {project.name_ru} недоступна!')
            return redirect(url_for('.param_table', network_id=None))
        finally:
            return render_template('param_table/param_table.html', vars=locals())


@pt.route('/<int:network_id>/<regex("\d+|''"):well_id>', methods=['GET', 'POST'])
def prepare_table(network_id, well_id):
    """
    Вьюха для проверки подготовки объектов для создания таблицы.

    Работает как GET, так и POST. При GET передаётся network_id нужного проекта и id скважины
    GET: param_table/network_id/well_id

    Вьюха проверяет:
        1. Наличие скважины по id
        2. Наличие соответствующих таблиц WITS_RECORD{}_IDX_{} и DATA для выбранной скважины.
        3. Наличие данных в таблицах WITS_RECORD{}_IDX_{} по рекордам
           Если пункты 2 и 3 сработали рекорд удалятся из списка рекордов. Соответственно не будет таблицы по рекорду.
        4. (Еще не реализованно) Соответствие всех мнемоников в DATA таблице с мнемониками текущего рекорда
    :param network_id: Id
    :param well_id:
    :return:
    """
    __title__ = 'Param Table'
    network_id = network_id or request.values.get('network_id')
    project = Project.get(network_id)
    if not project or not network_id:
        flash(f'project with network_id ="{network_id}" not founded!')
        return abort(404)
    well_id = request.values.get('well_id') if request.method == 'POST' else well_id

    # Get data from POST request if they are... else default
    list_of_records = scr.return_list_from_str(request.values.get('list_of_records', [1, 11, 12]))
    limit = request.values.get('limit', 'weeks')
    limit_value = request.values.get('limit_value', 2)
    # Prepare date limits
    dt = DateLimit(limit_value, limit)
    # if no limits in POST request set default limits
    # todo make request data as datetime format
    limit_from = request.values.get('limit_from', dt.begin)
    limit_to = request.values.get('limit_to', dt.end)

    # Start checking user input
    # Are well does exist?
    try:
        well = project.get_well_by_id(well_id)
    except exc.NoResultFound:
        flash(f'Скважины с id:{well_id} на проекте {project.name_ru} нет!')
        return redirect(url_for('.param_table', network_id=network_id))
    # Well exist... well keep checking
    for record in list_of_records[:]:
        if not well.check_record_tables(record):
            # If table are exist - they will save to dict well.tables like '{record}_idx' or '{record}_data'
            flash(f'Таблиц с данными для рекода: {record} '
                  f'- Не существует. Удаляем рекорд: {record} из списка: {list_of_records}')
            list_of_records.remove(record)

        mnem = set(well.check_data_in_record_table(record, start=limit_from, stop=limit_to))
        if mnem:
            flash(f'Ошибка. В таблице "{well.data_table_by_record(record)}" мнемоник {mnem} для рекорда "{record}" '
                  f'отсутствует в текущем [source_type_id: { well.source_type_id }, { well.source_type_name } ]')
            flash(f'Проверьте исходные данные! Вероятно была смена типа станции ГТИ!')
            return redirect(url_for('.param_table', network_id=network_id))
    # List is empty?
    if not list_of_records:
        flash(f'Отсутствуют данные в скважние {well.name}\n'
              f'Проверьте скважину или список рекордов: {request.values.get("records", [1, 11, 12])}')
        return redirect(url_for('.param_table', network_id=network_id))
    # if all checks is clear do:
    return render_template('param_table/download_param_table.html', vars=locals())


@pt.route('/download', methods=['GET', 'POST'])
@pt.route('/download/<int:network_id>/<int:well_id>')
def download(network_id=None, well_id=None):
    __title__ = 'Download param table'

    if request.method == 'GET':
        well_id = well_id or request.values.get('well_id')
        network_id = network_id or request.values.get('network_id')
        return redirect(url_for('.upload', network_id=network_id, file_name=well_id))
    elif request.method == 'POST':
        # todo Вынести выполнение функции в отдельный тред
        # todo Отлавливать остановки, выводить причины
        network_id = network_id or request.values.get('network_id')
        project = Project.query.filter(Project.network_id == network_id).one()
        well_id = request.values.get('well_id')
        list_of_records = scr.return_list_from_str(request.values.get('list_of_records'))
        limit_from = request.values.get('limit_from')
        limit_to = request.values.get('limit_to')
        table = scr.TableCreator(project.sqlsession, well_id, list_of_records, limit_from, limit_to)
        # Создаём таблицы
        table.create_tables()
        scr.excel_writer(
            path_to_file=app.config['PARAM_TABLE_DIR_PATH'],
            well_id=well_id,
            common_tables=table.tables['common_tables'],
            data_tables=table.tables['data_tables'],
            network_id=network_id
        )

        done = True
        if scr.check_file_exists(network_id, well_id, app.config['PARAM_TABLE_DIR_PATH']):
            file = True

        return render_template('param_table/download_param_table.html', vars=locals())
    else:
        flash('UNEXCEPTIONAL ERROR')
        return abort(404)


@pt.route('/upload/<path:network_id>/<path:file_name>')
def upload(network_id, file_name):
    file_path = app.config['PARAM_TABLE_DIR_PATH']
    file_path = Path(file_path).joinpath(f'{network_id}')
    if file_path.exists():
        well = Project.get(network_id).get_well_by_id(file_name)
        file_name = f'{file_name}.xlsx'
        attachment_filename = f'{well.name.replace(" ", "_")}.xlsx'.encode('utf-8')
        return send_from_directory(file_path, file_name,
                                   as_attachment=True,
                                   mimetype='text/xlsx; charset=utf-8',
                                   attachment_filename=attachment_filename)

    else:
        flash(f'Файла отчёта {file_name} нет, создайте фаил.')
        return redirect(redirect_url('.param_table'))
