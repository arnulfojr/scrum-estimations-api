import os

from requests import Session


class EstimationsClient:
    def __init__(self, host: str, port: int, protocol: str = 'http'):
        self.host = host
        self.port = port
        self.protocol = protocol

    def __enter__(self):
        self.session = Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()

    def _build_url(self, path: str = ''):
        if not path:
            return f'{self.protocol}://{self.host}:{self.port}'
        if path.startswith('/'):
            path = path[1:]
        return f'{self.protocol}://{self.host}:{self.port}/{path}'

    def get(self, path: str, headers={}):
        url = self._build_url(path)
        return self.session.get(url, headers=headers)

    def post(self, path: str, data, headers: dict = {}):
        url = self._build_url(path)
        return self.session.post(url, json=data, headers=headers)

    def put(self, path: str, data, headers: dict = {}):
        url = self._build_url(path)
        return self.session.put(url, json=data, headers=headers)


def run():
    host = os.getenv('HOST')
    port = int(os.getenv('PORT', 5000))

    with EstimationsClient(host, port) as http_client:
        organization = create_organization('Captain America Organization', client=http_client)
        users = create_three_users_within(organization, client=http_client)

        sequence = create_fibonacci_sequence(client=http_client)
        session = create_estimation_session_for(organization, sequence, client=http_client)
        join_users_to_session(session, users, client=http_client)
        tasks = create_two_tasks_in_session(session, client=http_client)

    print(f'Organization: {organization["id"]}')
    [print(f'User: {user["id"]}') for user in users]
    print(f'Sequence: {sequence["name"]}')
    for value in sequence['values']:
        print(f'  Value({value["id"]}): {value["value"]}')
    print(f'Session: {session["id"]}')
    for task in tasks:
        print(f'  Task({task["id"]}): {task.get("name")}')


def create_organization(name: str, client):
    response = client.post('/organizations/', {
        'name': name,
    })

    return response.json()


def create_three_users_within(organization, client):
    users = list()
    for i in range(0, 3):
        users.append({
            'email': f'user_{i}@example.com',
            'password': f'user_{i}',
            'name': f'User {1}',
            'organization': organization['id'],
        })

    responses = [client.post('/users/', data=user) for user in users]
    return [response.json() for response in responses]


def create_fibonacci_sequence(client):
    sequence_data = {
        'name': 'Fibo',
    }

    response = client.post('/estimations/sequences/', data=sequence_data)
    sequence = response.json()

    values = [
        {
            'value': 1.0,
        },
        {
            'value': 0.0,
        },
        {
            'value': 2.0,
        },
        {
            'value': 3.0,
        },
        {
            'value': 5.0,
        },
        {
            'value': 7.0,
        },
        {
            'name': '?',
        },
        {
            'name': 'Coffee',
        },
    ]
    client.post(f'/estimations/sequences/{sequence["name"]}/values/', data=values)

    response = client.get(f'/estimations/sequences/{sequence["name"]}')

    return response.json()


def create_estimation_session_for(organization, sequence, client):
    data = {
        'organization': {
            'id': organization['id'],
        },
        'sequence': {
            'name': sequence['name'],
        },
        'name': 'Testing Session',
    }

    response = client.post('/estimations/sessions/', data=data)
    return response.json()


def join_users_to_session(session, users, client):
    for user in users:
        data = {
            'user': {
                'id': user['id'],
            },
        }
        client.put(f'/estimations/sessions/{session["id"]}/members/', data=data)


def create_two_tasks_in_session(session, client):
    tasks = list()
    for i in range(0, 2):
        data = {
            'name': f'Task-{i}',
        }
        response = client.post(f'/estimations/sessions/{session["id"]}/tasks/', data=data)
        if 200 <= response.status_code < 205:
            tasks.append(response.json())
    return tasks


if __name__ == '__main__':
    run()
