from aiohttp import web
from aiohttp.web import Application

from users.routes import router


@web.middleware
async def json_middleware(request, handler):
    if request.method != 'GET' and 'json' not in request.content_type:
        return web.json_response({
            'message': 'This is a JSON based API, please use only JSON for requests.',
        }, status=400)

    return await handler(request)


UsersApp = Application(
    middlewares=[
        json_middleware,
    ],
)

UsersApp.add_routes(router)
