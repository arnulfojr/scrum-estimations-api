from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from users.models import User
from users.schemas import CREATE_USER_SCHEMA

from .app import users_app
from .exceptions import NotFound


@users_app.errorhandler(NotFound)
def handle_user_not_found(error: NotFound):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)


@users_app.route('/<user_id>', methods=['GET'])
def get_user(user_id: str):
    """Get the user's information."""
    user = User.lookup(user_id)
    return make_response(jsonify(user.dict_dump()), HTTPStatus.OK)


@users_app.route('/<user_id>/organizations', methods=['GET'])
def get_user_with_organizations(user_id: str):
    """Get the user's information."""
    user = User.lookup(user_id)
    if not user.organization:
        response = make_response(jsonify({
            'message': 'The user does not have an organization.',
        }), HTTPStatus.NOT_FOUND)
        return response

    return user.organization.dict_dump()


@users_app.route('/', methods=['POST'])
def create_user():
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, CREATE_USER_SCHEMA):
        return make_response(jsonify(validator.errors),
                             HTTPStatus.BAD_REQUEST)

    user = User.create_from(payload)
    return make_response(
        jsonify(user.dict_dump(with_organization=True)),
        HTTPStatus.CREATED,
    )


@users_app.route('/<user_id>', methods=['PATCH'])
def update_user(user_id: str):
    user = User.lookup(user_id)

    payload = request.get_json()
    user.update_from(**payload)
    user.save()

    return make_response(
        jsonify(user.dict_dump(with_organization=True)),
        HTTPStatus.OK,
    )


@users_app.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id: str):
    user = User.lookup(user_id)

    user.delete_instance()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)
