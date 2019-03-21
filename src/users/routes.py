from aiohttp import web
from aiohttp.web import Request
from aiohttp.web import RouteTableDef
from cerberus import Validator

from users.models import User
from users.schemas import CREATE_USER_SCHEMA


router = RouteTableDef()

validator = Validator()


@router.route('GET', '/{user_id}')
async def get_user(request: Request):
    """Get the user's information."""
    user_id = request.match_info['user_id']
    user = await User.get(user_id)
    if not user:
        return web.json_response({
            'message': 'The user does not exist.',
        }, status=404)

    return web.json_response(user.dict_dump())


@router.route('GET', '/{user_id}/organizations')
async def get_user_with_organizations(request: Request):
    """Get the user's information."""
    user_id = request.match_info['user_id']
    user = await User.get(user_id)
    if not user:
        return web.json_response({
            'message': 'The user does not exist.',
        }, status=404)

    if not user.organization:
        return web.json_response({
            'message': 'The user does not have an organization.',
        }, status=404)

    return web.json_response(user.organization.dict_dump())


@router.route('POST', '/')
async def create_user(request: Request):
    payload = await request.json()
    if not validator.validate(payload, CREATE_USER_SCHEMA):
        return web.json_response(validator.errors, status=400)

    user = await User.create_from(payload)
    if not user:
        return web.json_response({
            'message': 'Validation error',
        }, status=400)

    data = user.dict_dump()

    return web.json_response(data, status=201)


@router.route('PUT', '/{user_id}')
async def update_user(request):
    pass  # TODO


@router.route('DELETE', '/{user_id}')
async def delete_user(request: Request):
    user_id = request.match_info['user_id']
    user = await User.get(user_id)
    if not user:
        return web.json_response({}, status=404)

    await user.remove()
    return web.json_response({}, status=204)
