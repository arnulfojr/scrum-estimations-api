from flask import Blueprint


HealthApp = Blueprint('health_check', __name__)


@HealthApp.route('/healthz', methods=['GET'])
def health_check(request):
    return {
        'status': 'OK',
    }
