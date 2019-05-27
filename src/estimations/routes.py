from aiohttp import web
from aiohttp.web import RouteTableDef

from . import models
from .exc import ResourceAlreadyExists


routes = RouteTableDef()


@routes.route('GET', '/sequences')
async def get_all_sequences(request):
    sequences = await models.Sequence.all()

    return web.json_response([sequence.dump() for sequence in sequences],
                             status=200)


@routes.route('POST', '/sequences')
async def create_sequence(request):
    payload = await request.json()

    try:
        sequence = await models.Sequence.from_data(**payload)
    except ResourceAlreadyExists as e:
        return web.json_response({
            'message': str(e),
        }, status=422)

    return web.json_response(sequence.dump(), status=201)


@routes.route('GET', '/sequences/{name}')
async def get_sequence(request):
    name = request.match_info['name']
    if not name:
        return web.json_response({
            'message': 'Please provide a sequence identifier.',
        }, status=404)

    sequence = await models.Sequence.get(name)
    if not sequence:
        return web.json_response({
            'message': f'No sequence named {name} was found',
        }, status=404)

    return web.json_response(sequence.dump(), status=200)


@routes.route('DELETE', '/sequences/{name}')
async def remove_sequence(request):
    name = request.match_info['name']
    if not name:
        return web.json_response({
            'message': 'Please provide a sequence identifier.',
        }, status=404)

    sequence = await models.Sequence.get(name)
    if not sequence:
        return web.json_response({
            'message': f'No sequence named {name} was found',
        }, status=404)

    await sequence.remove()

    return web.json_response(None, status=204)


@routes.route('GET', '/sequences/{name}/values')
async def get_sequence_values(request):
    name = request.match_info['name']
    if not name:
        return web.json_response({
            'message': 'Please provide a sequence identifier.',
        }, status=404)

    sequence = await models.Sequence.get(name)
    if not sequence:
        return web.json_response({
            'message': f'No sequence named {name} was found',
        }, status=404)
    values = await models.Value.get_from_sequence(sequence)
