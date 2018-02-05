from sqlalchemy import BLOB, DECIMAL, Enum
from sqlalchemy import Integer, String, ForeignKey, Text, DateTime, Float, Boolean
from sqlalchemy import Table, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.functions import now, coalesce

Base = declarative_base()


class Meta(Base):
    __tablename__ = None
    __abstract__ = True

    def __repr__(self):
        return ('<{}({})>'.format(self.__tablename__, ','.join(
            _ + ':' + str(atr) for _, atr in self.__dict__.items() if not _.startswith('_'))))

    @classmethod
    def as_string(mcs, session):
        return mcs.query.statement.compile(compile_kwargs={"literal_binds": True}, dialect=session.bind.dialect)

    @classmethod
    def get(mcs, pk, session=None):
        if session:
            Base.query = session.query_property()
        return mcs.query.get(pk)


class Wits_network(Meta):
    __tablename__ = 'WITS_NETWORK'

    id = Column('id', Integer, primary_key=True, nullable=False,
                autoincrement=True)
    name_ru = Column('name_ru', String(64))
    name_en = Column('name_en', String(64))
    email = Column('email', String(32))
    phone = Column('phone', String(32))
    address = Column('address', String(128))
    logo = Column('logo', BLOB)


class Wits_user(Meta):
    __tablename__ = 'WITS_USER'

    id = Column('id', Integer, primary_key=True, nullable=False,
                autoincrement=True)
    network_id = Column('network_id', Integer, ForeignKey('WITS_NETWORK.id'))
    name = Column('name', String(255))
    password = Column('password', String(32))
    email = Column('email', String(255))
    witsml_user = Column('witsml_user', String(32))
    witsml_password = Column('witsml_password', String(32))
    group_id = Column('group_id', Integer, ForeignKey('WITS_USER_GROUP.id'))
    role = Column('role', Integer)
    session = Column('session', String(128))
    last_name = Column('last_name', String(32))
    first_name = Column('first_name', String(32))
    patr_name = Column('patr_name', String(32))
    lang = Column('lang', String(2))
    organization = Column('organization', String(255))
    position = Column('position', String(255))
    tel = Column('tel', String(32))
    removed = Column('removed', Integer)

    group = relationship('Wits_user_group', backref='users')
    network = relationship('Wits_network', backref='users')


class Wits_user_log(Meta):
    __tablename__ = 'WITS_USER_LOG'

    user_id = Column('user_id', Integer, ForeignKey('WITS_USER.id'), primary_key=True, autoincrement=True)
    event_id = Column('event_id', Integer, ForeignKey('WITS_USER_EVENT.id'))
    date = Column('date', Integer)
    wellbore_id = Column('wellbore_id', Integer)
    data = Column('data', Text)

    event = relationship('Wits_user_event', backref='user_events')
    user = relationship('Wits_user', backref='sessions')


class Wits_user_event(Meta):
    __tablename__ = 'WITS_USER_EVENT'

    id = Column('id', Integer, primary_key=True)
    name_ru = Column('name_ru', String(255))
    name_en = Column('name_en', String(255))


class Wits_user_group(Meta):
    __tablename__ = 'WITS_USER_GROUP'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    network_id = Column('network_id', Integer, ForeignKey('WITS_NETWORK.id'))
    name = Column('name', String(255))

    network = relationship('Wits_network', backref='user_groups')


class Wits_source(Meta):
    __tablename__ = 'WITS_SOURCE'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column('type_id', Integer, ForeignKey('WITS_SOURCE_TYPE.id'), nullable=False)
    network_id = Column('network_id', Integer, ForeignKey('WITS_NETWORK.id'), nullable=False)
    name = Column('name', String(255))
    service_network_id = Column('service_network_id', Integer)
    service_company = Column('service_company', String(255))
    product_key = Column('product_key', String(255))
    health_address = Column('health_address', String(255))
    health_auth = Column('health_auth', String(32))
    last_packet_id = Column('last_packet_id', Integer, nullable=False, default=-1)
    modified_date = Column('modified_date', DateTime, nullable=False, default=now())
    timezone = Column('timezone', String(6), nullable=False, default='+00:00')

    source_type = relationship('Wits_source_type', backref=backref('source', uselist=False))
    network = relationship('Wits_network', backref='boxes')


class Wits_source_type(Meta):
    __tablename__ = 'WITS_SOURCE_TYPE'

    id = Column('id', Integer, primary_key=True, nullable=False)
    name_en = Column('name_en', String(255), nullable=False)
    name_ru = Column('name_ru', String(255))
    producer = Column('producer', String(255))


class Wits_activity_type(Meta):
    __tablename__ = 'WITS_ACTIVITY_TYPE'

    id = Column('id', Float, primary_key=True, nullable=False)
    name_en = Column('name_en', String(32), nullable=False, default='Undefined Status')
    name_ru = Column('name_ru', String(32))
    descr_en = Column('descr_en', String(255), nullable=False, default='Anything not covered by other activity codes.')
    descr_ru = Column('descr_ru', String(255))
    chart_color = Column('chart_color', String(6))


