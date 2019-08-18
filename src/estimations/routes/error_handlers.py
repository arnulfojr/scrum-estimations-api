from http import HTTPStatus
from typing import Union

from flask import jsonify, make_response

from organizations.exceptions import NotFound as OrganizationNotFound
from users.exceptions import NotFound as UserNotFound

from ..app import estimations_app
from ..exc import SequenceNotFound, SessionNotFound, TaskNotFound


@estimations_app.errorhandler(SequenceNotFound)
@estimations_app.errorhandler(OrganizationNotFound)
@estimations_app.errorhandler(SessionNotFound)
@estimations_app.errorhandler(UserNotFound)
@estimations_app.errorhandler(TaskNotFound)
def handle_not_found(error: Union[OrganizationNotFound, SequenceNotFound, None]):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)
