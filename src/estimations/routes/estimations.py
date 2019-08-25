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
    """Get the tasks' estimations.
    ---
    tags:
        - Tasks
        - Estimations
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: path
          name: task_id
          type: string
          required: True
    definitions:
        Estimations:
            type: array
            items:
                $ref: '#/definitions/Estimation'
        Estimation:
            type: object
            properties:
                value:
                    $ref: '#/definitions/Value'
                task:
                    $ref: '#/definitions/TaskWithoutSession'
                user:
                    $ref: '#/definitions/UserWithoutOrganization'
                created_at:
                    type: string
                    format: datetime
    responses:
        200:
            description: Task estimations
            schema:
                $ref: '#/definitions/Estimations'
        404:
            description: The session or task were not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    session, task = get_or_fail(session_id, task_id)

    payload = [estimation.dump(with_task=False) for estimation in task.estimations]
    return make_response(jsonify(payload), HTTPStatus.OK)


@estimations_app.route('/sessions/<session_id>/tasks/<task_id>/estimations/', methods=['PUT'])
def estimate(session_id: str, task_id: str):
    """Estimate a task.
    ---
    tags:
        - Estimations
        - Tasks
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: path
          name: task_id
          type: string
          required: True
        - in: body
          name: body
          required: True
          schema:
            type: object
            properties:
                value:
                    type: object
                    description: 'Only one of the attributes is required.
                    If all given the first priority is the id, then the value and the name at the end.'
                    properties:
                        id:
                            type: string
                            format: uuid
                            description: Provide only one of these
                        name:
                            type: string
                            example: Coffee Break
                            description: Provide only one of these
                        value:
                            type: number
                            format: float
                            example: 2.0
                            description: Provide only one of these
                user:
                    type: object
                    properties:
                        id:
                            type: string
                            format: uuid
    responses:
        200:
            description: The estimation was updated
            schema:
                $ref: '#/definitions/Estimation'
        201:
            description: The estimation was created
            schema:
                $ref: '#/definitions/Estimation'
        400:
            description: Bad request input
            schema:
                $ref: '#/definitions/ValidationErrors'
        404:
            description: The session or task were not found
            schema:
                $ref: '#/definitions/NotFound'
    """
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
    elif 'value' in value_payload:
        value = sequence.get_value_for_numeric_value(value_payload['value'])
    elif 'name' in value_payload:
        value = sequence.get_value_for_value_name(value_payload['name'])
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
    """Get the summary of the task.
    ---
    tags:
        - Tasks
        - Estimations
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: path
          name: task_id
          type: string
          required: True
    definitions:
        RuntimeSummary:
            type: object
            properties:
                mean:
                    type: number
                    format: float
                    example: 2.5
                    description: The task's mean
                everybody_estimated:
                    type: boolean
                    description: true if all the session members had estimated
                consensus_met:
                    type: boolean
                    description: If everybody voted for the same value
                closest_value:
                    $ref: '#/definitions/Value'
                task:
                    $ref: '#/definitions/TaskWithoutSession'
                has_non_numeric_estimations:
                    type: boolean
                    description: If somebody voted for a value that does not have a numeric representation
                non_numeric_estimations:
                    type: array
                    items:
                        $ref: '#/definitions/Estimation'
    responses:
        200:
            description: Get the task's summary
            schema:
                $ref: '#/definitions/RuntimeSummary'
        404:
            description: Task or session were not found
            schema:
                $ref: '#/definitions/NotFound'
    """
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
