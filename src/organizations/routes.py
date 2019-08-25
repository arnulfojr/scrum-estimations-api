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
    """Get the organization.
    ---
    tags:
        - Organizations
    parameters:
        - in: path
          name: org_id
          required: True
          type: string
          format: uuid
    responses:
        200:
            description: Organization details
            schema:
                $ref: '#/definitions/Organization'
        404:
            description: Organization not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    organization = Organization.lookup(org_id)

    payload = organization.dump()
    return make_response(jsonify(payload), HTTPStatus.OK)


@organizations_app.route('/', methods=['POST'])
def create_organization():
    """Creates an organization.
    ---
    tags:
        - Organizations
    parameters:
        - in: body
          required: True
          name: body
          schema:
            properties:
                name:
                    type: string
                    example: An Organization Name
    responses:
        201:
            description: Creates the organizations
            schema:
                $ref: '#/definitions/OrganizationWithoutUsers'
        400:
            description: Invalid request
            schema:
                $ref: '#/definitions/ValidationErrors'
    """
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_ORGANIZATION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    organization = Organization.create_from(payload)
    data = organization.dump()
    return make_response(jsonify(data), HTTPStatus.CREATED)


@organizations_app.route('/<org_id>', methods=['DELETE'])
def delete_organization(org_id: str):
    """Deletes an organization.
    ---
    tags:
        - Organizations
    parameters:
        - in: path
          name: org_id
          type: string
          format: uuid
          required: True
    definitions:
        UnprocessableEntity:
            type: object
            properties:
                message:
                    type: string
                    example: Please remove all users from the organization
    responses:
        204:
            description: The organization was deleted
        422:
            description: The organization couldn't be deleted because it still has users related to it.
            schema:
                $ref: '#/definitions/UnprocessableEntity'
    """
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
    """Update the organization.
    ---
    tags:
        - Organizations
    parameters:
        - in: path
          name: org_id
          required: True
          type: string
          format: uuid
        - in: body
          name: body
          schema:
            type: object
            properties:
                name:
                    type: string
                    example: Organization Name
    responses:
        200:
            description: Organization was properly updated
            schema:
                $ref: '#/definitions/Organization'
        400:
            description: Bad input
            schema:
                $ref: '#/definitions/ValidationErrors'
    """
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
        jsonify(organization.dump()),
        HTTPStatus.OK,
    )


@organizations_app.route('/<org_id>/users', methods=['POST'])
def add_user_to_organization(org_id: str):
    """Add user to the organization.
    ---
    tags:
        - Organizations
        - Users
    parameters:
        - in: path
          name: org_id
          format: uuid
          type: string
          required: True
    definitions:
        OrganizationUserRelationship:
            type: object
            properties:
                organization:
                    $ref: '#/definitions/Organization'
                user:
                    $ref: '#/definitions/UserWithoutOrganization'
    responses:
        201:
            description: Relationship created
            schema:
                $ref: '#/definitions/OrganizationUserRelationship'
        400:
            description: Bad input
            schema:
                $ref: '#/definitions/ValidationErrors'
        404:
            description: Organization or User not found
            schema:
                $ref: '#/definitions/NotFound'
    """
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
            'organization': organization.dump(with_users=True),
            'user': user.dump(with_organization=False),
        }),
        HTTPStatus.CREATED,
    )


@organizations_app.route('/<org_id>/users/<user_id>', methods=['DELETE'])
def remove_user_from_organization(org_id: str, user_id: str):
    """Remove the user from an organization.
    ---
    tags:
        - Organizations
        - Users
    parameters:
        - in: path
          name: org_id
          type: string
          required: True
          format: uuid
        - in: path
          name: user_id
          required: True
          type: string
          format: uuid
    responses:
        204:
            description: The user was unrelated to the organization.
        404:
            description: The user or the organization specified were not found.
            schema:
                $ref: '#/definitions/NotFound'
    """
    Organization.lookup(org_id)
    user = User.lookup(user_id)

    user.organization = None
    user.save(only=('organization',))

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)
