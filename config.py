import database


class Configuration:
    # add global config
    pass


class Dev(Configuration):
    DEBUG = True
    SECRET_KEY = 'some_simple_key'
    SQLALCHEMY_DATABASE_URI = database.Dev.SQLALCHEMY_DATABASE_URI


class Ops(Configuration):
    DEBUG = False
    SECRET_KEY = database.Ops.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = database.Ops.SQLALCHEMY_DATABASE_URI
