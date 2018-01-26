import datetime
import re
from pathlib import Path

import pandas as pd
from xlsxwriter.utility import xl_range, xl_col_to_name

from models.classes import Dt
from models.wits_models import *

TEST = False
RECORDS_COMPREHENSION = {
    'record_1': 'Основные временные',
    'record_11': 'Состояние емкостей',
    'record_12': 'Данные хромотографа'
}


def return_list_from_str(stri):
    if isinstance(stri, list):
        return stri
    elif isinstance(stri, str):
        return sorted(list(map(int, re.findall(r'\d+', stri))))
    else:
        raise ValueError(f'arg {stri} should be str or list. Get {type(stri)}')


def check_file_exists(network_id, well_id, path_to_file):
    file_name = f'{well_id}.xlsx'
    file_path = Path(path_to_file).joinpath(f'{network_id}').joinpath(file_name)
    return file_path.is_file()

class DateLimit:
    def __init__(self, val=2, limit='days'):
        if limit == 'weeks':
            self._val = int(val) * 7
        else:
            self._val = int(val)
        self._date_to = datetime.datetime.now()
        self._date_from = self._date_to - datetime.timedelta(days=self._val)

    @property
    def end(self):
        return self._date_to

    @property
    def begin(self):
        return self._date_from


class TableCreator:
    # todo сделать асинхронным
    # todo сделать перевод значений из кПа в атм

    def __init__(self, session, well_id, list_of_records, start, stop):
        self.session = session
        self.well_id = well_id
        self.list_of_records = list_of_records
        self.start = Dt(start)
        self.stop = Dt(stop)
        self.tables = {}
        self.well = Wits_well.get(well_id, session)

        self.actc = self.get_actc()

    @property
    def connect(self):
        return self.session().connection()

    def get_actc(self):
        actc_table = pd.read_sql_query(Wits_activity_type.as_string(self.session), self.connect)
        actc_table.id = actc_table.id.apply(float)
        return actc_table

    def get_param_table(self, record_id):
        param_table = pd.read_sql_query(self.well.get_param_table(record_id, as_string=True), self.connect)
        # Заменяем спецсимволы из базы
        for i in (('3', '&#179;'), ('2', '&#178;')):
            param_table.unit = param_table.unit.str.replace(i[1], i[0])
        return param_table

    def get_data_tables(self, record_id):
        # todo Переработать запросы и обсчитывать макс значения для каждого параметра для кажого ACTC на стороне базы
        # tables = self.well.create_record_tables(record_id)
        sql_query_idx = f'select id, ' \
                        f'FROM_UNIXTIME(' \
                        f'UNIX_TIMESTAMP(' \
                        f'CONVERT_TZ(' \
                        f'date, "+00:00", ' \
                        f'(select logs_offset from WITS_WELL where wellbore_id={self.well.wellbore_id}))) ' \
                        f'- ' \
                        f'(select timeshift from WITS_WELL where wellbore_id={self.well.wellbore_id})) as date,' \
                        f'depth ' \
                        f'from WITS_RECORD{record_id}_IDX_{self.well.wellbore_id} ' \
                        f'where date between "{self.start.to_string()}" and "{self.stop.to_string()}" '

        sql_query_idx_old = f'select id,date,depth from WITS_RECORD{record_id}_IDX_{self.well.wellbore_id} where ' \
                            f'date between "{self.start.to_string()}" and "{self.stop.to_string()}"'
        sql_query_data = f'select idx_id as id, mnemonic, value from ' \
                         f'WITS_RECORD{record_id}_DATA_{self.well.wellbore_id} ' \
                         f'where idx_id in ({sql_query_idx_old.replace(",date,depth", "")})'
        #
        # Получение данных
        idx_table = pd.read_sql_query(sql_query_idx, self.connect, index_col='id', parse_dates=['date'])

        data_table = pd.read_sql_query(sql_query_data, self.connect)
        # Разворачиваем таблицу, делая колонками мнемоники
        data_table = data_table.pivot(index='id', columns='mnemonic', values='value')
        # data_table.
        # Мержим с индексой таблицей. Добовляем к каждому значению дату и глубину
        merget_table = idx_table.merge(data_table, left_index=True, right_index=True)

        return merget_table

    def get_big_table(self, record_id):
        data_dict = {}
        table = self.get_data_tables(record_id)
        table.fillna(0, inplace=True)
        table.ACTC = table.ACTC.replace(self.actc.set_index('id').to_dict().get('name_ru'))

        for column in table:
            if column in ['depth', 'date', 'ACTC', 'ACTC2', 'DBTM', 'DRTM', 'DMEA']:
                continue
            # Создаём словарь из таблиц с min/max данными по каждому мнемонику, за исключением вышеописанных
            data_dict[column] = pd.merge(
                table.loc[table.groupby("ACTC")[column].idxmin()][['ACTC', 'date', column]].rename(
                    columns={column: 'min', 'date': 'date_min'}),
                table.loc[table.groupby("ACTC")[column].idxmax()][['ACTC', 'date', column]].rename(
                    columns={column: 'max', 'date': 'date_max'}),
                on='ACTC',
                suffixes=('_min', '_max')).set_index('ACTC')

        datas = data_dict.values()
        list_datas = list(datas)
        big_table = pd.concat(list_datas, keys=data_dict.keys(), axis=1)
        big_table = big_table.unstack().unstack().unstack()
        return big_table

    def return_work_table(self, param_table, record_id):
        table = self.get_big_table(record_id)

        # ____-----debug-------------------------------------------------
        def repiter(table, param_table):
            ids_list = []
            for mnem in table.index:
                param = param_table[param_table['mnem'] == mnem]
                try:
                    ids = param.index
                    ids_list.append(int(ids.get_values()[0]))
                except Exception:
                    raise ValueError(f'Didn`t found mnemonic: {mnem} in param_table for record {record_id}')
            return ids_list

        table.index = repiter(table, param_table)
        # _--------------------------------------------------------------
        #  Преобазуем мнемоники в id и сортируем по id
        # table.index = [int(ids.get_values()[0]) for ids in
        #                [param_table[param_table['mnem'] == mnem].index for mnem in table.index]]
        # ________________________________________________________________
        table.sort_index(inplace=True)
        #  Отформатировали таблицу по параметрам
        #  Преобразовываем параметры в называния и юниты
        table.index = [' '.join([str(param_table['name'][ids]), str(param_table['unit'][ids])]) for ids in table.index]
        table.columns.rename(names='Код технологического этапа', level=0, inplace=True)
        table.index.name = 'Параметры'

        return table

    def create_tables(self):
        self.tables = {
            'actc_table': self.actc,
            'common_tables':
                {'record_' + str(k): self.get_param_table(record_id=k) for k in self.list_of_records}
        }
        # Выгружаем и формируем табилцы из таблиц с данными.
        self.tables['data_tables'] = {'record_' + str(k): self.return_work_table(
            param_table=self.tables['common_tables'].get('record_' + str(k)),
            record_id=k) for k in self.list_of_records}


