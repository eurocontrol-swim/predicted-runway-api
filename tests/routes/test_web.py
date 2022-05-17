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
from datetime import datetime
from unittest import mock

import pytest

from predicted_runway.adapters.airports import get_destination_airports, get_airport_by_icao
from predicted_runway.adapters.met.api import METNotAvailable
from predicted_runway.domain.models import WindInputSource, RunwayPredictionOutput, \
    RunwayProbability, RunwayConfigPredictionOutput, RunwayConfigProbability
from predicted_runway.routes.factory import RunwayPredictionInputFactory, \
    RunwayConfigPredictionInputFactory
from tests.routes.utils import query_string_from_request_arguments

RUNWAY_PREDICTION_URL = f'/runway-prediction/arrivals'
RUNWAY_CONFIG_PREDICTION_URL = f'/runway-config-prediction/arrivals'
AIRPORTS_DATA_URL = '/airports-data'
FORECAST_TIMESTAMP_RANGE_URL = '/forecast-timestamp-range'


@pytest.mark.parametrize('request_body, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'origin_icao': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "origin_icao": 'EHAM',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['origin_icao should be different from destination_icao']}"
        ]
    ),
    (
        {
            "origin_icao": 'invalid',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'LGAV',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be one of EHAM, LEMD, LFPO, LOWW.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
def test_runway_prediction__post__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    request_body,
    expected_messages
):
    test_client.post(RUNWAY_PREDICTION_URL, data=request_body)

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )



@pytest.mark.parametrize('request_body, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_runway_prediction__post__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    request_body,
    expected_message
):
    mock_create.side_effect = METNotAvailable()

    test_client.post(RUNWAY_PREDICTION_URL, data=request_body)

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )



@pytest.mark.parametrize('request_body', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_input_source": WindInputSource.USER.value,
            "wind_direction": 180.0,
            "wind_speed": 10.0
        }
    )
])
@mock.patch('flask.redirect')
def test_runway_prediction__post__no_errors__redirects_to_get_endpoint(
    mock_redirect,
    test_client,
    request_body,
):
    test_client.post(RUNWAY_PREDICTION_URL, data=request_body)

    query_string = query_string_from_request_arguments(request_body)

    mock_redirect.assert_called_once_with(f"{RUNWAY_PREDICTION_URL}{query_string}")


@pytest.mark.parametrize('request_args, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'origin_icao': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
        },
        [
            "'timestamp': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "origin_icao": 'EHAM',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['origin_icao should be different from destination_icao']}"
        ]
    ),
    (
        {
            "origin_icao": 'invalid',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        [
            "{'origin_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'LGAV',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be one of EHAM, LEMD, LFPO, LOWW.']}"
        ]
    ),
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
def test_runway_prediction__get__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_messages
):

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_PREDICTION_URL}{query_string}")

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )



