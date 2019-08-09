from http import HTTPStatus
from typing import Union

from cerberus import Validator
from flask import jsonify, make_response, request

from organizations import schemas
from organizations.models import Organization
from users.exceptions import NotFound as UserNotFound
from users.models import User

from .app import OrganizationsApp
from .exceptions import NotFound


@OrganizationsApp.errorhandler(NotFound)
@OrganizationsApp.errorhandler(UserNotFound)
def handle_organization_not_found(error: Union[NotFound, UserNotFound]):
    return make_response(
        jsonify({
            'message': str(error),
        }),
        HTTPStatus.NOT_FOUND,
    )


@OrganizationsApp.route('/<org_id>', methods=['GET'])
def get_organizations(org_id: str):
    organization = Organization.lookup(org_id)

    payload = organization.dict_dump()
    return make_response(jsonify(payload), HTTPStatus.OK)


@OrganizationsApp.route('/', methods=['POST'])
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


@OrganizationsApp.route('/<org_id>', methods=['PATCH'])
def update_organization(org_id: str):
    organization = Organization.lookup(org_id)

    data = request.get_json()
    if data.get('name'):
        organization.name = data.get('name')

    organization.save()

    return make_response(
        jsonify(organization.dict_dump()),
        HTTPStatus.OK,
    )


@OrganizationsApp.route('/<org_id>/users', methods=['POST'])
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
            'organization': organization.dict_dump(),
            'user': user.dict_dump(with_organization=False),
        }),
        HTTPStatus.CREATED,
    )


@OrganizationsApp.route('/<org_id>/users/<user_id>', methods=['DELETE'])
def remove_user_from_organization(org_id: str, user_id: str):
    Organization.lookup(org_id)
    user = User.lookup(user_id)

    user.organization = None
    user.save(only=('organization',))

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)
