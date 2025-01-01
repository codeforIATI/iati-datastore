import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'IATI_DATASTORE_DATABASE_URL', 'postgresql:///iati-datastore')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    # Handle database disconnect error
    # https://stackoverflow.com/questions/55457069/how-to-fix-operationalerror-psycopg2-operationalerror-server-closed-the-conn
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    RQ_REDIS_URL = os.environ.get(
        'IATI_DATASTORE_REDIS_URL', 'redis://localhost:6379/0')

# Due to a nasty OSX bug, we have to prevent checking system for proxies...
# https://wefearchange.org/2018/11/forkmacos.rst.html
# https://stackoverflow.com/a/53047403/11841218
os.environ['no_proxy'] = '*'
