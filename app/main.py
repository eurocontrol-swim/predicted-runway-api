from os import getenv
import logging
from pathlib import Path

import jinja2
import connexion

from app.routes.web import web_blueprint


logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app():

    connexion_app = connexion.App(__name__)

    connexion_app.add_api(Path('openapi.yml'))

    app = connexion_app.app
    my_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(['templates']),
    ])
    app.jinja_loader = my_loader

    app.logger = logger
    app.secret_key = getenv('SECRET_KEY')

    app.register_blueprint(web_blueprint)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Frontend started up.')

    return app
