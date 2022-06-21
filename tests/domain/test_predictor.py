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
from unittest.mock import Mock

import pytest
from pandas import DataFrame

from predicted_runway.domain.models import RunwayPredictionInput, Timestamp, WindInputSource, \
    RunwayProbability, RunwayConfigProbability
from predicted_runway.domain.predictor import Predictor, predict_runway, predict_runway_config
from tests.conftest import get_airport_by_icao


@pytest.mark.parametrize(
    'prediction_input, model_input, trained_classes, prediction_result, expected_prediction_model_output',
    [
        (
            RunwayPredictionInput(
                origin=get_airport_by_icao('EBBR'),
                destination=get_airport_by_icao('EHAM'),
                timestamp=Timestamp(1650751200),
                wind_input_source=WindInputSource.TAF,
                wind_speed=15.0,
                wind_direction=180.0
            ),
            {
                'hour': 22,
                'is_workday': True,
                'is_summer_season': False,
                'wind_speed': 15.0,
                'wind_dir': 180.0,
                'origin_angle': 6.921882923696614
            },
            ['18C', '36C'],
            [[0.9, 0.1]],
            {
                '18C': 0.9,
                '36C': 0.1
            }
        )
    ]
)
def test_predictor__predict(
    prediction_input, model_input, trained_classes, prediction_result, expected_prediction_model_output
):
    trained_model = mock.Mock()
    trained_model.classes_ = trained_classes
    trained_model.feature_names_in_ = list(model_input.keys())
    trained_model.predict_proba = mock.Mock()
    trained_model.predict_proba.return_value = prediction_result

    predictor = Predictor(trained_model=trained_model)
    prediction_result = predictor.predict(prediction_input)

    assert prediction_result == expected_prediction_model_output

    trained_model.predict_proba.assert_called_once()
    model_input_dataframe = trained_model.predict_proba.call_args.args[0]

    assert model_input_dataframe.equals(DataFrame(
        [list(model_input.values())],
        columns=list(model_input.keys()))
    )


@pytest.mark.parametrize('model_output, expected_result', [
    (
        {
            '18C': 0.9,
            '36C': 0.1
        },
        [
            RunwayProbability(runway_name='18C', value=0.9),
            RunwayProbability(runway_name='36C', value=0.1)
        ]
    )
])
@mock.patch.object(Predictor, 'from_path')
def test_predict_runway(mock_from_path, model_output, expected_result):
    predictor = Mock()
    predictor.predict = Mock(return_value=model_output)
    mock_from_path.return_value = predictor

    assert predict_runway(prediction_input=mock.Mock()) == expected_result


@pytest.mark.parametrize('model_output, expected_result', [
    (
        {
            "('18C', '36C')": 0.9,
            "('1', '19')": 0.1
        },
        [
            RunwayConfigProbability(runway_config="('18C', '36C')", value=0.9),
            RunwayConfigProbability(runway_config="('1', '19')", value=0.1)
        ]
    )
])
@mock.patch.object(Predictor, 'from_path')
def test_predict_runway_config(mock_from_path, model_output, expected_result):
    predictor = Mock()
    predictor.predict = Mock(return_value=model_output)
    mock_from_path.return_value = predictor

    assert predict_runway_config(prediction_input=mock.Mock()) == expected_result
