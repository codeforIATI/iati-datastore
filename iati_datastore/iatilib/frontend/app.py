from flask import Flask, render_template, request
from flask_babel import Babel
from flask_cors import CORS

from iatilib import db, rq, migrate

from .api1 import api
from .builder import builder
from iatilib.frontend.routes import routes
from iatilib.crawler import manager as crawler_manager
from iatilib.queue import manager as queue_manager


def create_app(config_object='iatilib.config.Config'):
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    babel = Babel(app, configure_jinja=False)
    babel.localeselector(get_locale)
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


def register_blueprints(app):
    app.register_blueprint(routes, url_prefix="")
    app.register_blueprint(builder, url_prefix="/build/api/1/access")
    app.register_blueprint(api, url_prefix="/api/1")
    app.register_blueprint(crawler_manager)
    app.register_blueprint(queue_manager)


def register_extensions(app):
    db.init_app(app)
    rq.init_app(app)
    CORS(app)
    migrate.init_app(app, db)


def register_error_handlers(app):
    app.register_error_handler(
        404, lambda x: (render_template('error/404.html'), 404))
    for code in (500, 501, 502, 503, 504):
        app.register_error_handler(
            code, lambda x: (render_template('error/5xx.html'), code))


def get_locale():
    return request.args.get("locale", "en")
