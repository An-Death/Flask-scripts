import pandas as pd
from flask import Blueprint, render_template

from scripts.ims_params_info.scr import main, SUP

ims = Blueprint('ims_params', __name__, url_prefix='/scripts/ims_params')


@ims.route('/')
@ims.route('/<int(min=1, max=6):sup>')
def ims_index(sup=None):
    __title__ = 'IMS params {}'.format(f'for SUP{sup}' if sup else '')
    if not sup:
        pass
    else:
        res = pd.DataFrame.from_dict(main(SUP[sup])).set_index('id')
        res = res.to_html()
        return render_template('ims/ims.html', vars=locals())
