import datetime
from pathlib import Path

from flask import Blueprint, request, render_template, send_file, url_for, redirect, flash, g
from sqlalchemy.exc import OperationalError

from models.models import *
from .forms import ParamTableForm
from scripts.param_table import scr

pt = Blueprint('param_table', __name__, url_prefix='/scripts/param_table')

class DateLimit:
    def __init__(self, val=2, limit='days'):
        if limit == 'weeks':
            self._val = val*7
        else:
            self._val = val
        self._date_to = datetime.datetime.now()
        self._date_from = self._date_to - datetime.timedelta(days=self._val)

    @property
    def end(self):
        return self._date_to
    @property
    def begin(self):
        return self._date_from


@pt.route('/<regex("[0-9]+|''"):network_id>', methods=['GET', 'POST'])
def param_table(network_id=None):
    __title__ = 'Param Table'
    projects = Project.query.filter(Project.supported == 1).all()

    if 'well_id' not in request.values:
        if not network_id:
            return render_template('param_table/param_table.html', vars=locals())
        else:
            project = Project.query.filter(Project.network_id == network_id).one()
            try:
                wells = project.get_active_wells()
            except OperationalError:
                flash(f'База данных проекта {project.name_ru} недоступна!')
                return redirect(url_for('.param_table', network_id=''))
            return render_template('param_table/param_table.html', vars=locals())
    else:
        # prj_name = request.values.get('project_name')
        # prj = [prj for prj in projects if prj.name_ru == prj_name]
        # server = prj[0].server
        # shortcuts = server.shortcuts
        # short = shortcuts.split(',')[0]
        # network_id = form.project.data
        # well_name = form.well.data
        # list_of_records = form.records.data
        # limit_selector = form.limit_selector.data
        # # todo Написать условия для limit_selector
        project = Project.query.filter(Project.network_id == network_id).one()
        well_id = request.values.get('well_id')
        list_of_records = request.values.get('records', [1, 11, 12])
        limit = request.values.get('limit', 'weeks')
        limit_value = request.values.get('limit_value', 2)
        dt = DateLimit(limit_value, limit)
        limit_from = request.values.get('limit_from', dt.begin)
        limit_to = request.values.get('limit_to', dt.end)
        well = project.get_well_by_id(well_id)
        record_tables = {}
        if not well :
            flash(f'Скважины с id:{well_id} на проекте {project.name_ru} нет!')
            return redirect(url_for('.param_table', network_id=network_id))
        for record in list_of_records[:]:
            tables = well.check_record_tables(record)
            if tables is None:
                flash(f'Таблиц с данными для рекода: {record} '
                      f'- Не существует. Удаляем рекорд: {record} из списка: {list_of_records}')
                list_of_records.remove(record)
            else:
                record_tables[record] = tables
        if not list_of_records:
            flash(f'Отсутствуют данные в скважние {well.name} '
                  f'по заданным рекордам {request.values.get("records", [1, 11, 12])} ')
            return redirect(url_for('.param_table', network_id=network_id))
        for r, tables in record_tables.items():
            idx = tables['idx']
            data = tables['data']
            q = idx.query.join(data, idx.id == data.idx_id).filer(idx.date > limit_from).filter(idx.date < limit_to)
            if q.count() < 0:
                flash(f'Отсутствуют данные в таблицах: {idx} || {data}... '
                      f'Удаляем рекорд: {r} из списка: {list_of_records}')
                list_of_records.pop(r)
        if not list_of_records:
            flash(f'Отсутствуют данные в скважние {well.name} '
                  f'по заданным рекордам {request.values.get("records", [1, 11, 12])} ')
            return redirect(url_for('.param_table', network_id=network_id))
        # list_records = request.values.get('records', '1,11,12').split(',')
        return redirect(url_for('param_table.download_param_table', network_id=network_id, well_id=well_id))


@pt.route('/download_param_table/<network_id>/<well_id>', methods=['GET', 'POST'])
def download_param_table(network_id=None, well_id=None):
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
