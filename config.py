import database


class Configuration:
    # add global config
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Dev(Configuration):
    DEBUG = True
    SECRET_KEY = 'some_simple_key'
    SQLALCHEMY_DATABASE_URI = database.Dev.SQLALCHEMY_DATABASE_URI
    PARAM_TABLE_DIR_PATH = '~/share/tables/param_table'
    USER_ACTIVITY_DIR_PATH = '~/share/tables/activity_table'

class Ops(Configuration):
    DEBUG = False
    SECRET_KEY = database.Ops.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = database.Ops.SQLALCHEMY_DATABASE_URI
    PARAM_TABLE_DIR_PATH = '/share/param_table'
    USER_ACTIVITY_DIR_PATH = '/share/activity_table'