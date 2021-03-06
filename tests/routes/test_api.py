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
from unittest import mock

import pytest
from met_update_db import repo as met_repo

from predicted_runway.domain.models import RunwayPredictionOutput, RunwayProbability, \
    WindInputSource, RunwayConfigPredictionOutput, RunwayConfigProbability
from predicted_runway.routes.factory import RunwayPredictionInputFactory, \
    RunwayConfigPredictionInputFactory
from tests.conftest import get_airport_by_icao
from tests.routes import API_BASE_PATH
from tests.routes.utils import query_string_from_request_arguments

ARRIVALS_RUNWAY_PREDICTION_URL = API_BASE_PATH + '/arrivals/{destination_icao}/runway-prediction'
ARRIVALS_RUNWAY_PREDICTION_INPUT_URL = API_BASE_PATH + '/arrivals/{destination_icao}/runway-prediction-input'
ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL = API_BASE_PATH + '/arrivals/{destination_icao}/runway-config-prediction'
ARRIVALS_RUNWAY_CONFIG_PREDICTION_INPUT_URL = API_BASE_PATH + '/arrivals/{destination_icao}/runway-config-prediction-input'


@pytest.mark.parametrize('invalid_destination_icao', [
    'EBBR', 'invalid', 'EHA'
])
def test_arrivals_runway_prediction__invalid_destination_icao__returns_404(
    test_client, invalid_destination_icao
):
    request_args = {
        "origin_icao": 'EBBR',
        "timestamp": '1650751200',
        "wind_direction": 180.0,
        "wind_speed": 10.0
    }
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=invalid_destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data['detail'] == "destination_icao should be one of EHAM, LEMD, LFPO, LOWW"


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {},
        "Missing query parameter 'origin_icao'"
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        "Missing query parameter 'timestamp'"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": 'invalid'
        },
        "Wrong type, expected 'integer' for query parameter 'timestamp'"
    ),
    (
        {
            "origin_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        "{'origin_icao': ['origin_icao should be different from destination_icao']}"
    ),
    (
        {
            "origin_icao": 'invalid',
            "timestamp": '1650751200'
        },
        "{'origin_icao': ['Should be a string of 4 characters.']}"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        "Wrong type, expected 'number' for query parameter 'wind_direction'"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        "{'wind_direction': ['Should be between 0 and 360.']}"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        "{'wind_direction': ['Should be between 0 and 360.']}"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        "Wrong type, expected 'number' for query parameter 'wind_speed'"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        "{'wind_speed': ['Should be positive.']}"
    ),
])
def test_arrivals_runway_prediction__invalid_input__returns_400(
    test_client, request_args, expected_message
):
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 400

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


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
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_arrivals_runway_prediction__met_not_available__returns_409(
    mock_create, test_client, request_args, expected_message
):
    mock_create.side_effect = met_repo.METNotAvailable()

    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
        },
        "Something went wrong during the prediction. Please try again later."
    )
])
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__prediction_error__returns_500(
    mock_get_runway_prediction_output, test_client, request_args, expected_message
):
    mock_get_runway_prediction_output.side_effect = Exception()

    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 500

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


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
        {'prediction_input': {'destination_icao': 'EHAM',
                              'origin_icao': 'EBBR',
                              'timestamp': 1650751200,
                              'wind_direction': 180.0,
                              'wind_input_source': 'USER',
                              'wind_speed': 10.0},
         'prediction_output': {'features': [{'geometry': {'coordinates': [[4.737225277777778,
                                                                           52.289105],
                                                                          [4.776925,
                                                                           52.30435111111111]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.4,
                                                            'runway_name': '6',
                                                            'true_bearing': 57.92},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.74003,
                                                                           52.33139722222223],
                                                                          [4.737683333333333,
                                                                           52.30583055555555]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.3,
                                                            'runway_name': '18C',
                                                            'true_bearing': 183.22},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.737683333333333,
                                                                           52.30583055555555],
                                                                          [4.74003,
                                                                           52.33139722222223]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.3,
                                                            'runway_name': '36C',
                                                            'true_bearing': 3.22},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.776925,
                                                                           52.30435111111111],
                                                                          [4.737225277777778,
                                                                           52.289105]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.001,
                                                            'runway_name': '24',
                                                            'true_bearing': 237.95},
                                             'type': 'Feature'}],
                               'type': 'FeatureCollection'}}
    )
])
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__no_errors__returns_200_and_output(
    mock_get_runway_prediction_output,
    test_client,
    destination_icao,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output

    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_result


@pytest.mark.parametrize('destination_icao, request_args, wind_input, prediction_output, expected_result', [
    (
        'EHAM',
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200',
            "wind_direction": 180.0,
            "wind_speed": 10.0
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
        {'prediction_input': {'destination_icao': 'EHAM',
                              'origin_icao': 'EBBR',
                              'timestamp': 1650751200,
                              'wind_direction': 180.0,
                              'wind_input_source': 'TAF',
                              'wind_speed': 10.0},
         'prediction_output': {'features': [{'geometry': {'coordinates': [[4.737225277777778,
                                                                           52.289105],
                                                                          [4.776925,
                                                                           52.30435111111111]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.4,
                                                            'runway_name': '6',
                                                            'true_bearing': 57.92},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.74003,
                                                                           52.33139722222223],
                                                                          [4.737683333333333,
                                                                           52.30583055555555]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.3,
                                                            'runway_name': '18C',
                                                            'true_bearing': 183.22},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.737683333333333,
                                                                           52.30583055555555],
                                                                          [4.74003,
                                                                           52.33139722222223]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.3,
                                                            'runway_name': '36C',
                                                            'true_bearing': 3.22},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[4.776925,
                                                                           52.30435111111111],
                                                                          [4.737225277777778,
                                                                           52.289105]],
                                                          'type': 'LineString'},
                                             'properties': {'probability': 0.001,
                                                            'runway_name': '24',
                                                            'true_bearing': 237.95},
                                             'type': 'Feature'}],
                               'type': 'FeatureCollection'}}
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_arrivals_runway_prediction__no_errors__wind_input_from_taf__returns_200_and_output(
    mock_get_runway_prediction_output,
    mock__handle_wind_input,
    test_client,
    destination_icao,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input

    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_URL.format(destination_icao=destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_result


@pytest.mark.parametrize('invalid_destination_icao', [
    'EBBR', 'invalid', 'EHA'
])
def test_arrivals_runway_config_prediction__invalid_destination_icao__returns_404(
    test_client, invalid_destination_icao
):
    request_args = {
        "timestamp": '1650751200',
        "wind_direction": 180.0,
        "wind_speed": 10.0
    }
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=invalid_destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data['detail'] == "destination_icao should be one of EHAM, LEMD, LFPO, LOWW"


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {},
        "Missing query parameter 'timestamp'"
    ),
    (
        {
            "timestamp": 'invalid'
        },
        "Wrong type, expected 'integer' for query parameter 'timestamp'"
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        "Wrong type, expected 'number' for query parameter 'wind_direction'"
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        "{'wind_direction': ['Should be between 0 and 360.']}"
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        "{'wind_direction': ['Should be between 0 and 360.']}"
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": "180",
            "wind_speed": "invalid"
        },
        "Wrong type, expected 'number' for query parameter 'wind_speed'"
    ),
    (
        {
            "timestamp": '1650751200',
            "wind_direction": 180,
            "wind_speed": -1
        },
        "{'wind_speed': ['Should be positive.']}"
    ),
])
def test_arrivals_runway_config_prediction__invalid_input__returns_400(
    test_client, request_args, expected_message
):
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 400

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch.object(RunwayConfigPredictionInputFactory, 'create')
def test_arrivals_runway_config_prediction__met_not_available__returns_409(
    mock_create, test_client, request_args, expected_message
):
    mock_create.side_effect = met_repo.METNotAvailable()

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao='EHAM')
    query_string = query_string_from_request_arguments(request_args)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


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
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__prediction_error__returns_500(
    mock_get_runway_config_prediction_output, test_client, request_args, expected_message
):
    mock_get_runway_config_prediction_output.side_effect = Exception()

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao='EHAM')
    query_string = query_string_from_request_arguments(request_args)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 500

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


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
        {'prediction_input': {'destination_icao': 'EHAM',
                              'timestamp': 1650751200,
                              'wind_direction': 180.0,
                              'wind_input_source': 'USER',
                              'wind_speed': 10.0},
         'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778,
                                                                            52.289105],
                                                                           [4.776925,
                                                                            52.30435111111111]],
                                                                          [[4.776925,
                                                                            52.30435111111111],
                                                                           [4.737225277777778,
                                                                            52.289105]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.6,
                                                            'runways': [{'name': '6',
                                                                         'true_bearing': 57.92},
                                                                        {'name': '24',
                                                                         'true_bearing': 237.95}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.74003,
                                                                            52.33139722222223],
                                                                           [4.737683333333333,
                                                                            52.30583055555555]],
                                                                          [[4.737683333333333,
                                                                            52.30583055555555],
                                                                           [4.74003,
                                                                            52.33139722222223]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.3,
                                                            'runways': [{'name': '18C',
                                                                         'true_bearing': 183.22},
                                                                        {'name': '36C',
                                                                         'true_bearing': 3.22}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.776925,
                                                                            52.30435111111111],
                                                                           [4.737225277777778,
                                                                            52.289105]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.1,
                                                            'runways': [{'name': '24',
                                                                         'true_bearing': 237.95}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.74003,
                                                                            52.33139722222223],
                                                                           [4.737683333333333,
                                                                            52.30583055555555]],
                                                                          [[4.737225277777778,
                                                                            52.289105],
                                                                           [4.776925,
                                                                            52.30435111111111]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.001,
                                                            'runways': [{'name': '18C',
                                                                         'true_bearing': 183.22},
                                                                        {'name': '6',
                                                                         'true_bearing': 57.92}]},
                                             'type': 'Feature'}],
                               'type': 'FeatureCollection'}}
    )
])
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__no_errors__returns_200_and_output(
    mock_get_runway_config_prediction_output,
    test_client,
    destination_icao,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_config_prediction_output.return_value = prediction_output

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_result


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
        {'prediction_input': {'destination_icao': 'EHAM',
                              'timestamp': 1650751200,
                              'wind_direction': 180.0,
                              'wind_input_source': 'TAF',
                              'wind_speed': 10.0},
         'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778,
                                                                            52.289105],
                                                                           [4.776925,
                                                                            52.30435111111111]],
                                                                          [[4.776925,
                                                                            52.30435111111111],
                                                                           [4.737225277777778,
                                                                            52.289105]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.6,
                                                            'runways': [{'name': '6',
                                                                         'true_bearing': 57.92},
                                                                        {'name': '24',
                                                                         'true_bearing': 237.95}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.74003,
                                                                            52.33139722222223],
                                                                           [4.737683333333333,
                                                                            52.30583055555555]],
                                                                          [[4.737683333333333,
                                                                            52.30583055555555],
                                                                           [4.74003,
                                                                            52.33139722222223]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.3,
                                                            'runways': [{'name': '18C',
                                                                         'true_bearing': 183.22},
                                                                        {'name': '36C',
                                                                         'true_bearing': 3.22}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.776925,
                                                                            52.30435111111111],
                                                                           [4.737225277777778,
                                                                            52.289105]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.1,
                                                            'runways': [{'name': '24',
                                                                         'true_bearing': 237.95}]},
                                             'type': 'Feature'},
                                            {'geometry': {'coordinates': [[[4.74003,
                                                                            52.33139722222223],
                                                                           [4.737683333333333,
                                                                            52.30583055555555]],
                                                                          [[4.737225277777778,
                                                                            52.289105],
                                                                           [4.776925,
                                                                            52.30435111111111]]],
                                                          'type': 'MultiLineString'},
                                             'properties': {'probability': 0.001,
                                                            'runways': [{'name': '18C',
                                                                         'true_bearing': 183.22},
                                                                        {'name': '6',
                                                                         'true_bearing': 57.92}]},
                                             'type': 'Feature'}],
                               'type': 'FeatureCollection'}}
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_arrivals_runway_config_prediction__no_errors__wind_input_from_taf__returns_200_and_output(
    mock_get_runway_config_prediction_output,
    mock__handle_wind_input,
    test_client,
    destination_icao,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_config_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_URL.format(destination_icao=destination_icao)
    query_string = query_string_from_request_arguments(request_args)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_result


@pytest.mark.parametrize('invalid_destination_icao', [
    'EBBR', 'invalid', 'EHA'
])
def test_arrivals_runway_prediction_input__invalid_destination_icao__returns_404(
    test_client, invalid_destination_icao
):
    request_args = {
        "origin_icao": 'EBBR',
        "timestamp": '1650751200',
    }
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_INPUT_URL.format(destination_icao=invalid_destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data['detail'] == "destination_icao should be one of EHAM, LEMD, LFPO, LOWW"


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {},
        "Missing query parameter 'origin_icao'"
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        "Missing query parameter 'timestamp'"
    ),
    (
        {
            "origin_icao": 'EBBR',
            "timestamp": 'invalid'
        },
        "Wrong type, expected 'integer' for query parameter 'timestamp'"
    ),
    (
        {
            "origin_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        "{'origin_icao': ['origin_icao should be different from destination_icao']}"
    ),
    (
        {
            "origin_icao": 'invalid',
            "timestamp": '1650751200'
        },
        "{'origin_icao': ['Should be a string of 4 characters.']}"
    ),
])
def test_arrivals_runway_prediction_input__invalid_query_args__returns_400(
    test_client, request_args, expected_message
):
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_INPUT_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 400

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


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
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_arrivals_runway_prediction_input__met_not_available__returns_409(
    mock_create, test_client, request_args, expected_message
):
    mock_create.side_effect = met_repo.METNotAvailable()

    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_PREDICTION_INPUT_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


