from flask import Flask
from app.config import TEMPLATES_DIR
from app.routes.web import web_blueprint
from app.routes.api import api_blueprint

from os import getenv
import logging

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, template_folder=TEMPLATES_DIR)
    app.logger = logger
    app.secret_key = getenv('SECRET_KEY')

    app.register_blueprint(web_blueprint)
    app.register_blueprint(api_blueprint)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Frontend started up.')

    return app
