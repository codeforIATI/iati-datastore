IATI Datastore Classic
======================

[![Build Status](https://img.shields.io/github/workflow/status/codeforIATI/iati-datastore/CI/main.svg)](https://github.com/codeforIATI/iati-datastore/actions?query=workflow%3ACI)
[![Coverage Status](https://img.shields.io/coveralls/codeforIATI/iati-datastore.svg)](https://coveralls.io/r/codeforIATI/iati-datastore?branch=main)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue.svg)](https://github.com/codeforIATI/iati-datastore/blob/main/LICENSE.txt)


Introduction
------------

The International Aid Transparency Initiative (IATI) aims to make
information about aid spending easier to access.

IATI maintains the [IATI Standard](https://iatistandard.org) and keeps a
[Registry of IATI data](https://iatiregistry.org/).

The *IATI Datastore* was originally built in 2013 by the
[Open Knowledge Foundation](https://okfn.org).
[Code for IATI](https://codeforiati.org) has updated the
software to use Python3 and modern dependencies.
Over time, we will include other bugfixes and feature
improvements. Our fork of the software is called *IATI Datastore Classic*.

A public instance is available here:

https://datastore.codeforiati.org


Requirements
------------

You will need [Redis](https://redis.io), [Postgres](https://postgresql.org), Python 3, pip and develpment libraries (for libpq, libxml2 and libxslt) to run the full setup.
For example, on Ubuntu:

    sudo apt-get install postgresql redis-server python3 python3-pip libpq-dev libxml2-dev libxslt-dev libevent-dev python3-dev

Installing for development
--------------------------

```
# Clone the source
git clone https://github.com/codeforIATI/iati-datastore.git

# Install development dependencies
pip install -r requirements_dev.txt

# Run the tests  (these tests use an in-memory sqlite db)
pytest

# Create a new PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE iati_datastore"

# Set an environment variable for `IATI_DATASTORE_DATABASE_URL` linking to the database created
export IATI_DATASTORE_DATABASE_URL=postgres:///iati_datastore

# Create the db tables
iati db upgrade

# Note: To create the tables the new database may need access privileges granted to your system user
# See http://dba.stackexchange.com/questions/117109/how-to-manage-default-privileges-for-users-on-a-database-vs-schema/117661#117661
sudo -u postgres psql -c "CREATE USER [SYSTEM USER]"
sudo -u postgres psql -c "GRANT ALL ON DATABASE iati_datastore TO [SYSTEM USER]"

# Create the front page
iati build-query-builder --deploy-url=http://127.0.0.1:5000

# Start the process of grabbing the source data
iati crawler download-and-update

# Start a development server – this should be run in a seperate terminal window
iati run

# Run a worker. This will download and index the datafiles
iati queue background

# The progess of the worker can be checked using:
iati crawler status

# A local API is available at: http://127.0.0.1:5000
```

Development with vagrant
------------------------

A Vagrant box is also provided. `vagrant up` as normal, then `vagrant ssh`.


```
# Run the tests  (these tests use an in-memory sqlite db)
pytest

# Create the db tables
iati db upgrade

# Create the front page
iati build-query-builder --deploy-url=http://127.0.0.1:5000

# Start the process of grabbing the source data
iati crawler download-and-update

# Start a development server – this should be run in a seperate terminal window
iati run --host 0.0.0.0

# Run a worker. This will download and index the datafiles
iati queue background

# The progess of the worker can be checked using:
iati crawler status

# A local API is available at: http://127.0.0.1:5000
```


Deploying with nginx
--------------------

* Intall the requirements listed above
* Install nginx

        sudo apt-get install nginx

* Install uwsgi, from within your `virtualenv`

        pip3 install uwsgi

* Create a uwSGI .ini file inside the root `iati-datastore` folder, e.g.

        [uwsgi]
        module = liveserver
        master = true
        processes = 5
        socket = /var/www/socks/%n.sock
        logto = /var/log/uwsgi/%n.log
        chmod-socket = 666
        vacuum = true
        die-on-term = true

* Make sure `/var/www/socks/` and `/var/log/uwsgi/` are writeable by the `www-data` user.

* Add a `liveserver.py` file, according to your server configuration:

        import sys, os
        PATH = os.path.dirname(os.path.realpath(__file__))
        sys.path.insert(0, '/path/to/iati-datastore/pyenv/lib/python3.6/site-packages')
        sys.path.insert(0, PATH)
        from iati_datastore.iatilib.wsgi import app as application

* Set up a systemd service, e.g. in `/etc/systemd/system/iati-datastore.service`

        [Unit]
        Description=IATI Datastore uWSGI instance
        After=network.target
        [Service]
        User=www-data
        Group=www-data
        WorkingDirectory=/path/to/iati-datastore/
        ExecStart=/path/to/iati-datastore/pyenv/bin/uwsgi --ini /path/to/iati-datastore/iati-datastore_uwsgi.ini
        [Install]
        WantedBy=multi-user.target


* Start the systemd service, e.g.:

        systemctl start iati-datastore

* Make sure that the service loads on restart:

        systemctl enable iati-datastore

* Create your nginx config file, e.g. in /etc/nginx/sites-available/datastore

        server {
            server_name datastore.codeforiati.org;
            gzip            on;
            gzip_types      text/plain application/xml text/css application/javascript application/json;
            gzip_min_length 1000;
            error_log  /var/www/logs/error.log;
            access_log /var/www/logs/access.log;

            error_page 404 /error/404.html;
            error_page 500 501 502 503 504 /error/5xx.html;
            location /error {
                root /path/to/iati-datastore/iati_datastore/iatilib/frontend/templates;
                internal;
            }

            location /docs {
                alias /path/to/iati-datastore/iati_datastore/iatilib/frontend/docs/dirhtml;
                expires 1y;
            }

            location / {
                uwsgi_intercept_errors on;
                include uwsgi_params;
                uwsgi_pass unix:/var/www/socks/iati-datastore_uwsgi.sock;
                uwsgi_buffering off;
            }
        }

* Load the config file and test nginx:

        cp /etc/nginx/sites-available/datastore /etc/nginx/sites-enabled/datastore
        nginx -t

* If everything worked out, restart nginx and your site should be available through your server (e.g. in the above configuration, via `datastore.codeforiati.org`:

        systemctl restart nginx


Deploying with apache
---------------------

* Install the requirements listed above
* Install Apache and mod_wsgi

        sudo apt-get install apache2 libapache2-mod-wsgi

* Clone the source
* Install `pip install -e iati_datastore`
* Create a database (in postgres), and set an environment variable
  `DATABASE_URL`. e.g.:

        sudo -u postgres createdb iati-datastore -O my_username -E utf-8
        export DATABASE_URL='postgres:///iati-datastore'

* Run `iati create_database` to create the db tables
* Set up a cron job for updates. (Add the following line after running `crontab -e`)

        0 0 * * * export DATABASE_URL='postgres:///iati-datastore'; /usr/local/bin/iati crawler download-and-update

* Run a worker with `iati queue background`
    - This needs to persist when you close your ssh connection. A simple way of doing this is using [screen](https://www.gnu.org/software/screen/).

* Set up apache using mod_wsgi

* Create a datastore.wsgi file containing this code (this is necessary because Apache's mod wsgi handles environment variables differently):

        import os
        os.environ['DATABASE_URL'] = 'postgres:///iati-datastore'
        from iatilib.wsgi import app as application

* Add this inside the `<VirtualHost>` tags of your apache configuration:

        WSGIDaemonProcess datastore user=my_username group=my_username
        WSGIProcessGroup datastore
        WSGIScriptAlias / /home/datastore/datastore.wsgi


Updating activities after changing import code
----------------------------------------------

* Restart background process
* Run `iati crawler download-and-update --ignore-hashes` This will force a full refresh

Generation of Documentation
---------------------------

API documentation in the docs folder is generated using [Sphinx](https://www.sphinx-doc.org).

    iati build-docs

Generation of the front page and query builder
----------------------------------------------

    iati build-query-builder

By default, the query builder will look for files served from http://127.0.0.1:5000 - if you would like to point it elsewhere (e.g. to https://datastore.codeforiati.org) then you should add the argument `deploy-url`:

    iati build-query-builder --deploy-url https://datastore.codeforiati.org
