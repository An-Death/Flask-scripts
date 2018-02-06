from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app import db
from .wits_models import Base
from .wits_models import Wits_well as well, Wits_source as source, Wits_well_prop as prop


class Meta(db.Model):
    __abstract__ = True
    __tablename__ = None

    def __repr__(self):
        return ('<{}({})>'.format(self.__tablename__, ', '.join(
            _ + ': ' + str(atr) for _, atr in self.__dict__.items() if not _.startswith('_'))))


class Server(Meta):
    __tablename__ = 'server'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    shortcuts = db.Column(db.String(200), nullable=True)

    # Для создания записи сервера
    # def __init__(self, id=None, name=None, shortcuts=None):

    def __str__(self):
        return self.name

    @property
    def shortcut(self):
        short = self.shortcuts.split(',')
        short.sort(key=len)
        return short[-1].strip()


class Project(Meta):
    # todo Написать хелп по использованию класса и объекта с описанием методов
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    network_id = db.Column(db.Integer, nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey(Server.id))
    supported = db.Column(db.Boolean, default=False)
    name_ru = db.Column(db.String(200), nullable=True)
    name_en = db.Column(db.String(200), nullable=True)
    gbox_connection_info = db.Column(db.Integer)

    server = db.relationship('Server', backref=db.backref("projects"))

    def _sql_engine(self, loging=True):
        """
        Создаём движок для подключения к базе на основе движка sqlalchemy
        :return: engine
        """

        engine_str = 'mysql+pymysql://{u}:{p}@{h}{port}/{b_name}?charset=utf8&use_unicode=1'.format(
            u=self.server.connection_info.db_login,
            p=self.server.connection_info.db_password,
            h=self.server.connection_info.db_host,
            port='' if self.server.connection_info.db_port is None or '' else ':' + str(
                self.server.connection_info.db_port),
            b_name=self.server.connection_info.db_name
        )
        self.engine = create_engine(engine_str, convert_unicode=True, echo=loging)
        return self.engine

    def get_shortcuts(self, echo=True):
        """
        Выводим список возможных сокращений для проекта.
        :param echo: По умолчанию True - принтим список. False - Возвращаем list
        :return:
        """
        if echo:
            print('Project: {} Shortcuts: {}'.format(self.name, ', '.join(self.server.shortcuts)))
        else:
            return self.shortcuts

    @property
    def name(self):
        return self.name_ru

    @property
    def connection_info(self):
        return self.server.connection_info

    @property
    def sqlsession(self):
        if not hasattr(self, 'session'):
            self.session = scoped_session(sessionmaker(autocommit=False,
                                                       autoflush=False,
                                                       bind=self._sql_engine()))
        return self.session

    @property
    def shortcut(self):
        return self.server.shortcut

    @property
    def uri_monitoring(self):
        server = self.server
        return server.connection_info.url

    @classmethod
    def get(cls, network_id):
        return cls.query.get_or_404(network_id)

    @classmethod
    def all_supported(cls):
        return cls.query.filter_by(supported=True).all()

    def get_active_wells(self):
        Base.query = self.sqlsession.query_property()

        return well.query.join(source).join(prop).filter(source.network_id == self.network_id). \
            filter(well.id > 0).filter(prop.status_id == 3).order_by(prop.group_id.desc(), well.id).all()

    def get_well_by_id(self, well_id):
        Base.query = self.sqlsession.query_property()
        return well.query.get(well_id)


class Server_connection_info(Meta):
    __tablename__ = 'server_connection_info'

    server_id = db.Column(db.Integer, db.ForeignKey(Server.id), primary_key=True)
    host = db.Column(db.String(200))
    host2 = db.Column(db.String(200), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    vpn = db.Column(db.CHAR(39), nullable=True)
    dns = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(200), nullable=True)
    url2 = db.Column(db.String(200), nullable=True)
    send_to_address = db.Column(db.CHAR(39))
    send_to_port = db.Column(db.SmallInteger, nullable=True)
    login = db.Column(db.String(200))
    password = db.Column(db.String(200))
    stream_path = db.Column(db.String(200), nullable=True)
    report_path = db.Column(nullable=True)
    db_login = db.Column(db.String(200), nullable=True)
    db_password = db.Column(db.String(200), nullable=True)
    db_port = db.Column(nullable=True)
    db_name = db.Column(db.String(200), nullable=True)
    db_host = db.Column(db.CHAR(39), nullable=True)
    encryptPK = db.Column(db.String(200), nullable=True)
    encryptLK = db.Column(db.String(200), nullable=True)

    server = db.relationship('Server', backref=db.backref('connection_info', uselist=False))

    def __str__(self):
        return self.server


class Project_info(Meta):
    __tablename__ = 'project_info'

    prj_id = db.Column(db.Integer, db.ForeignKey(Project.id), primary_key=True)
    # image = models.ImageField()
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(200), nullable=True)
    address = db.Column(db.String(500), nullable=True)

    project = db.relationship('Project', backref=db.backref('info', uselist=False))

    def __str__(self):
        return self.prj


class Gbox_connection_info(Meta):
    __tablename__ = 'gbox_connection_info'

    id = db.Column(db.Integer, db.ForeignKey(Project.gbox_connection_info), primary_key=True)
    default_login = db.Column(db.String(200))
    default_password = db.Column(db.String(200))
    default_port = db.Column(db.Integer, default=22)

    projects = db.relationship('Project', backref=db.backref('gbox', uselist=False))
