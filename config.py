import os
import database


class Configuration:
    # add global config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    basedir = os.path.abspath(os.path.dirname(__file__))


class Dev(Configuration):
    DEBUG = True
    SECRET_KEY = 'some_simple_key'
    SQLALCHEMY_DATABASE_URI = database.Dev.SQLALCHEMY_DATABASE_URI
    PARAM_TABLE_DIR_PATH = '/home/as/share/tables/param_table'
    USER_ACTIVITY_DIR_PATH = '/home/as/share/tables/activity_table'
    LOG_FILE = './support_scripts.log'


class Ops(Configuration):
    DEBUG = False
    SECRET_KEY = database.Ops.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = database.Ops.SQLALCHEMY_DATABASE_URI
    PARAM_TABLE_DIR_PATH = '/share/param_table'
    USER_ACTIVITY_DIR_PATH = '/share/activity_table'
    LOG_FILE = 'support_scripts.log'


class Dev_offline(Configuration):
    DEBUG = True
    SECRET_KEY = 'some_simple_key'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(Configuration.basedir, 'database.sqlite')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(Configuration.basedir, 'db_repository')
