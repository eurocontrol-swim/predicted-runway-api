from os import getenv
import logging
from pathlib import Path

import jinja2
import connexion

from predicted_runway.routes.web import web_blueprint


def _config_logging(app):
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
    app.logger = logging.getLogger(__name__)
    app.logger.setLevel(logging.INFO)

    return app


def _configure_jinja(app):
    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(['templates']),
    ])

    return app


def create_app():
    connexion_app = connexion.App(__name__)

    connexion_app.add_api(Path('openapi.yml'))

    app = connexion_app.app

    app.register_blueprint(web_blueprint)

    app = _configure_jinja(app)

    app = _config_logging(app)

    app.secret_key = getenv('SECRET_KEY')

    return app


if __name__ == '__main__':
    create_app().run('0.0.0.0', port=5000)
