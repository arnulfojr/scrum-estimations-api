from aiohttp.web import Application

from users.routes import router


UsersApp = Application()

UsersApp.add_routes(router)
