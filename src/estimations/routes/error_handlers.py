from http import HTTPStatus
from typing import Union

from flask import jsonify, make_response

from organizations.exceptions import NotFound as OrganizationNotFound

from ..app import estimations_app
from ..exc import SequenceNotFound, SessionNotFound


@estimations_app.errorhandler(SequenceNotFound)
@estimations_app.errorhandler(OrganizationNotFound)
@estimations_app.errorhandler(SessionNotFound)
def handle_not_found(error: Union[OrganizationNotFound, SequenceNotFound, None]):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)
