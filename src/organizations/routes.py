from http import HTTPStatus
from typing import Union

from cerberus import Validator
from flask import jsonify, make_response, request

from organizations import schemas
from organizations.models import Organization
from users.exceptions import NotFound as UserNotFound
from users.models import User

from .app import organizations_app
from .exceptions import NotFound


@organizations_app.errorhandler(NotFound)
@organizations_app.errorhandler(UserNotFound)
def handle_organization_not_found(error: Union[NotFound, UserNotFound]):
    return make_response(
        jsonify({
            'message': str(error),
        }),
        HTTPStatus.NOT_FOUND,
    )


@organizations_app.route('/<org_id>', methods=['GET'])
def get_organizations(org_id: str):
    organization = Organization.lookup(org_id)

    payload = organization.dict_dump()
    return make_response(jsonify(payload), HTTPStatus.OK)


@organizations_app.route('/', methods=['POST'])
def create_organization():
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_ORGANIZATION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    organization = Organization.create_from(payload)
    data = organization.dict_dump()
    return make_response(jsonify(data), HTTPStatus.CREATED)


@organizations_app.route('/<org_id>', methods=['DELETE'])
def delete_organization(org_id: str):
    organization = Organization.lookup(org_id)

    user_count = len(organization.users)
    if user_count > 0:
        return make_response(jsonify({
            'message': 'Please remove all users from the organization',
        }), HTTPStatus.UNPROCESSABLE_ENTITY)

    organization.delete_instance()
    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)


@organizations_app.route('/<org_id>', methods=['PATCH'])
def update_organization(org_id: str):
    organization = Organization.lookup(org_id)

    data = request.get_json()

    validator = Validator()
    if not validator.validate(data, schemas.CREATE_ORGANIZATION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    organization_name = data.get('name')
    if organization_name:
        organization.name = organization_name

    organization.save()

    return make_response(
        jsonify(organization.dict_dump()),
        HTTPStatus.OK,
    )


@organizations_app.route('/<org_id>/users', methods=['POST'])
def add_user_to_organization(org_id: str):
    organization = Organization.lookup(org_id)
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.JOIN_ORGANIZATION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    user_id = payload['user']['id']
    user = User.lookup(user_id)

    user.organization = organization
    user.save(only=('organization',))

    return make_response(
        jsonify({
            'organization': organization.dict_dump(with_users=True),
            'user': user.dict_dump(with_organization=False),
        }),
        HTTPStatus.CREATED,
    )


@organizations_app.route('/<org_id>/users/<user_id>', methods=['DELETE'])
def remove_user_from_organization(org_id: str, user_id: str):
    Organization.lookup(org_id)
    user = User.lookup(user_id)

    user.organization = None
    user.save(only=('organization',))

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)
