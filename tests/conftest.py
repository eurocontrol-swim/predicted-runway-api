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

import json
import os
from pathlib import Path

import pytest

import predicted_runway
from predicted_runway.app import create_app
from predicted_runway.domain.factory import AirportFactory
from predicted_runway.domain.models import Airport


def pytest_generate_tests(metafunc):
    os.environ['SECRET_KEY'] = 'secret'


@pytest.fixture(scope='session')
def test_app():
    _app = create_app()
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='session')
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture(autouse=True)
def mock_airports(monkeypatch):
    monkeypatch.setattr(predicted_runway.adapters.airports, 'ICAO_AIRPORTS_CATALOG_PATH',
                        Path(__file__).parent.joinpath('static/airports.json').absolute())


def _get_airports_data():
    path = Path(__file__).parent.joinpath('static/airports.json')
    with open(path, 'r') as f:
        return json.load(f)


def get_airport_by_icao(icao: str) -> Airport:
    data = _get_airports_data()
    return AirportFactory.create_from_data(data[icao])
