"""
Copyright 2022 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of
conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to
endorse
   or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open
Source Initiative: http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""

__author__ = "EUROCONTROL (SWIM)"

from collections import defaultdict
from os import getenv
import logging.config
from pathlib import Path

import jinja2
import connexion
import yaml
from mongoengine import connect

from predicted_runway import config as cfg
from predicted_runway.routes.web import web_blueprint


def _configure_jinja(app):
    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(['templates']),
    ])

    return app


def _configure_logging():
    logging.config.dictConfig(cfg.LOGGING)


def _configure_mongo():
    connect(**cfg.MONGO)


def get_openapi_spec(openapi_path: Path) -> dict:
    """
    Evaluates the x-hidden attribute of the paths and prevents them from showing up in the OpenAPi
    specs page
    :return:
    """

    with open(openapi_path, 'r') as f:
        openapi = yaml.safe_load(f)

    hidden_endpoints = defaultdict(list)
    for path, methods in openapi["paths"].items():
        for method, endpoint in methods.items():
            if endpoint.get("x-hidden"):
                hidden_endpoints[path].append(method)

    for path, methods in hidden_endpoints.items():
        for method in methods:
            del openapi["paths"][path][method]

        if not openapi["paths"][path]:
            del openapi["paths"][path]

    return openapi


def create_app():
    connexion_app = connexion.App(__name__)

    connexion_app.add_api(Path('openapi.yml'), options={"serve_spec": False},)
    connexion_app.add_url_rule("/openapi.json",
                               endpoint="/api/0_1./api/0_1_openapi_json",
                               view_func=lambda: get_openapi_spec(openapi_path=Path('openapi.yml')))

    app = connexion_app.app

    app.register_blueprint(web_blueprint)

    app = _configure_jinja(app)

    app.secret_key = getenv('SECRET_KEY')

    _configure_logging()

    _configure_mongo()

    return app


if __name__ == '__main__':
    create_app().run('0.0.0.0', port=5000)
