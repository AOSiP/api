import os

class Config(object):

    UPSTREAM_URL = os.environ.get('UPSTREAM_URL', 'https://ota.aosiprom.com/builds.json')
    DOWNLOAD_BASE_URL = os.environ.get('DOWNLOAD_BASE_URL', 'https://get.aosiprom.com/')
