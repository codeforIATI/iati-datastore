import os

from flask import Flask, redirect, url_for, send_from_directory
from flask.ext.rq import RQ
from flask.ext.heroku import Heroku
from flask_sslify import SSLify

from iatilib import db, redis


def create_app(**config):
    app = Flask('iatilib.frontend')

    app.config.update(config)

    Heroku(app)
    SSLify(app)

    if "REDISTOGO_URL" in os.environ:
        app.config.update({
            'RQ_DEFAULT_HOST': app.config["REDIS_HOST"],
            'RQ_DEFAULT_PORT': app.config["REDIS_PORT"],
            'RQ_DEFAULT_PASSWORD': app.config['REDIS_PASSWORD']
        })

    db.init_app(app)
    redis.init_app(app)

    RQ(app)

    @app.route('/')
    def homepage():
        return redirect(url_for('docs', path='api/'))

    @app.route('/error')
    def error():
        return redirect(url_for('docs', path='api/error/'))

    @app.route('/docs/<path:path>')
    def docs(path):
        folder = os.path.join(app.root_path, 'docs')
        if path.endswith('/'):
            path += 'index.html'
        return send_from_directory(folder, path)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'), 'favicon.ico')

    from .api1 import api

    app.register_blueprint(api, url_prefix="/api/1")
    return app
