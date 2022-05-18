from contextlib import contextmanager

from fabric import task


@contextmanager
def virtualenv(conn):
    with conn.cd('~/iatidatastoreclassic'):
        with conn.prefix('source .ve/bin/activate'):
            with conn.prefix('source env.sh'):
                yield


@task
def deploy(conn):
    with virtualenv(conn):
        # pull latest copy of code in version control
        conn.run('git pull origin main')
        # install dependencies
        conn.run('pip install -r requirements.txt')
        # run database migrations
        conn.run('iati db upgrade')
        # build the docs
        conn.run('iati build-docs')
        # create translations
        conn.run('(cd iati_datastore/iatilib && pybabel compile -d translations)')
        # build the query builder
        conn.run('iati build-query-builder --deploy-url https://datastore.codeforiati.org')
        # webserver
        conn.run('sudo /etc/init.d/uwsgi reload')
        # worker
        conn.run('sudo /bin/systemctl restart iatidatastoreclassic-iatidatastoreclassic')
