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

from unittest import mock

import pytest
from met_update_db import repo as met_repo

from predicted_runway import routes
from predicted_runway.adapters.airports import get_destination_airports, get_airport_by_icao
from predicted_runway.domain.models import WindInputSource, RunwayPredictionOutput, \
    RunwayProbability, RunwayConfigPredictionOutput, RunwayConfigProbability
from predicted_runway.routes.factory import RunwayPredictionInputFactory, \
    RunwayConfigPredictionInputFactory
from tests.routes.utils import query_string_from_request_arguments

ARRIVALS_RUNWAY_PREDICTION_URL = '/arrivals/{destination_icao}/runway-prediction'
ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL = '/arrivals/{destination_icao}/runway-config-prediction'


def mock_get_model_stats(airport_icao: str):
    return {'stats': {}}


@pytest.mark.parametrize('request_body, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'origin_icao': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "origin_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['origin_icao should be different from destination_icao']}"
        ]
    ),
    (
        {
            "origin_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        [
            "{'wind_speed': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        [
            "{'wind_speed': ['Should be positive.']}"
        ]
    ),
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
def test_arrivals_runway_prediction__post__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_body,
    expected_messages
):
    destination_icao='EHAM'
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_arrivals_runway_prediction__post__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_body,
    expected_message
):
    destination_icao = 'EHAM'
    mock_create.side_effect = met_repo.METNotAvailable()
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body', [
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_input_source": WindInputSource.USER.value,
            "wind_direction": 180.0,
            "wind_speed": 10.0
        }
    )
])
@mock.patch('flask.redirect')
def test_arrivals_runway_prediction__post__no_errors__redirects_to_get_endpoint(
    mock_redirect,
    test_client,
    request_body,
):
    destination_icao = 'EHAM'
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    query_string = query_string_from_request_arguments(request_body)

    mock_redirect.assert_called_once_with(f"{url}{query_string}")


