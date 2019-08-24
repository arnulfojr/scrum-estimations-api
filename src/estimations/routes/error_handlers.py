from http import HTTPStatus
from typing import Union

from flask import jsonify, make_response

from organizations.exceptions import NotFound as OrganizationNotFound
from users.exceptions import NotFound as UserNotFound

from ..app import estimations_app
from ..exc import EmptyIdentifier, InvalidRequest
from ..exc import SequenceNotFound, SessionNotFound, TaskNotFound, ValueNotFound


@estimations_app.errorhandler(SequenceNotFound)
@estimations_app.errorhandler(OrganizationNotFound)
@estimations_app.errorhandler(SessionNotFound)
@estimations_app.errorhandler(UserNotFound)
@estimations_app.errorhandler(TaskNotFound)
@estimations_app.errorhandler(ValueNotFound)
def handle_not_found(error: Exception):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)


@estimations_app.errorhandler(EmptyIdentifier)
@estimations_app.errorhandler(InvalidRequest)
@estimations_app.errorhandler(UserNotFound)
def handle_invalid_requests(error: Union[EmptyIdentifier, InvalidRequest, UserNotFound]):
    return make_response(
        jsonify({
            'message': str(error),
        }),
        error.status_code,
    )
