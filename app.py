import os

###########################################
from config import Configuration
from flask import Flask
# need to install Flask-Login Flask-OdenID
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from werkzeug.routing import BaseConverter

# todo Переместить в config
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = Configuration.SECRET_KEY
app.config.from_object(Configuration)
db_session = Configuration.DB_SESSION
# db = SQLAlchemy(app) // todo Перепилить на этот класс
# Для аутентификации
lm = LoginManager()
lm.init(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))


####

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