@pytest.mark.parametrize('request_args, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'origin_icao': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "origin_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['origin_icao should be different from destination_icao']}"
        ]
    ),
    (
        {
            "origin_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        [
            "{'wind_speed': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        [
            "{'wind_speed': ['Should be positive.']}"
        ]
    ),
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
def test_arrivals_runway_prediction__get__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_messages
):
    destination_icao = 'EHAM'
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    query_string = query_string_from_request_arguments(request_args)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.get(f"{url}{query_string}")

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_arrivals_runway_prediction__get__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_message
):
    destination_icao = 'EHAM'

    mock_create.side_effect = met_repo.METNotAvailable()
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        "Something went wrong during the prediction. Please try again later."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__get__prediction_error__renders_template_with_warning(
    mock_get_runway_prediction_output,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_message
):
    destination_icao = 'EHAM'
    mock_get_runway_prediction_output.side_effect = Exception()
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('destination_icao, request_args, prediction_output, expected_result', [
    (
        'EHAM',
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        RunwayPredictionOutput(
            probas=[
                RunwayProbability(
                    runway_name='18C',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='36C',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='6',
                    value=0.4
                ),
                RunwayProbability(
                    runway_name='24',
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EHAM')
        ),
        {'prediction_input': {'origin_icao': 'EBBR', 'destination_icao': 'EHAM', 'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'wind_input_source': 'from USER', 'wind_direction': 180.0, 'wind_speed': 10.0}, 'prediction_output': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'runway_name': '6', 'probability': 0.4, 'true_bearing': 57.92}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737225277777778, 52.289105], [4.776925, 52.30435111111111]]}}, {'type': 'Feature', 'properties': {'runway_name': '18C', 'probability': 0.3, 'true_bearing': 183.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.74003, 52.33139722222223], [4.737683333333333, 52.30583055555555]]}}, {'type': 'Feature', 'properties': {'runway_name': '36C', 'probability': 0.3, 'true_bearing': 3.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737683333333333, 52.30583055555555], [4.74003, 52.33139722222223]]}}]}, 'airport_coordinates': [4.7638897896, 52.3086013794]}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__get__no_errors__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    test_client,
    monkeypatch,
    destination_icao,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('destination_icao, request_args, wind_input, prediction_output, expected_result', [
    (
        'EHAM',
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
        },
        (180.0, 10.0, WindInputSource.TAF),
        RunwayPredictionOutput(
            probas=[
                RunwayProbability(
                    runway_name='18C',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='36C',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='6',
                    value=0.4
                ),
                RunwayProbability(
                    runway_name='24',
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EHAM')
        ),
        {'prediction_input': {'origin_icao': 'EBBR', 'destination_icao': 'EHAM', 'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'wind_input_source': 'from TAF', 'wind_direction': 180.0, 'wind_speed': 10.0}, 'prediction_output': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'runway_name': '6', 'probability': 0.4, 'true_bearing': 57.92}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737225277777778, 52.289105], [4.776925, 52.30435111111111]]}}, {'type': 'Feature', 'properties': {'runway_name': '18C', 'probability': 0.3, 'true_bearing': 183.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.74003, 52.33139722222223], [4.737683333333333, 52.30583055555555]]}}, {'type': 'Feature', 'properties': {'runway_name': '36C', 'probability': 0.3, 'true_bearing': 3.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737683333333333, 52.30583055555555], [4.74003, 52.33139722222223]]}}]}, 'airport_coordinates': [4.7638897896, 52.3086013794]}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__get__no_errors__wind_input_from_taf__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock__handle_wind_input,
    mock_render_template,
    test_client,
    monkeypatch,
    destination_icao,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        [
            "{'wind_speed': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        [
            "{'wind_speed': ['Should be positive.']}"
        ]
    ),
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
def test_arrivals_runway_config_prediction__post__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_body,
    expected_messages
):
    destination_icao = 'EHAM'

    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body, expected_message', [
    (
        {
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayConfigPredictionInputFactory, 'create')
def test_arrivals_runway_config_prediction__post__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_body,
    expected_message
):
    destination_icao = 'EHAM'

    mock_create.side_effect = met_repo.METNotAvailable()

    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body', [
    (
        {
            "timestamp": '1650751200',
            "wind_input_source": WindInputSource.USER.value,
            "wind_direction": 180.0,
            "wind_speed": 10.0
        }
    )
])
@mock.patch('flask.redirect')
def test_arrivals_runway_config_prediction__post__no_errors__redirects_to_get_endpoint(
    mock_redirect,
    test_client,
    monkeypatch,
    request_body,
):
    destination_icao = 'EHAM'
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    test_client.post(url, data=request_body)

    query_string = query_string_from_request_arguments(request_body)

    mock_redirect.assert_called_once_with(f"{url}{query_string}")


@pytest.mark.parametrize('request_args, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        [
            "{'wind_speed': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        [
            "{'wind_speed': ['Should be positive.']}"
        ]
    ),
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
def test_arrivals_runway_config_prediction__get__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_messages
):
    destination_icao = 'EHAM'

    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayConfigPredictionInputFactory, 'create')
def test_arrivals_runway_config_prediction__get__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_message
):
    destination_icao = 'EHAM'

    mock_create.side_effect = met_repo.METNotAvailable()

    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        "Something went wrong during the prediction. Please try again later."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__get__prediction_error__renders_template_with_warning(
    mock_get_runway_config_prediction_output,
    mock_flash,
    mock_render_template,
    test_client,
    monkeypatch,
    request_args,
    expected_message
):
    destination_icao = 'EHAM'

    mock_get_runway_config_prediction_output.side_effect = Exception()

    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('destination_icao, request_args, prediction_output, expected_result', [
    (
        'EHAM',
        {
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        RunwayConfigPredictionOutput(
            probas=[
                RunwayConfigProbability(
                    runway_config="('18C', '36C')",
                    value=0.3
                ),
                RunwayConfigProbability(
                    runway_config="('6', '24')",
                    value=0.6
                ),
                RunwayConfigProbability(
                    runway_config="('24',)",
                    value=0.1
                ),
                RunwayConfigProbability(
                    runway_config="('18C', '6')",
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EHAM')
        ),
        {'airport_coordinates': [4.7638897896, 52.3086013794],'prediction_input': {'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'destination_icao': 'EHAM', 'wind_direction': 180.0, 'wind_input_source': 'from USER', 'wind_speed': 10.0},'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778, 52.289105],[4.776925, 52.30435111111111]], [[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.6, 'runways': [{'name': '6','true_bearing': 57.92}, {'name': '24','true_bearing': 237.95}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.74003, 52.33139722222223],[4.737683333333333, 52.30583055555555]], [[4.737683333333333, 52.30583055555555],[4.74003, 52.33139722222223]]], 'type': 'MultiLineString'},'properties': {'probability': 0.3, 'runways': [{'name': '18C','true_bearing': 183.22}, {'name': '36C','true_bearing': 3.22}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.1, 'runways': [{'name': '24','true_bearing': 237.95}]},'type': 'Feature'}],'type': 'FeatureCollection'}}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__get__no_errors__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    test_client,
    monkeypatch,
    destination_icao,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('destination_icao, request_args, wind_input, prediction_output, expected_result', [
    (
        'EHAM',
        {
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        (180.0, 10.0, WindInputSource.TAF),
        RunwayConfigPredictionOutput(
            probas=[
                RunwayConfigProbability(
                    runway_config="('18C', '36C')",
                    value=0.3
                ),
                RunwayConfigProbability(
                    runway_config="('6', '24')",
                    value=0.6
                ),
                RunwayConfigProbability(
                    runway_config="('24',)",
                    value=0.1
                ),
                RunwayConfigProbability(
                    runway_config="('18C', '6')",
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EHAM')
        ),
        {'airport_coordinates': [4.7638897896, 52.3086013794],'prediction_input': {'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'destination_icao': 'EHAM', 'wind_direction': 180.0, 'wind_input_source': 'from TAF', 'wind_speed': 10.0},'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778, 52.289105],[4.776925, 52.30435111111111]], [[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.6, 'runways': [{'name': '6','true_bearing': 57.92}, {'name': '24','true_bearing': 237.95}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.74003, 52.33139722222223],[4.737683333333333, 52.30583055555555]], [[4.737683333333333, 52.30583055555555],[4.74003, 52.33139722222223]]], 'type': 'MultiLineString'},'properties': {'probability': 0.3, 'runways': [{'name': '18C','true_bearing': 183.22}, {'name': '36C','true_bearing': 3.22}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.1, 'runways': [{'name': '24','true_bearing': 237.95}]},'type': 'Feature'}],'type': 'FeatureCollection'}}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__get__no_errors__wind_input_from_taf__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock__handle_wind_input,
    mock_render_template,
    test_client,
    monkeypatch,
    destination_icao,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input
    monkeypatch.setattr(routes.web, 'get_model_stats', mock_get_model_stats)

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{url}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        model_stats=mock_get_model_stats(destination_icao),
        destination_airport=get_airport_by_icao(destination_icao),
        destination_airports=get_destination_airports()
    )
