from aiohttp import web


router = web.RouteTableDef()


@router.get('/healthz')
async def health_check(request):
    return web.json_response({
        'status': 'OK',
    })


HealthApp = web.Application()

HealthApp.add_routes(router)
