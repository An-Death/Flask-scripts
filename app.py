from flask import Flask
from werkzeug.routing import BaseConverter
from flask_sqlalchemy import SQLAlchemy
from database import db_session

from config import Configuration

app = Flask(__name__)
app.secret_key = Configuration.SECRET_KEY
app.config.from_object(Configuration)
# db = SQLAlchemy(app) // todo Перепилить на этот класс

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