class Wits_well(Meta):
    __tablename__ = 'WITS_WELL'
    # __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    wellbore_id = Column(Integer, ForeignKey('WITS_WELLBORE.id'))
    source_id = Column(Integer, ForeignKey('WITS_SOURCE.id'))
    created_date = Column(DateTime)
    modified_date = Column(DateTime)
    timeshift = Column(Integer)
    logs_offset = Column(String(6))
    timezone = Column(String(6))
    alias = Column(String(255))
    external_id = Column(String(39))

    source = relationship('Wits_source', backref=backref('wells'))
    wellbores = relationship('Wits_wellbore', backref=backref('well', uselist=False))

    @classmethod
    def checkwell(cls, ses, name: str):
        return bool(ses.query(cls.name).filter(cls.name == name).count())

    @property
    def source_type_id(self):
        return self.source.type_id

    @property
    def source_type_name(self):
        return ': '.join(('name_ru', self.source.source_type.name_ru))

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = self._sa_instance_state.session
        return self._session

    @property
    def record_tables(self):
        return {self.tables[i] for i in self.tables.keys() if isinstance(i, int)}

    @property
    def product_key(self):
        return self.source.product_key

    @property
    def gbox(self):
        return '-'.join(map(str.lower, self.product_key.split('-')[:2]))

    def idx_table_by_record(self, record: int):
        return self.tables[record]['idx']

    def data_table_by_record(self, record: int):
        return self.tables[record]['data']

    def _add_related_table(self, table_name, table, record=None):
        if not hasattr(self, 'tables'):
            self.tables = {}
        if record:
            if record not in self.tables:
                self.tables[record] = {}
            self.tables[record][table_name] = table
        self.tables[table_name] = table

    def create_record_tables(self, record):
        record_tables = {'idx': f'WITS_RECORD{record}_IDX_{self.wellbore_id}',
                         'data': f'WITS_RECORD{record}_DATA_{self.wellbore_id}'}
        mapper = TableMapper(engine=self.session.bind)
        tables = {k: mapper.return_mapped_table(table) for k, table in record_tables.items()}
        for k, v in tables.items():
            self._add_related_table(k, v, record=record)
        return tables

    def check_record_tables(self, record):
        tables = self.create_record_tables(record)
        return None if None in tables.values() else True

    def check_idx_in_record_table(self, record, start, stop):
        idx = self.idx_table_by_record(record)
        q = self.session.query(idx.c.id).filter(idx.c.date > start).filter(
            idx.c.date < stop)
        return bool(q.count())

    def check_data_in_record_table(self, record, start, stop):
        idx = self.idx_table_by_record(record)
        data = self.data_table_by_record(record)
        mnemonics = self.session.query(Wits_source_param.mnemonic).filter(Wits_source_param.record_id == record). \
            filter(Wits_source_param.source_type_id == self.source_type_id)
        # idx_q = self.session.query(idx.c.id).filter(idx.c.date > start).filter(idx.c.date < stop)
        # idx_q = idx_q.subquery('idx_q')
        q = self.session.query(data.c.mnemonic).join(idx, idx.c.id == data.c.idx_id)
        q = q.filter(idx.c.date > start).filter(idx.c.date < stop).group_by(data.c.mnemonic)
        # q = self.session.query(data.c.mnemonic).filter(data.c.idx_id.in_(idx_q)).group_by(data.c.mnemonic)
        q = q.filter(~data.c.mnemonic.in_(mnemonics))

        return q.all()

    def get_param_table(self, record_id, as_string=False):

        q = self.session.query(
            Wits_source_param.mnemonic.label('mnem'),
            coalesce(Wits_unit.name_ru, Wits_unit.name_en).label('unit'),
            Wits_param.name_ru.label('name')
        )
        q = q.outerjoin(Wits_param).outerjoin(Wits_unit)
        q = q.filter(Wits_source_param.source_type_id == self.source_type_id)
        q = q.filter(Wits_source_param.record_id == record_id)
        q = q.order_by(Wits_source_param.record_id, Wits_source_param.param_num)
        if as_string:
            return q.statement.compile(compile_kwargs={"literal_binds": True}, dialect=self.session.bind.dialect)
        else:
            return q.all()


class Wits_well_group(Meta):
    __tablename__ = 'WITS_WELL_GROUP'

    id = Column('id', Integer, primary_key=True, nullable=False)
    name = Column('name', String(255), nullable=False)
    network_id = Column('network_id', Integer, ForeignKey('WITS_NETWORK.id'))
    user_ud = Column('user_id', Integer, nullable=False)
    parent_ud = Column('parent_id', Integer)
    order_num = Column('order_num', Integer, nullable=False, default=0)

    network = relationship('Wits_network', backref='well_groups')