def write_param_sheet(writer, common_tables_dict):
    sheet_name = 'Параметры'
    tables_count = len(common_tables_dict)
    full_param_table = pd.concat([common_tables_dict[key] for key in common_tables_dict],
                                 copy=False, axis=1,
                                 join_axes=[common_tables_dict['record_1'].index])
    full_param_table.to_excel(writer, sheet_name, index=False, header=['Мнем', 'Юнит', 'Параметр'] * tables_count
                              )
    sheet = writer.sheets[sheet_name]
    for i in range(2, len(full_param_table.columns), tables_count):
        sheet.set_column(':'.join([xl_col_to_name(i)] * 2), 28)


def write_data_tables(writer, data_tables, formats):
    #  todo Придумать как перенести время в комменты к данным
    for table_key in data_tables:
        sheet_name = RECORDS_COMPREHENSION[table_key]
        table = data_tables[table_key]
        # table.reset_index(inplace=True)
        table.to_excel(writer, sheet_name=sheet_name)

        last_row = len(table.index) + 2
        last_col = len(table.columns)
        sheet = writer.sheets[sheet_name]
        # for row in range(3, last_row, 2):
        #     sheet.set_column(':'.join([xl_range(row, 0 , row, last_col)]), cell_format=blue)
        sheet.set_column('A:A', 28)  # На индексные ячейки формат не применяется =(
        full_datas = []
        for col in range(1, last_col, 2):
            dates = ':'.join([xl_range(3, col, last_row, col)])
            datas = ':'.join([xl_range(3, col + 1, last_row, col + 1)])
            sheet.set_column(dates, 18, None, {'align': 'left'})
            full_datas.append(datas)
            # if datas:
            #     sheet.conditional_format(datas, {'type': '3_color_scale'})
            #     sheet.conditional_format(datas, {'type': 'cell',
            #                                      'criteria': '>',
            #                                      'value': '5000',
            #                                      'format': formats['red']})
            #     sheet.conditional_format(datas, {'type': 'cell',
            #                                      'criteria': '==',
            #                                      'value': '0',
            #                                      'format': formats['grey']})

        sheet.conditional_format(full_datas[0], {'type': 'cell',
                                                 'criteria': '>',
                                                 'value': '5000',
                                                 'format': formats['red'],
                                                 'multi_range': ' '.join(full_datas)})
        sheet.conditional_format(full_datas[0], {'type': 'cell',
                                                 'criteria': '==',
                                                 'value': '0',
                                                 'format': formats['grey'],
                                                 'multi_range': ' '.join(full_datas)})


def excel_writer(path_to_file: str, network_id: int, well_id: str, common_tables: dict, data_tables: dict):
    # Записываем в фаил и форматируем как надо, пока фаил открыт.
    file_name = well_id.replace(' ', '_') + '.xlsx'
    file_path = Path(path_to_file).joinpath(f'{network_id}')
    if not file_path.exists(): file_path.mkdir(exist_ok=True)
    file_name = file_path.joinpath(file_name)
    with pd.ExcelWriter(file_name.__str__(), engine='xlsxwriter', datetime_format='DD/MM/YY hh:mm:ss') as writer:
        book = writer.book
        #  Formats
        formats = {
            'red': book.add_format({'bg_color': '#FFC7CE',
                                    'font_color': '#9C0006'}),
            'grey': book.add_format({'font_color': '#91949a'}),
            'blue': book.add_format({'bg_color': '#eceff4'}),
            'date_format': book.add_format({'align': 'left'})
        }

        write_data_tables(writer, data_tables, formats)
        write_param_sheet(writer, common_tables)
