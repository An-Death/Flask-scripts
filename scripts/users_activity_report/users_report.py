import pandas as pd
from sqlalchemy.sql import func

from models.wits_models import Wits_user as users, Wits_user_group as group

aliases = {
    0: '№п/п',
    1: 'ФИО полностью',
    2: 'Наименование предприятия/филиала/экспедиции',
    3: 'Отдел/служба',
    4: 'Должность',
    5: 'Email',
    6: 'Логин в системе (совпадает с доменным именем)',
    7: 'Примечание'
}
BKE_comr = {
    'GPN_Development': '',
    'RTM_KF': '',
    'RTM_MSK': '',
    'RTM_NVBN': '',
    'RTM_PKH': '',
    'RTM_USK': '',
    'RTM_VIP': '',
    'RTM_ZSF': '',
    'RTM_ZSF+KF': ''
}


def get_table(con):
    query = con.query(func.CONCAT_WS(' ', users.last_name, users.first_name, users.patr_name).label('1'),
                      group.name.label('2'),
                      users.organization.label('3'),
                      users.position.label('4'),
                      users.email.label('5'),
                      users.name.label('6'),
                      users.tel.label('7'),
                      ).outerjoin(group, users.group_id == group.id)
    query = query.filter(users.removed == 0)
    query = query.order_by(group.name, users.id)
    query_as_string = query.statement.compile(compile_kwargs={"literal_binds": True},
                                              dialect=query.session.bind.dialect)
    table = pd.read_sql_query(query_as_string, con.connection())
    table.columns = list(aliases.values())[1:]
    return table


if __name__ == '__main__':
    pass
