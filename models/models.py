from sqlalchemy import Boolean, CHAR, SmallInteger
from sqlalchemy import Column
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from config import Base


class Meta:
    __tablename__ = None

    def __repr__(self):
        return ('<{}({})>'.format(self.__tablename__, ','.join(
            str(atr) for _, atr in self.__class__.__dict__.items() if not _.startswith('_'))))


class Server(Base, Meta):
    __tablename__ = 'server'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)
    shortcuts = Column(String(200), nullable=True)

    # Для создания записи сервера
    # def __init__(self, id=None, name=None, shortcuts=None):

    def __str__(self):
        return self.name

    @property
    def shortcut(self):
        short = self.shortcuts.split(',')
        short.sort(key=len)
        return short[-1].strip()


class Project(Base, Meta):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True, autoincrement=True)
    network_id = Column(Integer, nullable=False)
    server_id = Column(Integer, ForeignKey(Server.id))
    supported = Column(Boolean, default=False)
    name_ru = Column(String(200), nullable=True)
    name_en = Column(String(200), nullable=True)

    server = relationship('Server', backref="projects")

    def __str__(self):
        return self.name_ru

        # def return_supported(self):
        #     return self.name_ru if self.supported == 1 else None


class Server_connection_info(Base, Meta):
    __tablename__ = 'server_connection_info'

    server_id = Column(Integer, ForeignKey(Server.id), primary_key=True)
    host = Column(String(200))
    host2 = Column(String(200), nullable=True)
    port = Column(Integer, nullable=True)
    vpn = Column(CHAR(39), nullable=True)
    dns = Column(String(200), nullable=True)
    url = Column(String(200), nullable=True)
    url2 = Column(String(200), nullable=True)
    send_to_address = Column(CHAR(39))
    send_to_port = Column(SmallInteger, nullable=True)
    login = Column(String(200))
    password = Column(String(200))
    stream_path = Column(String(200), nullable=True)
    report_path = Column(nullable=True)
    db_login = Column(String(200), nullable=True)
    db_password = Column(String(200), nullable=True)
    db_port = Column(nullable=True)
    db_name = Column(String(200), nullable=True)
    db_host = Column(CHAR(39), nullable=True)
    encryptPK = Column(String(200), nullable=True)
    encryptLK = Column(String(200), nullable=True)

    server = relationship('Server', backref='connection_info')

    def __str__(self):
        return self.server


class Project_info(Base, Meta):
    __tablename__ = 'project_info'

    prj_id = Column(Integer, ForeignKey(Project.id), primary_key=True)
    # image = models.ImageField()
    email = Column(String(200), nullable=True)
    phone = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)

    project = relationship('Project', backref='info')

    def __str__(self):
        return self.prj
