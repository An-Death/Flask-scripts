import socket
from contextlib import closing
from pathlib import Path

from lazy_property import LazyProperty as lazy_property
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from ssh_decorate import ssh_connect

from app import db
# from app import log
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

    @lazy_property
    def shortcut(self):
        return self.shortcuts.split(',').sort(key=len).pop().strip() or ''

    @lazy_property
    def host(self):
        return self.connection_info.ssh


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

    @lazy_property
    def name(self):
        return self.name_ru

    @lazy_property
    def connection_info(self):
        return self.server.connection_info

    @lazy_property
    def sqlsession(self):
        return scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self._sql_engine())
        )

    @lazy_property
    def shortcut(self):
        return self.server.shortcut

    @lazy_property
    def uri_monitoring(self):
        return self.server.connection_info.url

    @lazy_property
    def SSHClient(self):
        return ssh_connect(**self.server.host, verbose=True)

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

    def speed_test_server_status(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((self.server.host['server'], 3333)) == 0:
                return True

    def run_speed_test_server(self):
        from app import app
        if not self.speed_test_server_status():
            serv = Path(app.root_path).joinpath('scripts/speed_test/async_server.py')
            remote = Path('/tmp').joinpath(serv.name).as_posix()
            command = 'nohup python3 {} --start >/tmp/async_server.out & sleep 3'.format(remote)
            self.SSHClient.put_file(local_path=serv,
                                    remote_path=remote)
            # log.info(f'send command {command} on server {self.server.shortcut}')
            print(command)
            self.SSHClient.exec_cmd(command)

    def stop_speed_test_server(self):
        if self.speed_test_server_status():
            remote = Path('/tmp').joinpath('async_server.py')
            self.SSHClient.exec_cmd('python3 {} --stop'.format(remote.as_posix()))

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

    @lazy_property
    def ssh(self):
        return dict(server=self.host, port=self.port, user=self.login, password=self.password)

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
