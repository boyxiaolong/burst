# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')

from burst import Burst, Blueprint

import logging

LOG_FORMAT = '\n'.join((
    '/' + '-' * 80,
    '[%(levelname)s][%(asctime)s][%(process)d:%(thread)d][%(filename)s:%(lineno)d %(funcName)s]:',
    '%(message)s',
    '-' * 80 + '/',
))

logger = logging.getLogger('burst')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

GROUP_CONFIG = {
    1: {
        'count': 10,
    },
}

app = Burst()
app.config.from_object(__name__)


@app.route(1)
def index(request):
    return dict(
        ret=10
    )


app.run()
