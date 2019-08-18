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
    if not code:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(code)

    return make_response(jsonify(session.dump()), HTTPStatus.OK)


@estimations_app.route('/sessions/', methods=['POST'])
def create_session():
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
        }), HTTPStatus.BAD_REQUEST)

    task.name = payload['name']
    task.save()

    return make_response(jsonify(task.dump()), HTTPStatus.CREATED)
