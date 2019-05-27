from aiohttp import web

from estimations.app import EstimationsApp
from health import HealthApp
from organizations.app import OrganizationsApp
from settings.app import ACCESS_LOG_FORMAT, HOST, PORT
from users.app import UsersApp


App = web.Application()

# - register sub applications - #
App.add_subapp('/selfz', HealthApp)

App.add_subapp('/estimations', EstimationsApp)

App.add_subapp('/users', UsersApp)

App.add_subapp('/organizations', OrganizationsApp)


if __name__ == '__main__':
    web.run_app(App, host=HOST,
                port=PORT,
                access_log=ACCESS_LOG_FORMAT)
