from aiohttp import web
from aiohttp.web import Request
from aiohttp.web import RouteTableDef

from organizations.models import Organization
from users.models import User

from . import helpers


router = RouteTableDef()


@router.route('GET', '/{org_id}')
async def get_organizations(request: Request):
    organization_id = request.match_info['org_id']
    organization = await helpers.fetch_organization(organization_id)
    if not organization:
        return web.json_response({
            'message': 'The organization does not exist.',
        }, status=404)

    return web.json_response(organization.dict_dump())


@router.route('POST', '/')
async def create_organization(request: Request):
    payload = await request.json()

    organization = await Organization.create_from(payload)

    data = organization.dict_dump()

    return web.json_response(data, status=201)


@router.route('PATCH', '/{org_id}')
async def update_organization(request: Request):
    organization_id = request.match_info['org_id']
    organization = await Organization.get(organization_id)

    if not organization:
        return web.json_response({
            'message': f'No organization with ID {organization_id} was found',
        }, status=404)

    data = await request.json()
    if data.get('name'):
        organization.name = data.get('name')

    await organization.update()

    return web.json_response(organization.dict_dump(),
                             status=200)


@router.route('POST', '/{org_id}/users')
async def add_user_to_organization(request: Request):
    org_id = request.match_info['org_id']
    organization = await Organization.get(org_id)
    if not organization:
        return web.json_response({
            'message': 'The given organization does not exist.',
        }, status=404)

    payload = await request.json()
    user = payload.get('user', dict())
    if not user:
        return web.json_response({
            'message': 'The request must contain a user.',
        }, status=400)

    user = await User.get(user.get('id'))
    if not user:
        return web.json_response({
            'message': 'The user does not exist.',
        }, status=404)

    user.organization = organization
    await user.put(only=('organization',))

    return web.json_response({
        'organization': organization.dict_dump(),
        'user': user.dict_dump(),
    }, status=201)


@router.route('DELETE', '/{org_id}/users/{user_id}')
async def remove_user_from_organization(request: Request):
    org_id = request.match_info['org_id']
    organization = await Organization.get(org_id)
    if not organization:
        return web.json_response({
            'message': 'The given organization does not exist.',
        }, status=404)

    user_id = request.match_info['user_id']
    user = await User.get(user_id)
    if not user:
        return web.json_response({
            'message': 'The user does not exist.',
        }, status=404)

    user.organization = None
    await user.put(only=('organization',))

    return web.json_response(None, status=204)
