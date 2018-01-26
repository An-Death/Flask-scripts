from flask import Blueprint, render_template, flash, redirect, url_for, request

from models.models import Project
from scripts.speed_test.speed_test import speedTest

st = Blueprint('speed_test', __name__, url_prefix='/scripts/speed_test')


@st.route('/')
@st.route('/<int:network_id>')
@st.route('/<int:network_id>/<int:well_id>', methods=['GET'])
def speed_test(network_id=None, well_id=None):
    __title__ = 'Speed Test'
    if not network_id:
        return redirect(url_for('scripts'))
    elif not well_id:
        project = Project.get(network_id)
        wells = project.get_active_wells()
    elif not request.args.get('gbox_addr'):
        project = Project.get(network_id)
        well = project.get_well_by_id(well_id)
        gbox = well.gbox
    # elif well_id and gbox_addr:
    else:
        from views import app
        project = Project.get(network_id)
        wells = project.get_active_wells()
        gbox = request.args.get('gbox_addr')
        timeout = request.args.get('timeout')
        server_host = project.connection_info.send_to_address
        server_port = project.connection_info.port
        server_login = project.connection_info.login
        server_password = project.connection_info.password
        try:
            test = speedTest(server_host, server_port, server_login, server_password,
                             gbox, 22, project.gbox.default_login, project.gbox.default_password,
                             ailoop=app.loop, timeout=120, verbose=True)
        except Exception as e:
            flash(e, category='Error')
            return render_template('speed_test/speed_test.html', vars=locals())
        df, _ = test()
        if not _:
            df = df.to_html()
            test.close()
        else:
            del df
            flash(_, category='Error')
    # else:
    #     projects = Project.all_supported()
    return render_template('speed_test/speed_test.html', vars=locals())