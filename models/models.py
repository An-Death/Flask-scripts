from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app import db


class Meta(db.Model):
    __abstract__ = True
    __tablename__ = None

    def __repr__(self):
        return ('<{}({})>'.format(self.__tablename__, ','.join(
            str(atr) for _, atr in self.__class__.__dict__.items() if not _.startswith('_'))))


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
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    network_id = db.Column(db.Integer, nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey(Server.id))
    supported = db.Column(db.Boolean, default=False)
    name_ru = db.Column(db.String(200), nullable=True)
    name_en = db.Column(db.String(200), nullable=True)

    server = db.relationship('Server', backref=db.backref("projects"))


    def __str__(self):
        prj = [
            ' Project {} '.format(self.name_ru).center(70, '-'),
            'Main INFO:',
            'host: {},  host2: {}, port: {}'.format(self.server.host, self.server.host2, self.server.port),
            'VPN: {}, DNS: {}'.format(self.server.vpn, self.server.dns),
            'Monitoring INFO:',
            'URL: {}, URL2: {}'.format(self.server.url, self.server.url2),
            #  monitoring login, pass
            'Send_to_Address: {}, Send_to_Port: {}'.format(self.server.send_to_address, self.server.send_to_port),
            'SSH INFO:',
            'Ssh_user: {}, Ssh_pass: {}'.format(self.server.login, self.server.password),
            'Connection: "{}"'.format('sshpass -p {} ssh -o StrictHostKeyChecking=no {}@{} -p{}'.
                                      format(self.server.password,
                                             self.server.login,
                                             self.server.host,
                                             self.server.port)),
            'Path_to_stream: {}'.format(self.server.stream_path),
            'Path_to_reporting: {}'.format(self.server.report_path),
            'SQL INFO:',
            'Login: {}, Pass: {}, Base_name: {}, Port: {}, Gate: {}'.format(
                self.server.db_login,
                self.server.db_password,
                self.server.db_name,
                self.server.db_port,
                self.server.db_host
            ),
            'SQL_Connection: "{}"'.format(
                'mysql --default-character-set=utf8 --safe-updates -h {} -P {} -u{} -p{} {} -A'.
                    format(
                    self.sever.db_host,
                    self.server.db_port,
                    self.server.db_login,
                    self.server.db_password,
                    self.server.db_name
                ))
        ]
        return '\n'.join(prj)

    def __repr__(self):
        return '<{}({})'.format(self.name,
                                ','.join([self.server.host, self.server.port, self.server.login, self.server.password]))

    def _sql_engine(self, loging=True):
        """
        Создаём движок для подключения к базе на основе движка sqlalchemy
        :return: engine
        """

        engine_str = 'mysql+pymysql://{u}:{p}@{h}{port}/{b_name}?charset=utf8&use_unicode=1'.format(
            u=self.server.user,
            p=self.server.password,
            h=self.server.host,
            port='' if self.server.port is None or '' else ':' + str(self.server.port),
            b_name=self.server.bname
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
    def sqlsession(self):
        if not hasattr(self, 'session'):
            self.session = scoped_session(sessionmaker(autocommit=False,
                                                       autoflush=False,
                                                       bind=self._sql_engine()))
        return self.session

    def get_active_wells(self):
        from .wits_models import Base
        from .wits_models import Wits_well as Well
        Base.query = self.sqlsession.query_property()

        return Well.query.filter(Well.source.network_id == self.network_id). \
            filter(Well.id > 0).filter(Well.property.status_id == 3).order_by(Well.property.group.id)

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

    server = db.relationship('Server', backref=db.backref('connection_info'))


    def __str__(self):
        return self.server


class Project_info(Meta):
    __tablename__ = 'project_info'

    prj_id = db.Column(db.Integer, db.ForeignKey(Project.id), primary_key=True)
    # image = models.ImageField()
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(200), nullable=True)
    address = db.Column(db.String(500), nullable=True)

    project = db.relationship('Project', backref=db.backref('info'))


    def __str__(self):
        return self.prj
