import os


SERVICE_NAME = os.environ['SERVICE_NAME']

HOST = os.environ['HOSTNAME']

PORT = os.environ['PORT']

ACCESS_LOG_FORMAT = '%a %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
