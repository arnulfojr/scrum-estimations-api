from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas

from ..app import estimations_app
from ..models import (
    Estimation,
    Session,
    Task,
    Value,
)


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/estimations', methods=['GET'])
def get_estimations(session_id: str, task_id: str):
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    try:
        task = Task.lookup(task_id, session=session)
    except (TypeError, ValueError):
        return make_response(jsonify({
            'message': 'We could not infer the Task from the given input...',
        }), HTTPStatus.BAD_REQUEST)

    payload = [estimation.dump() for estimation in task.estimations]
    return make_response(jsonify(payload), HTTPStatus.OK)


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/estimations/', methods=['PUT'])
def estimate(session_id: str, task_id: str):
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    try:
        task = Task.lookup(task_id, session=session)
    except (TypeError, ValueError):
        return make_response(jsonify({
            'message': 'We could not infer the Task from the given input...',
        }), HTTPStatus.BAD_REQUEST)

    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_ESTIMATION):
        return make_response(jsonify(validator.errors), HTTPStatus.BAD_REQUEST)

    # TODO: move the user to the authentication layer
    user_id = payload['user']['id']
    value_id = payload['value']['id']

    value = Value.lookup(value_id)

    estimation = Estimation(value=value, user=user_id, task=task)
    estimation.save(force_insert=True)

    return make_response(
        jsonify(estimation.dump()),
        HTTPStatus.CREATED,
    )


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/summary', methods=['GET'])
def get_task_summary(session_id: str, task_id: str):
    pass
