from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas
from users.models import User

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

    payload = [estimation.dump(with_task=False) for estimation in task.estimations]
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

    # FIXME: move the user to the authentication layer
    user_id = payload['user']['id']

    user = User.lookup(user_id)
    if not user.belongs_to_organization(session.organization):
        return make_response(jsonify({
            'message': f'This user({user_id}) seems to not be part of the organization\'s session',
        }), HTTPStatus.UNAUTHORIZED)

    value_id = payload['value']['id']
    value = Value.lookup(value_id)

    # did the user already estimated?
    estimation = Estimation.lookup(task, user)
    if estimation is None:
        estimation = Estimation(value=value, user=user, task=task)
        estimation.save(force_insert=True)
        http_status_code = HTTPStatus.CREATED
    else:
        estimation.value = value
        estimation.save()
        http_status_code = HTTPStatus.OK

    return make_response(
        jsonify(estimation.dump()),
        http_status_code,
    )


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/summary', methods=['GET'])
def get_task_summary(session_id: str, task_id: str):
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

    mean_estimation = task.mean_estimation
    everybody_estimated = task.is_estimated_by_all_members
    consensus_met = task.consensus_met
    closest_value = session.sequence.closest_possible_value(mean_estimation)

    return make_response(jsonify({
        'mean': float(mean_estimation),
        'everybody_estimated': everybody_estimated,
        'consensus_met': consensus_met,
        'closest_value': closest_value.dump() if closest_value else 0,
        'task': task.dump(with_session=False, with_estimations=True),
        'has_non_numeric_estimations': task.has_non_numeric_estimations(),
        'non_numeric_estimations': [estimation.dump(with_task=False)
                                    for estimation in task.non_numeric_estimations],
    }), HTTPStatus.OK)
