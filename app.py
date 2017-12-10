import os

from flask import Flask
from flask_cache import Cache
from flask_sqlalchemy import SQLAlchemy
from werkzeug.routing import BaseConverter

from config import Ops, Dev, Dev_offline

app = Flask(__name__)
if os.environ.get('SUPPORT_SCRIPTS_EXEC') == "Dev":
    app.secret_key = Dev.SECRET_KEY
    app.config.from_object(Dev)
elif os.environ.get('SUPPORT_SCRIPTS_EXEC') == "Dev_offline":
    app.config.from_object(Dev_offline)
else:
    app.secret_key = Ops.SECRET_KEY
    app.config.from_object(Ops)


if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(app.config['LOG_FILE'], 'a', 1 * 1024 ** 3, 3)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.info('support_scripts started')

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

db = SQLAlchemy(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter
