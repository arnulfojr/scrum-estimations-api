from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas
from users.models import User

from ..app import estimations_app
from ..exc import UserIsNotPartOfTheSession
from ..models import Session, SessionMember, Task


@estimations_app.route('/sessions/<code>', methods=['GET'])
def get_session(code: str):
    """Get the session.
    ---
    description: A session in which organizations estimate a series of tasks.
    tags:
        - Sessions
    parameters:
        - in: path
          name: code
          required: True
          type: string
          format: uuid
    definitions:
        Session:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: Some Session name
                completed:
                    type: boolean
                    description: 'If true the session is mark as completed and
                    no further changes can be made to the session.'
                sequence:
                    $ref: '#/definitions/Sequence'
                organization:
                    $ref: '#/definitions/Organization'
                members:
                    type: array
                    items:
                        $ref: '#/definitions/SessionMembers'
                tasks:
                    type: array
                    items:
                        $ref: '#/definitions/TaskWithoutSession'
                created_at:
                    type: string
                    format: datetime
        SessionWithoutTasks:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: Some Session name
                completed:
                    type: boolean
                    description: 'If true the session is mark as completed and
                    no further changes can be made to the session.'
                sequence:
                    $ref: '#/definitions/Sequence'
                organization:
                    $ref: '#/definitions/Organization'
                members:
                    type: array
                    items:
                        $ref: '#/definitions/SessionMembers'
                created_at:
                    type: string
                    format: datetime
    responses:
        200:
            description: Session
            schema:
                $ref: '#/definitions/Session'
        404:
            description: The session was not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not code:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(code)

    return make_response(jsonify(session.dump()), HTTPStatus.OK)


@estimations_app.route('/sessions/', methods=['POST'])
def create_session():
    """Create a session.
    ---
    tags:
        - Sessions
    parameters:
        - in: body
          name: body
          required: True
          schema:
            type: object
            properties:
                name:
                    type: string
                organization:
                    type: object
                    properties:
                        id:
                            type: string
                            format: uuid
                sequence:
                    type: object
                    properties:
                        name:
                            type: string
    responses:
        201:
            description: Session was created
            schema:
                $ref: '#/definitions/Session'
        400:
            description: Invalid request
            schema:
                $ref: '#/definitions/ValidationErrors'
    """
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_SESSION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    session = Session.from_data(**payload)

    return make_response(jsonify(session.dump()), HTTPStatus.CREATED)


@estimations_app.route('/sessions/<session_id>/members', methods=['GET'])
def get_session_members(session_id: str):
    """Get the session members.
    ---
    tags:
        - Sessions
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
    definitions:
        SessionMembers:
            type: array
            items:
                $ref: '#/definitions/SessionMember'
        SessionMember:
            $ref: '#/definitions/UserWithoutOrganization'
    responses:
        200:
            description: Members
            schema:
                $ref: '#/definitions/SessionMembers'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    if not session.session_members:
        return make_response(jsonify([]), HTTPStatus.OK)

    return make_response(
        jsonify([member.user.dump(with_organization=False) for member in session.session_members]),
        HTTPStatus.OK,
    )


@estimations_app.route('/sessions/<session_id>/members/', methods=['PUT'])
def join_session(session_id: str):
    """Join a session.
    ---
    description: 'Adds the user to the session as long as the user is member of same organization.'
    tags:
        - Sessions
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: body
          name: body
          required: True
          schema:
            type: object
            properties:
                user:
                    type: object
                    properties:
                        id:
                            type: string
                            format: uuid
    definitions:
        Member:
            type: object
            properties:
                session:
                    $ref: '#/definitions/Session'
                user:
                    $ref: '#/definitions/UserWithoutOrganization'
        Unauthorized:
            type: object
            properties:
                message:
                    type: string
                    example: You are not authorized to get, modified, create this resource.
    responses:
        200:
            description: User joined the session
            schema:
                $ref: '#/definitions/Member'
        400:
            description: Invalid request
            schema:
                $ref: '#/definitions/ValidationErrors'
        403:
            description: Unauthorized to join the session
            schema:
                $ref: '#/definitions/Unauthorized'
        422:
            description: User already joined the session
            schema:
                $ref: '#/definitions/UnprocessableEntity'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.JOIN_SESSION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    user = User.lookup(payload['user']['id'])

    if not user.belongs_to_organization(session.organization):
        return make_response(jsonify({
            'message': f'User({user.id}) is not part of the session\'s '
                       f'organization({session.organization.id})',
        }), HTTPStatus.UNAUTHORIZED)

    try:
        SessionMember.lookup(session, user)
    except UserIsNotPartOfTheSession:
        member = SessionMember.create(user=user, session=session)
    else:
        return make_response(jsonify({
            'message': f'User has already joined the session',
        }), HTTPStatus.UNPROCESSABLE_ENTITY)

    return make_response(jsonify(member.dump()), HTTPStatus.OK)


@estimations_app.route('/sessions/<session_id>/members/<user_id>', methods=['DELETE'])
def leave_session(session_id: str, user_id: str):
    """Leave the session.
    ---
    tags:
        - Sessions
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: path
          name: user_id
          type: string
          format: uuid
          required: True
    responses:
        204:
            description: User was removed from the session.
        404:
            description: The specified user or session were not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)
    user = User.lookup(user_id)

    session = SessionMember.lookup(user=user, session=session)
    session.leave()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)


@estimations_app.route('/sessions/<session_id>/tasks', methods=['GET'])
def get_session_tasks(session_id: str):
    """Get the session's tasks.
    ---
    tags:
        - Sessions
        - Tasks
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
    definitions:
        TasksWithoutSession:
            type: array
            items:
                $ref: '#/definitions/TaskWithoutSession'
        TaskWithoutSession:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: TASK-123
                created_at:
                    type: string
                    format: datetime
                estimations:
                    $ref: '#/definitions/EstimationsWithoutTask'
    responses:
        200:
            description: Session's tasks
            schema:
                $ref: '#/definitions/TasksWithoutSession'
        404:
            description: Session not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    return make_response(
        jsonify([task.dump(with_session=False) for task in session.tasks]),
        HTTPStatus.OK,
    )


@estimations_app.route('/sessions/<session_id>/tasks/<task>', methods=['GET'])
def get_task_from_session(session_id: str, task: str):
    """Get a task from the session.
    ---
    tags:
        - Sessions
        - Tasks
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: path
          name: task
          type: string
          required: True
    definitions:
        EstimationWithoutTask:
            type: object
            properties:
                value:
                    $ref: '#/definitions/Value'
                user:
                    $ref: '#/definitions/UserWithoutOrganization'
                created_at:
                    type: string
                    format: datetime
        EstimationsWithoutTask:
            type: array
            items:
                $ref: '#/definitions/EstimationWithoutTask'
        Task:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: TASK-123
                created_at:
                    type: string
                    format: datetime
                session:
                    $ref: '#/definitions/SessionWithoutTasks'
                estimations:
                    $ref: '#/definitions/EstimationsWithoutTask'
    responses:
        200:
            description: The task
            schema:
                $ref: '#/definitions/Task'
        400:
            description: The task requested was not found
            schema:
                $ref: '#/definitions/NotFound'
        404:
            description: Session not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    try:
        task = Task.lookup(task, session=session)
    except (TypeError, ValueError):
        return make_response(jsonify({
            'message': 'We could not infer the Task from the given input...',
        }), HTTPStatus.BAD_REQUEST)

    return make_response(jsonify(task.dump()), HTTPStatus.OK)


@estimations_app.route('/sessions/<session_id>/tasks/', methods=['POST'])
def add_task_to_session(session_id: str):
    """Create a task in the session.
    ---
    tags:
        - Tasks
        - Sessions
    parameters:
        - in: path
          name: session_id
          type: string
          format: uuid
          required: True
        - in: body
          name: body
          required: True
          schema:
            type: object
            properties:
                name:
                    type: string
                    example: TASK-123
    responses:
        201:
            description: The task
            schema:
                $ref: '#/definitions/Task'
        400:
            description: The task requested was not found
            schema:
                $ref: '#/definitions/ValidationErrors'
        404:
            description: Session not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_TASK):
        return make_response(jsonify(validator.errors),
                             HTTPStatus.BAD_REQUEST)

    task = Task.create(session=session, name=payload['name'])

    return make_response(jsonify(task.dump()), HTTPStatus.CREATED)


@estimations_app.route('/sessions/<session_id>/tasks/<task>', methods=['PATCH'])
def edit_task_from_session(session_id: str, task: str):
    """Edit the task.
    ---
    tags:
        - Tasks
        - Sessions
    parameters:
        - in: path
          name: session_id
          format: uuid
          type: string
          required: True
        - in: path
          name: task
          required: True
          type: string
        - in: body
          name: body
          schema:
            type: object
            properties:
                name:
                    type: string
                    example: TASK-123
    responses:
        200:
            description: Task was updated
            schema:
                $ref: '#/definitions/Task'
        400:
            description: Input errors
            schema:
                $ref: '#/definitions/ValidationErrors'
        422:
            description: The task identifier is not valid
            schema:
                $ref: '#/definitions/UnprocessableEntity'
    """
    if not session_id:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(session_id)

    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.EDIT_TASK):
        return make_response(jsonify(validator.errors),
                             HTTPStatus.BAD_REQUEST)

    try:
        task = Task.lookup(task, session=session)
    except (TypeError, ValueError):
        return make_response(jsonify({
            'message': 'We could not infer the Task from the given input...',
        }), HTTPStatus.UNPROCESSABLE_ENTITY)

    task.name = payload['name']
    task.save()

    return make_response(jsonify(task.dump()), HTTPStatus.OK)
