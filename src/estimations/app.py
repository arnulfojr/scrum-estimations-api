from aiohttp.web import Application

from .routes import routes


EstimationsApp = Application()


EstimationsApp.router.add_routes(routes)
