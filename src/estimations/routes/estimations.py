from http import HTTPStatus
from typing import Tuple, Union

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas
from users.models import User

from ..app import estimations_app
from ..exc import EmptyIdentifier, InvalidRequest, ValueNotFound
from ..models import (
    Estimation,
    Sequence,
    Session,
    Task,
    Value,
)


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/estimations', methods=['GET'])
def get_estimations(session_id: str, task_id: str):
    session, task = get_or_fail(session_id, task_id)

    payload = [estimation.dump(with_task=False) for estimation in task.estimations]
    return make_response(jsonify(payload), HTTPStatus.OK)


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/estimations/', methods=['PUT'])
def estimate(session_id: str, task_id: str):
    session, task = get_or_fail(session_id, task_id)

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

    value_payload = payload['value']
    sequence: Sequence = session.sequence
    if 'id' in value_payload:
        value = Value.lookup(value_payload['id'])
    elif 'name' in value_payload:
        value = sequence.get_value_for_value_name(value_payload['name'])
    elif 'value' in value_payload:
        value = sequence.get_value_for_numeric_value(value_payload['value'])
    else:
        value = None

    if not value:
        raise ValueNotFound('The Value given did not contain a value from the sequence')

    # did the user already estimated?
    estimation = Estimation.lookup(task, user)
    if not estimation:
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
    session, task = get_or_fail(session_id, task_id)

    mean_estimation = task.mean_estimation
    everybody_estimated = task.is_estimated_by_all_members
    consensus_met = task.consensus_met and everybody_estimated
    closest_value = session.sequence.closest_possible_value(mean_estimation)
    non_numeric_estimations = [estimation.dump(with_task=False)
                               for estimation in task.non_numeric_estimations]

    return make_response(jsonify({
        'mean': float(mean_estimation),
        'everybody_estimated': everybody_estimated,
        'consensus_met': consensus_met,
        'closest_value': closest_value.dump() if closest_value else 0,
        'task': task.dump(with_session=False, with_estimations=True),
        'has_non_numeric_estimations': task.has_non_numeric_estimations(),
        'non_numeric_estimations': non_numeric_estimations,
    }), HTTPStatus.OK)


def get_or_fail(session_id: Union[str, None], task_id: Union[str, None]) -> Tuple[Session, Task]:
    """Gets the session and task based on their identifiers."""
    if not session_id:
        raise EmptyIdentifier('Please provide a session identifier')
    if not task_id:
        raise EmptyIdentifier('Please provide a valid task identifier')

    session = Session.lookup(session_id)

    try:
        task = Task.lookup(task_id, session=session)
    except (TypeError, ValueError) as e:
        raise InvalidRequest('We could not infer the Task from the given input...') from e
    else:
        return session, task
