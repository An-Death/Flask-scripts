from flask import Blueprint, render_template

from models.models import Project
from scripts.speed_test.speed_test import speedTest

st = Blueprint('speed_test', __name__, url_prefix='/scripts/speed_test')


@st.route('/')
@st.route('/<int:network_id>')
@st.route('/<int:network_id>/<string:gbox>')
def speed_test(network_id=None, gbox=None):
    from views import app
    __title__ = 'Speed Test'
    if network_id and not gbox:
        project = Project.get(network_id)
        wells = project.get_active_wells()
    elif network_id and gbox:
        project = Project.get(network_id)
        server_host = project.connection_info.send_to_address
        server_port = project.connection_info.port
        server_login = project.connection_info.login
        server_password = project.connection_info.password
        gbox = map(str.lower, gbox.split('-')[:2])
        test = speedTest(server_host, server_port, server_login, server_password,
                         '-'.join(gbox), 22, 'login', 'password', ailoop=app.loop, timeout=120, verbose=True)
        df = test().to_html()
    else:
        projects = Project.all_supported()
    return render_template('speed_test/speed_test.html', vars=locals())
