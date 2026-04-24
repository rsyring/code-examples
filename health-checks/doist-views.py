import logging

from flask import Blueprint, current_app, request
import sqlalchemy as sa

from .ext import db
from .libs import actions, checks, sync


log = logging.getLogger(__name__)
public = Blueprint('public', __name__)


@public.route('/', methods=['POST', 'GET'])
def index():
    return "'sup yos"


@public.route('/hooks', methods=['POST', 'GET'])
def hooks():
    data = request.get_json(silent=True)
    actions.on_webhook(data)
    checks.ping_webhook_alive()
    return 'ok'


@public.route('/oauth', methods=['POST', 'GET'])
def oauth():
    print(request.get_json(silent=True))
    return 'oauth done'


@public.route('/healthy-db')
def healthy_db():
    try:
        with db.engine.begin() as conn:
            conn.execute(sa.text('select id from project limit 1')).fetchall()
            return f'{current_app.name} ok'
    except Exception:
        log.exception('Todoist API health check failed')
        return 'failed', 503


@public.route('/healthy-api')
def healthy_api():
    api = sync.SyncAPI()
    try:
        api.user()
        return f'{current_app.name} api ok'
    except Exception:
        log.exception('Todoist API health check failed')
        return 'failed', 503
