import logging

from flask import (
    Blueprint,
    jsonify,
    make_response,
    request,
    current_app,
    g,
)
from werkzeug.local import LocalProxy

from jicofo_reservation_proxy.service import ENUM_CREATION_STATUS

logger = logging.getLogger(__name__)

conference = Blueprint('conference', __name__, url_prefix='/conference')


def initialise_service(flask_app, service_class):
    flask_app.config['service_class'] = service_class


def _get_service():
    if 'service' not in g:
        assert 'service_class' in current_app.config, "initialise_service() not called?"
        g.service = current_app.config['service_class']()
    return g.service


service = LocalProxy(_get_service)


def respond(payload, status=200):
    return make_response(jsonify(payload), status)


@conference.route('', methods=['POST'])
def conference_create():
    # Jicofo sends data as x-www-form-urlencoded with fields "name", "start_time", "mail_owner"
    room_name = request.form.get('name')  # short name of the conference room(not full MUC address)
    start_time = request.form.get('start_time')  # Java SimpleDateFormat: yyyy-MM-dd'T'HH:mm:ss.SSSX
    mail_owner = request.form.get('mail_owner')  # user id e.g. ab7bba1e-405b-47ac-9465-a7f8b032a033@jitsi-host.domain

    if not all((room_name, start_time, mail_owner)):
        logger.error('Missing params from Jicofo')
        return respond(status=500, payload={
            'message': 'Internal server error (Missing Jicofo params)',
        })

    result = service.create_conference(
        room_name=room_name,
        start_time=start_time,
        mail_owner=mail_owner,
    )

    if result.status == ENUM_CREATION_STATUS.OK:
        return respond(status=200, payload=result.info.to_dict())
    elif result.status == ENUM_CREATION_STATUS.ALREADY_EXIST:
        return respond(status=409, payload={
            'conflict_id': result.info.conflict_id,
        })
    else:
        assert result.status == ENUM_CREATION_STATUS.REJECTED
        return respond(status=403, payload={
            'message': result.message,
        })


@conference.route('<int:conflict_id>', methods=['GET'])
def conference_get(conflict_id):
    info = service.get_conference(conflict_id=conflict_id)

    if info:
        return respond(status=200, payload=info.to_dict())
    else:
        return respond(status=404, payload={'message': 'unknown conference'})


@conference.route('<int:conflict_id>', methods=['DELETE'])
def conference_delete(conflict_id):
    # NOTE: due to existing bug (https://github.com/jitsi/jicofo/issues/39) this endpoint may not be called after all
    #       users leave meeting despite what it says in the docs. Until that is fixed, this will only be called on
    #       on expiry.
    try:
        service.delete_conference(conflict_id=conflict_id)
    except:
        logger.exception('delete_conference() call failed')

    # always return 200 or we'll be subject to odd Jicofo behaviour
    # See https://community.jitsi.org/t/jicofo-reservation-reuse-room-after-expiring/69243/5
    return respond(status=200, payload={'message': 'OK'})
