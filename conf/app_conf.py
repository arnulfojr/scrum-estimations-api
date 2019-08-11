import multiprocessing

from settings.app import HOSTNAME, PORT


workers = (multiprocessing.cpu_count() * 2) - 1

worker_class = 'sync'

bind = f'{HOSTNAME}:{PORT}'

threads = 2

max_requests = 100

max_requests_jitter = 5

accesslog = '-'

errorlog = '-'
