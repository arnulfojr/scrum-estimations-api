from aiohttp.web import Application

from organizations.routes import router


OrganizationsApp = Application()

OrganizationsApp.add_routes(router)
