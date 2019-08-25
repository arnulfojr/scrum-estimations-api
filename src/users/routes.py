from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from users.models import User
from users.schemas import CREATE_USER_SCHEMA

from .app import users_app
from .exceptions import NotFound, UserAlreadyExists


@users_app.errorhandler(NotFound)
def handle_user_not_found(error: NotFound):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)


@users_app.errorhandler(UserAlreadyExists)
def handle_user_already_exists_error(error: UserAlreadyExists):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.UNPROCESSABLE_ENTITY)


@users_app.route('/<user_id>', methods=['GET'])
def get_user(user_id: str):
    """Get the user's information.
    ---
    tags:
    - Users
    parameters:
        - in: path
          name: user_id
          type: string
          required: True
          format: uuid
    definitions:
        UserWithoutOrganization:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                email:
                    type: string
                    format: email
                role:
                    type: string
                    enum:
                        - USER
                        - ADMIN
                registered_on:
                    type: string
                    format: datetime
        NotFound:
            type: object
            properties:
                message:
                    type: string
                    example: Not Found
    responses:
        200:
            description: User's information
            schema:
                $ref: '#/definitions/UserWithoutOrganization'
        404:
            description: User not found
            schema:
                $ref: '#/definitions/NotFound'

    """
    user = User.lookup(user_id)
    return make_response(jsonify(user.dump()), HTTPStatus.OK)


@users_app.route('/<user_id>/organization', methods=['GET'])
def get_user_with_organizations(user_id: str):
    """Returns the user's organization.
    ---
    tags:
        - Users
        - Organizations
    parameters:
        - in: path
          name: user_id
          format: uuid
          required: True
          type: string
    definitions:
        Organization:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: Some Organization
                users:
                    type: array
                    description: All the users belonging to the organization
                    items:
                        $ref: '#/definitions/UserWithoutOrganization'
    responses:
        200:
            description: User's Organization
            schema:
                $ref: '#/definitions/Organization'
        404:
            description: User or Organization not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    user = User.lookup(user_id)
    if not user.organization:
        response = make_response(jsonify({
            'message': 'The user does not have an organization.',
        }), HTTPStatus.NOT_FOUND)
        return response

    return user.organization.dump()


@users_app.route('/', methods=['POST'])
def create_user():
    """Creates a user.
    ---
    tags:
    - Users
    parameters:
        - in: body
          required: True
          name: body
          schema:
            type: object
            properties:
                email:
                    type: string
                    format: email
                name:
                    type: string
                    example: John Doe
                password:
                    type: string
                    format: password
                role:
                    type: string
                    enum:
                        - USER
                        - ADMIN
                organization:
                    type: object
                    properties:
                        id:
                            type: string
                            format: uuid
                registered_on:
                    type: string
                    format: datetime
    definitions:
        OrganizationWithoutUsers:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    example: Some Organization
        User:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                email:
                    type: string
                    format: email
                role:
                    type: string
                    enum:
                        - USER
                        - ADMIN
                registered_on:
                    type: string
                    format: datetime
                organization:
                    $ref: '#/definitions/OrganizationWithoutUsers'
        ValidationErrors:
            type: object
            properties:
                attribute_name:
                    type: array
                    items:
                        type: string
                        example: name must be present
    responses:
        201:
            description: User was created
            schema:
                $ref: '#/definitions/User'
        400:
            description: Errors
            schema:
                $ref: '#/definitions/ValidationErrors'
    """
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, CREATE_USER_SCHEMA):
        return make_response(jsonify(validator.errors),
                             HTTPStatus.BAD_REQUEST)

    user = User.create_from(payload)
    return make_response(
        jsonify(user.dump(with_organization=True)),
        HTTPStatus.CREATED,
    )


@users_app.route('/<user_id>', methods=['PATCH'])
def update_user(user_id: str):
    """Path the user.
    ---
    tags:
        - Users
    parameters:
        - in: path
          name: user_id
          required: True
          type: string
          format: uuid
        - in: body
          required: True
          name: body
          schema:
            properties:
                email:
                    type: string
                    format: email
                name:
                    type: string
                    example: John Doe
                role:
                    type: string
                    enum:
                        - ADMIN
                        - USER
                        - SUPER_ADMIN
    responses:
        200:
            description: User was patched
            schema:
                $ref: '#/definitions/User'
        404:
            description: Specified user was not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    user = User.lookup(user_id)

    payload = request.get_json()
    user.update_from(**payload)
    user.save()

    return make_response(
        jsonify(user.dump(with_organization=True)),
        HTTPStatus.OK,
    )


@users_app.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id: str):
    """Delete the user.
    ---
    tags:
        - Users
    parameters:
        - in: path
          name: user_id
          type: string
          format: uuid
          required: True
    responses:
        204:
            description: User deleted
        404:
            description: User not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    user = User.lookup(user_id)

    user.delete_instance()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)
