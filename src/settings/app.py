import os


SERVICE_NAME = os.getenv('SERVICE_NAME')

HOSTNAME = HOST = os.getenv('HOSTNAME')

PORT = int(os.getenv('PORT', 5000))

ACCESS_LOG_FORMAT = '%a %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
