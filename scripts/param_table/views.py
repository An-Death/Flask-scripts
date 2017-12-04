from pathlib import Path

from flask import Blueprint, request, render_template, send_file, url_for, redirect, flash
from sqlalchemy.exc import OperationalError

from models.models import *
from scripts.param_table import scr
from scripts.param_table.scr import DateLimit

pt = Blueprint('param_table', __name__, url_prefix='/scripts/param_table')


@pt.route('/<regex("[0-9]+|''"):network_id>', methods=['GET', 'POST'])
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.query.filter(Project.supported == 1).all()
    # GET:
    # if 'well_id' not in request.values:
    if request.method == 'GET':
        if not network_id:
            # Return list of {projects}
            return render_template('param_table/param_table.html', vars=locals())
        else:
            # Get project from list by network_id
            project = [project for project in projects if project.network_id == network_id][0]
            # project = Project.query.filter(Project.network_id == network_id).one()
            try:
                # Getting active wells from current project
                wells = project.get_active_wells()
            except OperationalError:
                flash(f'База данных проекта {project.name_ru} недоступна!')
                return redirect(url_for('.param_table', network_id=''))
            finally:
                return render_template('param_table/param_table.html', vars=locals())
    else:  # POST:
        project = [project for project in projects if project.network_id == network_id][0]
        # Get data from POST request
        well_id = request.values.get('well_id')
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
        # Are well does exist?
        if not well :
            flash(f'Скважины с id:{well_id} на проекте {project.name_ru} нет!')
            return redirect(url_for('.param_table', network_id=network_id))
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
        # todo sa.Table haven't query method!!!
        # for r, tables in record_tables.items():
        #     idx = tables['idx']
        #     data = tables['data']
        #     # todo sqla.Table have not method query. how i can add it?
        #     q = idx.query.join(data, idx.id == data.idx_id).filer(idx.date > limit_from).filter(idx.date < limit_to)
        #     if q.count() < 0:
        #         flash(f'Отсутствуют данные в таблицах: {idx} || {data}... '
        #               f'Удаляем рекорд: {r} из списка: {list_of_records}')
        #         list_of_records.remove(r)
        if not list_of_records:
            flash(f'Отсутствуют данные в скважние {well.name} \n'
                  f'Проверьте скважину или список рекордов: {request.values.get("records", [1, 11, 12])}')
            return redirect(url_for('.param_table', network_id=network_id))
        well_name = well.name or well.alias
        shortcut = project.shortcut
        return redirect(url_for('param_table.download_param_table', shortcut=shortcut, well_name=well_name))
        # return redirect(url_for('param_table.download_param_table', network_id=network_id, well_id=well_name))


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