@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": '1650751200'
        },
        f"There is no meteorological information available for the provided timestamp. "
        f"Please try again with different value."
    )
])
@mock.patch('flask.render_template')
@mock.patch('flask.flash')
@mock.patch.object(RunwayPredictionInputFactory, 'create')
def test_runway_prediction__get__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_message
):
    mock_create.side_effect = METNotAvailable()


    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_PREDICTION_URL}{query_string}")

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
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
def test_runway_prediction__get__prediction_error__renders_template_with_warning(
    mock_get_runway_prediction_output,
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_message
):
    mock_get_runway_prediction_output.side_effect = Exception()

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_PREDICTION_URL}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, prediction_output, expected_result', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
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
        {'prediction_input': {'origin_icao': 'EBBR', 'destination_icao': 'EHAM', 'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'wind_input_source': 'from USER', 'wind_direction': 180.0, 'wind_speed': 10.0}, 'prediction_output': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'runway_name': '6', 'probability': 0.4, 'true_bearing': 57.92}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737225277777778, 52.289105], [4.776925, 52.30435111111111]]}}, {'type': 'Feature', 'properties': {'runway_name': '18C', 'probability': 0.3, 'true_bearing': 183.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.74003, 52.33139722222223], [4.737683333333333, 52.30583055555555]]}}, {'type': 'Feature', 'properties': {'runway_name': '36C', 'probability': 0.3, 'true_bearing': 3.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737683333333333, 52.30583055555555], [4.74003, 52.33139722222223]]}}]}, 'airport_coordinates': [4.7638897896, 52.3086013794], 'stats': {'datetime': '2022-05-03T15:39:39.237054', 'airport': 'EHAM', 'dataset_file': '../data/final/dataset_EHAM_20210101_20211231.csv', 'date_from': '20210101', 'date_to': '20211231', 'model_filepath': '../models/rwy_used/cross-val_results/2022.05.03/CV-Test_rwy_used_results_EHAM_2022.05.03.json', 'number_estimators': 100, 'criterion': 'entropy', 'Cross-Validation with metar': {'mean_f1_weighted': 0.780042987622147, 'mean_balanced_accuracy': 0.6361590292371322, 'mean_balanced_accuracy_over_random': 0.5841817476995796, 'mean_accuracy': 0.7831405218749101, 'mean_recall_weighted': 0.7831405218749101, 'mean_precision_weighted': 0.7787738190955145, 'mean_top_2': 0.9413837922591025, 'mean_roc_auc': 0.9561976561107486, 'log_loss_r_used': 11846.773328155332, 'parallel_f1_weighted': 0.8476892638977388, 'parallel_balanced_accuracy': 0.6422266721806317, 'parallel_balanced_accuracy_over_random': 0.5706720066167581, 'parallel_accuracy': 0.850948573082011, 'parallel_recall_weighted': 0.850948573082011, 'parallel_precision_weighted': 0.8458844321338811}, 'features_importance': [['wind_dir', 0.3926026694560875], ['origin_angle', 0.20885040038726355], ['wind_speed', 0.17676037409925724], ['hour', 0.1706949486387369], ['is_summer_season', 0.025919577590236484], ['is_workday', 0.025172029828418256]], 'raw_results': {'fit_time': [1.640192985534668, 1.6318044662475586, 1.6129686832427979, 2.6991095542907715, 2.3397216796875], 'score_time': [0.8006584644317627, 0.8389027118682861, 1.1165943145751953, 0.9337189197540283, 0.9231874942779541], 'test_f1_weighted': [0.7776808507099894, 0.7807152684686011, 0.7784415909487092, 0.7807001800996997, 0.7826770478837358], 'test_balanced_accuracy': [0.6303823151802099, 0.6353945237960066, 0.635033654451409, 0.6307177304972615, 0.6492669222607739], 'test_balanced_accuracy_over_random': [0.5775797887773828, 0.5833080271954361, 0.5828956050873246, 0.5779631205682989, 0.5991621968694558], 'test_accuracy': [0.7812935907789442, 0.783496072241392, 0.781513838925189, 0.7841568166801263, 0.7852422907488987], 'test_recall_weighted': [0.7812935907789442, 0.783496072241392, 0.781513838925189, 0.7841568166801263, 0.7852422907488987], 'test_precision_weighted': [0.7764091084807576, 0.7793222995314654, 0.7773378107190775, 0.7792519085868093, 0.7815479681594631], 'test_top_2': [0.9411937449526466, 0.9420747375376257, 0.93642170178401, 0.9440569708538287, 0.9431718061674009], 'test_roc_auc': [0.9557409816211943, 0.95751913707759, 0.9541903361184119, 0.9564386223537362, 0.9570992033828106], 'test_log_loss_r_used': [11504.416984901462, 11895.727958195888, 12579.319641032711, 11895.13540461226, 11359.266652034337], 'test_parallel_f1_weighted': [0.8474408631620386, 0.8484158026653088, 0.8429729126371531, 0.8497617027409732, 0.8498550382832196], 'test_parallel_bal_acc_sc': [0.6385601684277206, 0.6413004484718635, 0.6381487079558813, 0.6351152655438913, 0.6580087705038018], 'test_parallel_bal_acc_sc_over_random': [0.5662722021132647, 0.5695605381662362, 0.5657784495470576, 0.5621383186526696, 0.5896105246045622], 'test_parallel_acc_sc': [0.8514059173335291, 0.8513325012847809, 0.8463402099698994, 0.853094486454739, 0.8525697503671072], 'test_parallel_recall_score_weighted': [0.8514059173335291, 0.8513325012847809, 0.8463402099698994, 0.853094486454739, 0.8525697503671072], 'test_parallel_precision_score_weighted': [0.8455170892906669, 0.8464972023988727, 0.8411720945284004, 0.8477976070329777, 0.8484381674184877]}, 'features': ['hour', 'is_workday', 'is_summer_season', 'wind_speed', 'wind_dir', 'origin_angle'], 'test_with_metar': {'f1_weighted': 0.7843023387328663, 'balanced_accuracy': 0.6470626528884019, 'balanced_accuracy_over_rand': 0.5966430318724594, 'accuracy': 0.7867379302243628, 'recall_weighted': 0.7867379302243628, 'precision_weighted': 0.7829026422063982, 'top_2': 0.9463761306237519, 'roc_auc': 0.9585671812914206, 'log_loss_r_used': 14092.82353963447, 'parallel_f1_weighted': 0.8508089527639182, 'parallel_balanced_accuracy': 0.6562320408523248, 'parallel_balanced_accuracy_over_random': 0.5874784490227898, 'parallel_accuracy': 0.8532244802067426, 'parallel_recall_weighted': 0.8532244802067426, 'parallel_precision_weighted': 0.8491396822316221}, 'test_with_taf': {'f1_weighted': 0.5790502246484722, 'balanced_accuracy': 0.38193282598644795, 'balanced_accuracy_over_rand': 0.29363751541308336, 'accuracy': 0.592388112298837, 'recall_weighted': 0.592388112298837, 'precision_weighted': 0.5738181606946912, 'top_2': 0.8052390461646893, 'roc_auc': 0.8540347789642153, 'log_loss_r_used': 48413.8084317588, 'parallel_f1_weighted': 0.6772680084032837, 'parallel_balanced_accuracy': 0.41209020834807036, 'parallel_balanced_accuracy_over_random': 0.29450825001768444, 'parallel_accuracy': 0.6909432632444497, 'parallel_recall_weighted': 0.6909432632444497, 'parallel_precision_weighted': 0.6709886682948534}, 'diff_from_metar_to_taf': {'f1_weighted': -0.20525211408439403, 'balanced_accuracy': -0.26512982690195397, 'balanced_accuracy_over_rand': -0.303005516459376, 'accuracy': -0.19434981792552575, 'recall_weighted': -0.19434981792552575, 'precision_weighted': -0.209084481511707, 'top_2': -0.1411370844590626, 'roc_auc': -0.10453240232720529, 'log_loss_r_used': 2.4353519218913404, 'parallel_f1_weighted': -0.1735409443606345, 'parallel_balanced_accuracy': -0.24414183250425442, 'parallel_balanced_accuracy_over_random': -0.29297019900510535, 'parallel_accuracy': -0.16228121696229292, 'parallel_recall_weighted': -0.16228121696229292, 'parallel_precision_weighted': -0.1781510139367687}}}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_runway_prediction__get__no_errors__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    test_client,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_PREDICTION_URL}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        destination_airports=get_destination_airports()
    )

@pytest.mark.parametrize('request_args, wind_input, prediction_output, expected_result', [
    (
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
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
        {'prediction_input': {'origin_icao': 'EBBR', 'destination_icao': 'EHAM', 'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'wind_input_source': 'from TAF', 'wind_direction': 180.0, 'wind_speed': 10.0}, 'prediction_output': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'runway_name': '6', 'probability': 0.4, 'true_bearing': 57.92}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737225277777778, 52.289105], [4.776925, 52.30435111111111]]}}, {'type': 'Feature', 'properties': {'runway_name': '18C', 'probability': 0.3, 'true_bearing': 183.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.74003, 52.33139722222223], [4.737683333333333, 52.30583055555555]]}}, {'type': 'Feature', 'properties': {'runway_name': '36C', 'probability': 0.3, 'true_bearing': 3.22}, 'geometry': {'type': 'LineString', 'coordinates': [[4.737683333333333, 52.30583055555555], [4.74003, 52.33139722222223]]}}]}, 'airport_coordinates': [4.7638897896, 52.3086013794], 'stats': {'datetime': '2022-05-03T15:39:39.237054', 'airport': 'EHAM', 'dataset_file': '../data/final/dataset_EHAM_20210101_20211231.csv', 'date_from': '20210101', 'date_to': '20211231', 'model_filepath': '../models/rwy_used/cross-val_results/2022.05.03/CV-Test_rwy_used_results_EHAM_2022.05.03.json', 'number_estimators': 100, 'criterion': 'entropy', 'Cross-Validation with metar': {'mean_f1_weighted': 0.780042987622147, 'mean_balanced_accuracy': 0.6361590292371322, 'mean_balanced_accuracy_over_random': 0.5841817476995796, 'mean_accuracy': 0.7831405218749101, 'mean_recall_weighted': 0.7831405218749101, 'mean_precision_weighted': 0.7787738190955145, 'mean_top_2': 0.9413837922591025, 'mean_roc_auc': 0.9561976561107486, 'log_loss_r_used': 11846.773328155332, 'parallel_f1_weighted': 0.8476892638977388, 'parallel_balanced_accuracy': 0.6422266721806317, 'parallel_balanced_accuracy_over_random': 0.5706720066167581, 'parallel_accuracy': 0.850948573082011, 'parallel_recall_weighted': 0.850948573082011, 'parallel_precision_weighted': 0.8458844321338811}, 'features_importance': [['wind_dir', 0.3926026694560875], ['origin_angle', 0.20885040038726355], ['wind_speed', 0.17676037409925724], ['hour', 0.1706949486387369], ['is_summer_season', 0.025919577590236484], ['is_workday', 0.025172029828418256]], 'raw_results': {'fit_time': [1.640192985534668, 1.6318044662475586, 1.6129686832427979, 2.6991095542907715, 2.3397216796875], 'score_time': [0.8006584644317627, 0.8389027118682861, 1.1165943145751953, 0.9337189197540283, 0.9231874942779541], 'test_f1_weighted': [0.7776808507099894, 0.7807152684686011, 0.7784415909487092, 0.7807001800996997, 0.7826770478837358], 'test_balanced_accuracy': [0.6303823151802099, 0.6353945237960066, 0.635033654451409, 0.6307177304972615, 0.6492669222607739], 'test_balanced_accuracy_over_random': [0.5775797887773828, 0.5833080271954361, 0.5828956050873246, 0.5779631205682989, 0.5991621968694558], 'test_accuracy': [0.7812935907789442, 0.783496072241392, 0.781513838925189, 0.7841568166801263, 0.7852422907488987], 'test_recall_weighted': [0.7812935907789442, 0.783496072241392, 0.781513838925189, 0.7841568166801263, 0.7852422907488987], 'test_precision_weighted': [0.7764091084807576, 0.7793222995314654, 0.7773378107190775, 0.7792519085868093, 0.7815479681594631], 'test_top_2': [0.9411937449526466, 0.9420747375376257, 0.93642170178401, 0.9440569708538287, 0.9431718061674009], 'test_roc_auc': [0.9557409816211943, 0.95751913707759, 0.9541903361184119, 0.9564386223537362, 0.9570992033828106], 'test_log_loss_r_used': [11504.416984901462, 11895.727958195888, 12579.319641032711, 11895.13540461226, 11359.266652034337], 'test_parallel_f1_weighted': [0.8474408631620386, 0.8484158026653088, 0.8429729126371531, 0.8497617027409732, 0.8498550382832196], 'test_parallel_bal_acc_sc': [0.6385601684277206, 0.6413004484718635, 0.6381487079558813, 0.6351152655438913, 0.6580087705038018], 'test_parallel_bal_acc_sc_over_random': [0.5662722021132647, 0.5695605381662362, 0.5657784495470576, 0.5621383186526696, 0.5896105246045622], 'test_parallel_acc_sc': [0.8514059173335291, 0.8513325012847809, 0.8463402099698994, 0.853094486454739, 0.8525697503671072], 'test_parallel_recall_score_weighted': [0.8514059173335291, 0.8513325012847809, 0.8463402099698994, 0.853094486454739, 0.8525697503671072], 'test_parallel_precision_score_weighted': [0.8455170892906669, 0.8464972023988727, 0.8411720945284004, 0.8477976070329777, 0.8484381674184877]}, 'features': ['hour', 'is_workday', 'is_summer_season', 'wind_speed', 'wind_dir', 'origin_angle'], 'test_with_metar': {'f1_weighted': 0.7843023387328663, 'balanced_accuracy': 0.6470626528884019, 'balanced_accuracy_over_rand': 0.5966430318724594, 'accuracy': 0.7867379302243628, 'recall_weighted': 0.7867379302243628, 'precision_weighted': 0.7829026422063982, 'top_2': 0.9463761306237519, 'roc_auc': 0.9585671812914206, 'log_loss_r_used': 14092.82353963447, 'parallel_f1_weighted': 0.8508089527639182, 'parallel_balanced_accuracy': 0.6562320408523248, 'parallel_balanced_accuracy_over_random': 0.5874784490227898, 'parallel_accuracy': 0.8532244802067426, 'parallel_recall_weighted': 0.8532244802067426, 'parallel_precision_weighted': 0.8491396822316221}, 'test_with_taf': {'f1_weighted': 0.5790502246484722, 'balanced_accuracy': 0.38193282598644795, 'balanced_accuracy_over_rand': 0.29363751541308336, 'accuracy': 0.592388112298837, 'recall_weighted': 0.592388112298837, 'precision_weighted': 0.5738181606946912, 'top_2': 0.8052390461646893, 'roc_auc': 0.8540347789642153, 'log_loss_r_used': 48413.8084317588, 'parallel_f1_weighted': 0.6772680084032837, 'parallel_balanced_accuracy': 0.41209020834807036, 'parallel_balanced_accuracy_over_random': 0.29450825001768444, 'parallel_accuracy': 0.6909432632444497, 'parallel_recall_weighted': 0.6909432632444497, 'parallel_precision_weighted': 0.6709886682948534}, 'diff_from_metar_to_taf': {'f1_weighted': -0.20525211408439403, 'balanced_accuracy': -0.26512982690195397, 'balanced_accuracy_over_rand': -0.303005516459376, 'accuracy': -0.19434981792552575, 'recall_weighted': -0.19434981792552575, 'precision_weighted': -0.209084481511707, 'top_2': -0.1411370844590626, 'roc_auc': -0.10453240232720529, 'log_loss_r_used': 2.4353519218913404, 'parallel_f1_weighted': -0.1735409443606345, 'parallel_balanced_accuracy': -0.24414183250425442, 'parallel_balanced_accuracy_over_random': -0.29297019900510535, 'parallel_accuracy': -0.16228121696229292, 'parallel_recall_weighted': -0.16228121696229292, 'parallel_precision_weighted': -0.1781510139367687}}}
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_prediction_output')
def test_runway_prediction__get__no_errors__wind_input_from_taf__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    mock__handle_wind_input,
    test_client,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_PREDICTION_URL}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runway.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_body, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "destination": 'EHAM',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "destination_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "destination_icao": 'LGAV',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be one of EHAM, LEMD, LFPO, LOWW.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
def test_runway_config_prediction__post__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    request_body,
    expected_messages
):
    test_client.post(RUNWAY_CONFIG_PREDICTION_URL, data=request_body)

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )



@pytest.mark.parametrize('request_body, expected_message', [
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
def test_runway_config_prediction__post__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    request_body,
    expected_message
):
    mock_create.side_effect = METNotAvailable()

    test_client.post(RUNWAY_CONFIG_PREDICTION_URL, data=request_body)

    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )



@pytest.mark.parametrize('request_body', [
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_input_source": WindInputSource.USER.value,
            "wind_direction": 180.0,
            "wind_speed": 10.0
        }
    )
])
@mock.patch('flask.redirect')
def test_runway_config_prediction__post__no_errors__redirects_to_get_endpoint(
    mock_redirect,
    test_client,
    request_body,
):
    test_client.post(RUNWAY_CONFIG_PREDICTION_URL, data=request_body)

    query_string = query_string_from_request_arguments(request_body)

    mock_redirect.assert_called_once_with(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")


@pytest.mark.parametrize('request_args, expected_messages', [
    (
        {},
        [
            "'timestamp': ['Missing data for required field.']",
            "'destination_icao': ['Missing data for required field.'"
        ]
    ),
    (
        {
            "destination": 'EHAM',
        },
        [
            "'timestamp': ['Missing data for required field.']",
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": 'invalid'
        },
        [
            "{'timestamp': ['Not a valid integer.']",
        ]
    ),
    (
        {
            "destination_icao": 'invalid',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be a string of 4 characters.']}"
        ]
    ),
    (
        {
            "destination_icao": 'LGAV',
            "timestamp": '1650751200'
        },
        [
            "{'destination_icao': ['Should be one of EHAM, LEMD, LFPO, LOWW.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": "invalid"
        },
        [
            "{'wind_direction': ['Not a valid number.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": 361.0
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
            "timestamp": '1650751200',
            "wind_direction": -1
        },
        [
            "{'wind_direction': ['Should be between 0 and 360.']}"
        ]
    ),
    (
        {
            "destination_icao": 'EHAM',
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
            "destination_icao": 'EHAM',
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
def test_runway_config_prediction__get__invalid_input__renders_template_with_warning(
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_messages
):

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")

    mock_flash.assert_called_once()

    flashed_messages = mock_flash.call_args.args[0]
    for message in expected_messages:
        assert message in flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
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
def test_runway_config_prediction__get__met_not_available__renders_template_with_warning(
    mock_create,
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_message
):
    mock_create.side_effect = METNotAvailable()


    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, expected_message', [
    (
        {
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
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_runway_config_prediction__get__prediction_error__renders_template_with_warning(
    mock_get_runway_config_prediction_output,
    mock_flash,
    mock_render_template,
    test_client,
    request_args,
    expected_message
):
    mock_get_runway_config_prediction_output.side_effect = Exception()

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")

    mock_flash.assert_called_once()
    flashed_messages = mock_flash.call_args.args[0]
    assert expected_message == flashed_messages

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=None,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, prediction_output, expected_result', [
    (
        {
            "destination_icao": 'EHAM',
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
        {'airport_coordinates': [4.7638897896, 52.3086013794],'prediction_input': {'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'destination_icao': 'EHAM', 'wind_direction': 180.0, 'wind_input_source': 'from USER', 'wind_speed': 10.0},'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778, 52.289105],[4.776925, 52.30435111111111]], [[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.6, 'runways': [{'name': '6','true_bearing': 57.92}, {'name': '24','true_bearing': 237.95}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.74003, 52.33139722222223],[4.737683333333333, 52.30583055555555]], [[4.737683333333333, 52.30583055555555],[4.74003, 52.33139722222223]]], 'type': 'MultiLineString'},'properties': {'probability': 0.3, 'runways': [{'name': '18C','true_bearing': 183.22}, {'name': '36C','true_bearing': 3.22}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.1, 'runways': [{'name': '24','true_bearing': 237.95}]},'type': 'Feature'}],'type': 'FeatureCollection'},'stats': {'airport': 'EHAM','criterion': 'entropy','dataset_file': '../data/final/rwy_cnf_dataset_EHAM_20210101_20211231.csv','date_from': '20210101','date_to': '20211231','datetime': '2022-05-03T15:44:11.365959','diff_from_metar_to_taf': {'accuracy': -0.3663458553244334, 'balanced_accuracy': -0.5468852375047308, 'balanced_accuracy_over_rand': -0.5966020772778882, 'f1_weighted': -0.3781296608434068, 'hamming_loss': 0.10453718898301326, 'jaccard_score': -0.3803397593062319, 'parallel_accuracy': -0.3663458553244334, 'parallel_balanced_accuracy': -0.5468852375047308, 'parallel_balanced_accuracy_over_random': -0.5966020772778882, 'parallel_f1_weighted': -0.3781296608434068, 'parallel_precision_weighted': -0.37701359291949366, 'parallel_recall_weighted': -0.3663458553244334, 'precision_weighted': -0.37701359291949366, 'recall_weighted': -0.3663458553244334, 'roc_auc': -0.1446107608042142, 'top_2': -0.2569388388699161},'features': ['15min_day_interval', 'is_workday', 'is_summer_season', 'wind_speed', 'wind_dir'],'features_importance': [['wind_dir', 0.39805403370399806],['15min_day_interval', 0.33860074063410434],['wind_speed', 0.19696720359333356],['is_summer_season', 0.03866476160542617],['is_workday', 0.027713260463137806]],'mean_results': {'mean_accuracy': 0.8976496671027956, 'mean_balanced_accuracy': 0.880719056520517, 'mean_balanced_accuracy_over_random': 0.8698753343860185, 'mean_f1_weighted': 0.8974883855640201, 'mean_hamming_loss': 0.025710111006151653, 'mean_jaccard_score': 0.8786868341505455, 'mean_precision_weighted': 0.8978737093285781, 'mean_recall_weighted': 0.8976496671027956, 'mean_roc_auc': 0.990184851790225, 'mean_top_2': 0.9830787658987971, 'parallel_accuracy': 0.8976496671027956, 'parallel_balanced_accuracy': 0.880719056520517, 'parallel_balanced_accuracy_over_random': 0.8698753343860185, 'parallel_f1_weighted': 0.8974883855640201, 'parallel_precision_weighted': 0.8978737093285781, 'parallel_recall_weighted': 0.8976496671027956},'model_filepath': '../models/rwy_cnf/cross-val_results/2022.05.03/CV-Test_rwy_cnf_results_EHAM_2022.05.03.json','number_estimators': 100,'raw_results': {'fit_time': [1.6736524105072021, 1.470320224761963, 1.5453405380249023, 1.4997766017913818, 1.4819831848144531],'score_time': [5.8038489818573, 5.004283905029297, 5.554771900177002, 5.610626697540283, 4.8957085609436035],'test_accuracy': [0.8966935734244024,0.8976946363424668,0.8979275013583793,0.8968407979507879,0.8990918264379415],'test_balanced_accuracy': [0.8791872322058869, 0.87857883120977, 0.8835381616375632, 0.8722905130199683, 0.8900005445293965],'test_balanced_accuracy_over_random': [0.868204253315513, 0.8675405431379308, 0.8729507217864325, 0.8606805596581473, 0.8800005940320689],'test_f1_weighted': [0.89648123700359, 0.8974992505186343, 0.8979236568505037, 0.8966113867042128, 0.8989263967431596],'test_hamming_loss': [0.026056681598438818,0.025892372007407325,0.025570796509242523,0.02603652654106741,0.02499417837460219],'test_jaccard_score': [0.8772890072057051, 0.8778932123775965, 0.8790915443318211, 0.8770784623026403, 0.8820819445349641],'test_parallel_acc_sc': [0.8966935734244024, 0.8976946363424668, 0.8979275013583793, 0.8968407979507879, 0.8990918264379415],'test_parallel_bal_acc_sc': [0.8791872322058869, 0.87857883120977, 0.8835381616375632, 0.8722905130199683, 0.8900005445293965],'test_parallel_bal_acc_sc_over_random': [0.868204253315513, 0.8675405431379308, 0.8729507217864325, 0.8606805596581473, 0.8800005940320689],'test_parallel_f1_weighted': [0.89648123700359,0.8974992505186343,0.8979236568505037,0.8966113867042128,0.8989263967431596],'test_parallel_precision_score_weighted': [0.8969494762203706, 0.8976965713780695, 0.8983338798695508, 0.8969699010921752, 0.8994187180827248],'test_parallel_recall_score_weighted': [0.8966935734244024,0.8976946363424668,0.8979275013583793,0.8968407979507879,0.8990918264379415],'test_precision_weighted': [0.8969494762203706,0.8976965713780695,0.8983338798695508,0.8969699010921752,0.8994187180827248],'test_recall_weighted': [0.8966935734244024, 0.8976946363424668, 0.8979275013583793, 0.8968407979507879, 0.8990918264379415],'test_roc_auc': [0.989685143181387, 0.9898160922921959, 0.9908251103538654, 0.9907550841063198, 0.9898428290173572],'test_top_2': [0.9812946289972059, 0.9826127454785376, 0.9840875572459831, 0.9840099355740123, 0.9833889621982458]},'test_with_metar': {'accuracy': 0.90679913070475,'balanced_accuracy': 0.8934776519793849,'balanced_accuracy_over_rand': 0.883793802159329,'f1_weighted': 0.9066991985623477,'hamming_loss': 0.023941100811637913,'jaccard_score': 0.8875074254398485,'parallel_accuracy': 0.90679913070475,'parallel_balanced_accuracy': 0.8934776519793849,'parallel_balanced_accuracy_over_random': 0.883793802159329,'parallel_f1_weighted': 0.9066991985623477,'parallel_precision_weighted': 0.9071555697613394,'parallel_recall_weighted': 0.90679913070475,'precision_weighted': 0.9071555697613394,'recall_weighted': 0.90679913070475,'roc_auc': 0.9916329805968696,'top_2': 0.9861533685190934},'test_with_taf': {'accuracy': 0.5404532753803166,'balanced_accuracy': 0.3465924144746541,'balanced_accuracy_over_rand': 0.2871917248814409,'f1_weighted': 0.5285695377189409,'hamming_loss': 0.12847828979465117,'jaccard_score': 0.5071676661336166,'parallel_accuracy': 0.5404532753803166,'parallel_balanced_accuracy': 0.3465924144746541,'parallel_balanced_accuracy_over_random': 0.2871917248814409,'parallel_f1_weighted': 0.5285695377189409,'parallel_precision_weighted': 0.5301419768418457,'parallel_recall_weighted': 0.5404532753803166,'precision_weighted': 0.5301419768418457,'recall_weighted': 0.5404532753803166,'roc_auc': 0.8470222197926554,'top_2': 0.7292145296491773}}}
    )
])
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_runway_config_prediction__get__no_errors__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    test_client,
    request_args,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('request_args, wind_input, prediction_output, expected_result', [
    (
        {
            "destination_icao": 'EHAM',
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
        {'airport_coordinates': [4.7638897896, 52.3086013794],'prediction_input': {'date_time': 'Sat, 23 Apr 2022 22:00:00 UTC', 'destination_icao': 'EHAM', 'wind_direction': 180.0, 'wind_input_source': 'from TAF', 'wind_speed': 10.0},'prediction_output': {'features': [{'geometry': {'coordinates': [[[4.737225277777778, 52.289105],[4.776925, 52.30435111111111]], [[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.6, 'runways': [{'name': '6','true_bearing': 57.92}, {'name': '24','true_bearing': 237.95}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.74003, 52.33139722222223],[4.737683333333333, 52.30583055555555]], [[4.737683333333333, 52.30583055555555],[4.74003, 52.33139722222223]]], 'type': 'MultiLineString'},'properties': {'probability': 0.3, 'runways': [{'name': '18C','true_bearing': 183.22}, {'name': '36C','true_bearing': 3.22}]},'type': 'Feature'}, {'geometry': {'coordinates': [[[4.776925, 52.30435111111111],[4.737225277777778, 52.289105]]], 'type': 'MultiLineString'},'properties': {'probability': 0.1, 'runways': [{'name': '24','true_bearing': 237.95}]},'type': 'Feature'}],'type': 'FeatureCollection'},'stats': {'airport': 'EHAM','criterion': 'entropy','dataset_file': '../data/final/rwy_cnf_dataset_EHAM_20210101_20211231.csv','date_from': '20210101','date_to': '20211231','datetime': '2022-05-03T15:44:11.365959','diff_from_metar_to_taf': {'accuracy': -0.3663458553244334, 'balanced_accuracy': -0.5468852375047308, 'balanced_accuracy_over_rand': -0.5966020772778882, 'f1_weighted': -0.3781296608434068, 'hamming_loss': 0.10453718898301326, 'jaccard_score': -0.3803397593062319, 'parallel_accuracy': -0.3663458553244334, 'parallel_balanced_accuracy': -0.5468852375047308, 'parallel_balanced_accuracy_over_random': -0.5966020772778882, 'parallel_f1_weighted': -0.3781296608434068, 'parallel_precision_weighted': -0.37701359291949366, 'parallel_recall_weighted': -0.3663458553244334, 'precision_weighted': -0.37701359291949366, 'recall_weighted': -0.3663458553244334, 'roc_auc': -0.1446107608042142, 'top_2': -0.2569388388699161},'features': ['15min_day_interval', 'is_workday', 'is_summer_season', 'wind_speed', 'wind_dir'],'features_importance': [['wind_dir', 0.39805403370399806],['15min_day_interval', 0.33860074063410434],['wind_speed', 0.19696720359333356],['is_summer_season', 0.03866476160542617],['is_workday', 0.027713260463137806]],'mean_results': {'mean_accuracy': 0.8976496671027956, 'mean_balanced_accuracy': 0.880719056520517, 'mean_balanced_accuracy_over_random': 0.8698753343860185, 'mean_f1_weighted': 0.8974883855640201, 'mean_hamming_loss': 0.025710111006151653, 'mean_jaccard_score': 0.8786868341505455, 'mean_precision_weighted': 0.8978737093285781, 'mean_recall_weighted': 0.8976496671027956, 'mean_roc_auc': 0.990184851790225, 'mean_top_2': 0.9830787658987971, 'parallel_accuracy': 0.8976496671027956, 'parallel_balanced_accuracy': 0.880719056520517, 'parallel_balanced_accuracy_over_random': 0.8698753343860185, 'parallel_f1_weighted': 0.8974883855640201, 'parallel_precision_weighted': 0.8978737093285781, 'parallel_recall_weighted': 0.8976496671027956},'model_filepath': '../models/rwy_cnf/cross-val_results/2022.05.03/CV-Test_rwy_cnf_results_EHAM_2022.05.03.json','number_estimators': 100,'raw_results': {'fit_time': [1.6736524105072021, 1.470320224761963, 1.5453405380249023, 1.4997766017913818, 1.4819831848144531],'score_time': [5.8038489818573, 5.004283905029297, 5.554771900177002, 5.610626697540283, 4.8957085609436035],'test_accuracy': [0.8966935734244024,0.8976946363424668,0.8979275013583793,0.8968407979507879,0.8990918264379415],'test_balanced_accuracy': [0.8791872322058869, 0.87857883120977, 0.8835381616375632, 0.8722905130199683, 0.8900005445293965],'test_balanced_accuracy_over_random': [0.868204253315513, 0.8675405431379308, 0.8729507217864325, 0.8606805596581473, 0.8800005940320689],'test_f1_weighted': [0.89648123700359, 0.8974992505186343, 0.8979236568505037, 0.8966113867042128, 0.8989263967431596],'test_hamming_loss': [0.026056681598438818,0.025892372007407325,0.025570796509242523,0.02603652654106741,0.02499417837460219],'test_jaccard_score': [0.8772890072057051, 0.8778932123775965, 0.8790915443318211, 0.8770784623026403, 0.8820819445349641],'test_parallel_acc_sc': [0.8966935734244024, 0.8976946363424668, 0.8979275013583793, 0.8968407979507879, 0.8990918264379415],'test_parallel_bal_acc_sc': [0.8791872322058869, 0.87857883120977, 0.8835381616375632, 0.8722905130199683, 0.8900005445293965],'test_parallel_bal_acc_sc_over_random': [0.868204253315513, 0.8675405431379308, 0.8729507217864325, 0.8606805596581473, 0.8800005940320689],'test_parallel_f1_weighted': [0.89648123700359,0.8974992505186343,0.8979236568505037,0.8966113867042128,0.8989263967431596],'test_parallel_precision_score_weighted': [0.8969494762203706, 0.8976965713780695, 0.8983338798695508, 0.8969699010921752, 0.8994187180827248],'test_parallel_recall_score_weighted': [0.8966935734244024,0.8976946363424668,0.8979275013583793,0.8968407979507879,0.8990918264379415],'test_precision_weighted': [0.8969494762203706,0.8976965713780695,0.8983338798695508,0.8969699010921752,0.8994187180827248],'test_recall_weighted': [0.8966935734244024, 0.8976946363424668, 0.8979275013583793, 0.8968407979507879, 0.8990918264379415],'test_roc_auc': [0.989685143181387, 0.9898160922921959, 0.9908251103538654, 0.9907550841063198, 0.9898428290173572],'test_top_2': [0.9812946289972059, 0.9826127454785376, 0.9840875572459831, 0.9840099355740123, 0.9833889621982458]},'test_with_metar': {'accuracy': 0.90679913070475,'balanced_accuracy': 0.8934776519793849,'balanced_accuracy_over_rand': 0.883793802159329,'f1_weighted': 0.9066991985623477,'hamming_loss': 0.023941100811637913,'jaccard_score': 0.8875074254398485,'parallel_accuracy': 0.90679913070475,'parallel_balanced_accuracy': 0.8934776519793849,'parallel_balanced_accuracy_over_random': 0.883793802159329,'parallel_f1_weighted': 0.9066991985623477,'parallel_precision_weighted': 0.9071555697613394,'parallel_recall_weighted': 0.90679913070475,'precision_weighted': 0.9071555697613394,'recall_weighted': 0.90679913070475,'roc_auc': 0.9916329805968696,'top_2': 0.9861533685190934},'test_with_taf': {'accuracy': 0.5404532753803166,'balanced_accuracy': 0.3465924144746541,'balanced_accuracy_over_rand': 0.2871917248814409,'f1_weighted': 0.5285695377189409,'hamming_loss': 0.12847828979465117,'jaccard_score': 0.5071676661336166,'parallel_accuracy': 0.5404532753803166,'parallel_balanced_accuracy': 0.3465924144746541,'parallel_balanced_accuracy_over_random': 0.2871917248814409,'parallel_f1_weighted': 0.5285695377189409,'parallel_precision_weighted': 0.5301419768418457,'parallel_recall_weighted': 0.5404532753803166,'precision_weighted': 0.5301419768418457,'recall_weighted': 0.5404532753803166,'roc_auc': 0.8470222197926554,'top_2': 0.7292145296491773}}}
    )
])
@mock.patch('predicted_runway.routes.factory._handle_wind_input')
@mock.patch('flask.render_template')
@mock.patch('predicted_runway.domain.predictor.get_runway_config_prediction_output')
def test_runway_config_prediction__get__no_errors__wind_input_from_taf__renders_template_with_prediction_output(
    mock_get_runway_prediction_output,
    mock_render_template,
    mock__handle_wind_input,
    test_client,
    request_args,
    wind_input,
    prediction_output,
    expected_result
):
    mock_get_runway_prediction_output.return_value = prediction_output
    mock__handle_wind_input.return_value = wind_input

    query_string = query_string_from_request_arguments(request_args)

    test_client.get(f"{RUNWAY_CONFIG_PREDICTION_URL}{query_string}")

    mock_render_template.assert_called_once()
    assert mock_render_template.call_args.args == ('runwayConfig.html',)
    assert mock_render_template.call_args.kwargs == dict(
        result=expected_result,
        destination_airports=get_destination_airports()
    )


@pytest.mark.parametrize('airports_list, expected_result', [
    (
        [
            get_airport_by_icao('EHAM'),
            get_airport_by_icao('EBBR')
        ],
        [
            {"title": get_airport_by_icao('EHAM').title},
            {"title": get_airport_by_icao('EBBR').title}
        ]
    )
])
@mock.patch('predicted_runway.adapters.airports.get_airports')
def test_airports_data(mock_get_airports, test_client, airports_list, expected_result):

    mock_get_airports.return_value = airports_list
    response = test_client.get(f"{AIRPORTS_DATA_URL}/irrelevant")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_result


@pytest.mark.parametrize('invalid_destination_icao, expected_message', [
    (
        'EBBR',
        {'error': 'destination_icao EBBR is not supported. Please choose one of EHAM, LEMD, LFPO, LOWW'}
    )
])
def test_get_forecast_timestamp_range__destination_icao_not_supported__returns_404(
    test_client, invalid_destination_icao, expected_message
):
    response = test_client.get(f"{FORECAST_TIMESTAMP_RANGE_URL}/{invalid_destination_icao}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data == expected_message


@pytest.mark.parametrize('destination_icao, expected_message', [
    (
        'EHAM',
        {'error': 'No meteorological data available'}
    )
])
@mock.patch('predicted_runway.adapters.met.api.get_taf_datetime_range')
def test_get_forecast_timestamp_range__met_not_available__returns_409(
    mock_get_taf_datetime_range, test_client, destination_icao, expected_message
):
    mock_get_taf_datetime_range.side_effect = METNotAvailable()

    response = test_client.get(f"{FORECAST_TIMESTAMP_RANGE_URL}/{destination_icao}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data == expected_message


@pytest.mark.parametrize('destination_icao, taf_datetime_range, expected_message', [
    (
        'EHAM',
        (datetime(2022, 5, 19, 12), datetime(2022, 5, 20, 18)),
        {
            'start_timestamp': 1652954400,
            'end_timestamp': 1653062400
        }
    )
])
@mock.patch('predicted_runway.adapters.met.api.get_taf_datetime_range')
def test_get_forecast_timestamp_range__no_errors__returns_200_and_the_range(
    mock_get_taf_datetime_range, test_client, destination_icao, taf_datetime_range, expected_message
):
    mock_get_taf_datetime_range.return_value = taf_datetime_range

    response = test_client.get(f"{FORECAST_TIMESTAMP_RANGE_URL}/{destination_icao}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_message