class Wits_well_prop(Meta):
    __tablename__ = 'WITS_WELL_PROP'

    well_id = Column(Integer, ForeignKey('WITS_WELL.id'), primary_key=True, nullable=False)
    area = Column(String(255))
    pad = Column(String(255))
    number = Column(String(64))
    longitude = Column(Float)
    latitude = Column(Float)
    type_id = Column(Integer, nullable=False, default=1)
    status_id = Column(Integer, nullable=False, default=3)
    purpose_id = Column(Integer, nullable=False, default=22)
    video_enabled = Column(Boolean, default=False)
    cameras_count = Column(Integer, nullable=False, default=0)
    gti_enabled = Column(Boolean, default=False)
    group_id = Column(Integer, ForeignKey('WITS_WELL_GROUP.id'))
    order_num = Column(Integer, nullable=False, default=0)
    name_full = Column(String(255))
    ground_elevation = Column(Float, nullable=False, default=0)
    evidence_address = Column(String(255))
    embedded_address = Column(String(255))
    cuttings_depth = Column(Float, nullable=False, default=0)
    mwd_enabled = Column(Integer, nullable=False, default=0)
    rig_contacts = Column(String(255))
    rig_crew_id = Column(Integer)
    rig_type_id = Column(Integer)
    air_temperature = Column(Float)
    opslog_autoimport_enabled = Column(Boolean, nullable=False, default=0)

    well = relationship('Wits_well', backref=backref('properties', uselist=False))
    group = relationship('Wits_well_group', backref='wells')


class Wits_wellbore(Meta):
    __tablename__ = 'WITS_WELLBORE'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    well_id = Column(Integer)
    packet_id_min = Column(Integer)
    packet_id_max = Column(Integer)
    created_date = Column(DateTime)
    modified_date = Column(DateTime)
    status_id = Column(Integer)
    purpose_id = Column(Integer)
    type_id = Column(Integer)
    source_type_id = Column(Integer, ForeignKey('WITS_SOURCE_TYPE.id'))
    plan_depth_unit = Column(Enum('m', 'ft'))
    plan_start_depth = Column(DECIMAL)
    plan_start_date = Column(DateTime)
    current_date = Column(DateTime)
    current_depth = Column(DECIMAL)
    bit_pos = Column(DECIMAL)
    activity_id = Column(Integer)

    source_type = relationship('Wits_source_type', backref='wellbores')


class Wits_source_param(Meta):
    __tablename__ = 'WITS_SOURCE_PARAM'

    source_type_id = Column('source_type_id', Integer, ForeignKey('WITS_SOURCE_TYPE.id'), primary_key=True,
                            nullable=False)
    record_id = Column('record_id', Integer, ForeignKey(''), primary_key=True, nullable=False)
    param_num = Column('param_num', Integer, primary_key=True, nullable=False)
    mnemonic = Column('mnemonic', String(25), ForeignKey('WITS_PARAM.mnemonic'), nullable=False)
    unit_id = Column('unit_id', Integer, ForeignKey('WITS_UNIT.id'))
    required = Column('required', Boolean, default=False)
    depth_curve = Column('depth_curve', String(25))


class Wits_param(Meta):
    __tablename__ = 'WITS_PARAM'

    mnemonic = Column('mnemonic', String(25), primary_key=True,
                      nullable=False)
    name_en = Column('name_en', String(255), nullable=False)
    name_ru = Column('name_ru', String(255))
    type = Column('type', String(1))
    unit_id = Column('unit_id', Integer, ForeignKey('WITS_UNIT.id'), nullable=False)
    value_min = Column('value_min', Float)
    value_max = Column('value_max', Float)

    param_source_info = relationship('Wits_source_param', backref=backref('param_info', uselist=False))


class Wits_unit(Meta):
    __tablename__ = 'WITS_UNIT'

    id = Column('id', Integer, primary_key=True, autoincrement=True, nullable=False)
    name_en = Column('name_en', String(25), nullable=False)
    name_ru = Column('name_ru', String(25))
    descr = Column('descr', String(255))
    format = Column('format', String(10), nullable=False, default='8.2')
    ratio = Column('ratio', Float)
    ratio_operation = Column('ratio_operation', String(1))
    alias = Column('alias', String(25))
    main_unit_id = Column('main_unit_id', Integer)  # todo make sa.Table for convert values
    default_ru = Column('default_ru', Integer)
    default_en = Column('default_en', Integer)


class Wits_record:
    pass


class TableMapper:
    def __init__(self, engine=None):
        self.engine = engine
        self.meta = Base.metadata
        self.meta.bind = engine

    def return_mapped_table(self, name=None):
        if not self.engine.dialect.has_table(self.engine, name):
            return None
        else:
            table = Table(name, self.meta, autoload=True)
        # insp = Inspector.from_engine(self.engine)
        return table
