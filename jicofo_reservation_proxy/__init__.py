import flask

from jicofo_reservation_proxy.routes import (
    initialise_service,
    conference,
)
from jicofo_reservation_proxy.service import DummyService


def create_app(service_class=DummyService):
    """ Initialises and returns the flask application.

    Args:
        service_class (class): Implementation class for underlying service. Defaults to a placeholder implementation
                               that allows all creation requests and keeps track of meetings in memory.

    Returns:
        flask.Flask
    """

    app = flask.Flask(__name__, static_folder=None)

    initialise_routes(flask_app=app)
    initialise_service(flask_app=app, service_class=service_class)

    return app


def initialise_routes(flask_app):
    flask_app.register_blueprint(conference)