@pytest.mark.parametrize('destination_icao, query_args, wind_input, expected_prediction_input', [
    (
        'EHAM',
        {
            "origin_icao": 'EBBR',
            "timestamp": '1650751200'
        },
        (180.0, 10.0, WindInputSource.TAF),
        {
            "origin_icao": "EBBR",
            "destination_icao": "EHAM",
            "timestamp": 1650751200,
            "wind_direction": 180,
            "wind_speed": 10,
            "wind_input_source": WindInputSource.TAF.value
        }
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
def test_arrivals_runway_prediction_input__no_errors__returns_prediction_input(
        mock_handle_wind_input,
        test_client,
        destination_icao,
        query_args,
        wind_input,
        expected_prediction_input
):
    mock_handle_wind_input.return_value = wind_input

    query_string = query_string_from_request_arguments(query_args)
    url = ARRIVALS_RUNWAY_PREDICTION_INPUT_URL.format(destination_icao=destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_prediction_input


@pytest.mark.parametrize('invalid_destination_icao', [
    'EBBR', 'invalid', 'EHA'
])
def test_arrivals_runway_config_prediction_input__invalid_destination_icao__returns_404(
    test_client, invalid_destination_icao
):
    request_args = {
        "timestamp": '1650751200',
        "wind_direction": 180.0,
        "wind_speed": 10.0
    }
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_INPUT_URL.format(destination_icao=invalid_destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data['detail'] == "destination_icao should be one of EHAM, LEMD, LFPO, LOWW"


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {},
        "Missing query parameter 'timestamp'"
    ),
    (
        {
            "timestamp": 'invalid'
        },
        "Wrong type, expected 'integer' for query parameter 'timestamp'"
    ),
])
def test_arrivals_runway_config_prediction_input__invalid_query_args__returns_400(
    test_client, request_args, expected_message
):
    query_string = query_string_from_request_arguments(request_args)
    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_INPUT_URL.format(destination_icao='EHAM')

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 400

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch.object(RunwayConfigPredictionInputFactory, 'create')
def test_arrivals_runway_config_prediction_input__met_not_available__returns_409(
    mock_create, test_client, request_args, expected_message
):
    mock_create.side_effect = met_repo.METNotAvailable()

    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_INPUT_URL.format(destination_icao='EHAM')
    query_string = query_string_from_request_arguments(request_args)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data['detail'] == expected_message


@pytest.mark.parametrize('destination_icao, query_args, wind_input, expected_prediction_input', [
    (
        'EHAM',
        {
            "timestamp": '1650751200'
        },
        (180.0, 10.0, WindInputSource.TAF),
        {
            "destination_icao": "EHAM",
            "timestamp": 1650751200,
            "wind_direction": 180,
            "wind_speed": 10,
            "wind_input_source": WindInputSource.TAF.value
        }
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
def test_arrivals_runway_config_prediction_input__no_errors__returns_prediction_input(
        mock_handle_wind_input,
        test_client,
        destination_icao,
        query_args,
        wind_input,
        expected_prediction_input
):
    mock_handle_wind_input.return_value = wind_input

    query_string = query_string_from_request_arguments(query_args)
    url = ARRIVALS_RUNWAY_CONFIG_PREDICTION_INPUT_URL.format(destination_icao=destination_icao)

    response = test_client.get(f"{url}{query_string}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_prediction_input

