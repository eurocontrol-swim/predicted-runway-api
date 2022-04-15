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

import datetime

import pytest as pytest

from app.domain import DESTINATION_ICAOS
from app.routes.schemas import ValidationError, PredictionInputSchema


@pytest.fixture
def prediction_input_data():
    return {
        "origin_icao": "EBBR",
        "destination_icao": "EHAM",
        "timestamp": 1650029727,
        "wind_direction": 100.0,
        "wind_speed": 100.0
    }


@pytest.mark.parametrize('invalid_origin_icao', ['ICAO1', 1, 1.0, {}, [], (), False, None])
def test_prediction_input_schema__invalid_origin_icao(invalid_origin_icao):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_origin_icao(invalid_origin_icao)
    assert str(e.value) == 'origin_icao should be a string of 4 characters.'


@pytest.mark.parametrize('origin_icao', ['ICAO', '11CA'])
def test_prediction_input_schema__origin_icao_is_valid(origin_icao):
    assert PredictionInputSchema()._validate_origin_icao(origin_icao) == origin_icao.upper()


@pytest.mark.parametrize('invalid_destination_icao', ['ICAO1', 1, 1.0, {}, [], (), False, None])
def test_prediction_input_schema__invalid_destination_icao(invalid_destination_icao):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_destination_icao(invalid_destination_icao)
    assert str(e.value) == 'destination_icao should be a string of 4 characters.'


@pytest.mark.parametrize('invalid_destination_icao', ['LEMD', 'EBBR', 'LGAV'])
def test_prediction_input_schema__destination_icao_is_not_supported(invalid_destination_icao):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_destination_icao(invalid_destination_icao)
    assert str(e.value) == f"destination_icao should be one of {', '.join(DESTINATION_ICAOS)}."


@pytest.mark.parametrize('destination_icao', DESTINATION_ICAOS)
def test_prediction_input_schema__destination_icao_is_valid_and_supported(destination_icao):
    assert PredictionInputSchema()._validate_destination_icao(destination_icao) == destination_icao


@pytest.mark.parametrize('invalid_timestamp', ['str', [], {}, (), None])
def test_prediction_input_schema__timestamp_is_not_integer(invalid_timestamp):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_timestamp(invalid_timestamp)
    assert str(e.value) == f"timestamp should be an integer."


@pytest.mark.parametrize('invalid_timestamp', [1111111111111111111111111])
def test_prediction_input_schema__timestamp_not_convertable_to_datetime(invalid_timestamp):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_timestamp(invalid_timestamp)
    assert str(e.value) == f"Invalid timestamp."


@pytest.mark.parametrize('timestamp', [1650024497, 1650030959])
def test_prediction_input_schema__timestamp_is_converted_to_datetime(timestamp):
    assert PredictionInputSchema()._validate_timestamp(timestamp).timestamp() == timestamp


@pytest.mark.parametrize('invalid_wind_direction', ['str', [], {}, (), None])
def test_prediction_input_schema__wind_direction_is_not_float(invalid_wind_direction):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_wind_direction(invalid_wind_direction)
    assert str(e.value) == f"wind_direction should be a float."


@pytest.mark.parametrize('invalid_wind_direction', [-1, 361])
def test_prediction_input_schema__wind_direction_is_not_between_0_and_360(invalid_wind_direction):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_wind_direction(invalid_wind_direction)
    assert str(e.value) == f"wind_direction should be between 0 and 360."


@pytest.mark.parametrize('wind_direction', [0, 1, 100, 360])
def test_prediction_input_schema__wind_direction_is_valid(wind_direction):
    assert PredictionInputSchema()._validate_wind_direction(wind_direction) == wind_direction


@pytest.mark.parametrize('invalid_wind_speed', ['str', [], {}, (), None])
def test_prediction_input_schema__wind_speed_is_not_float(invalid_wind_speed):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_wind_speed(invalid_wind_speed)
    assert str(e.value) == f"wind_speed should be a float."


@pytest.mark.parametrize('invalid_wind_speed', [-1, -1000])
def test_prediction_input_schema__wind_speed_is_not_between_positive(invalid_wind_speed):
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema()._validate_wind_speed(invalid_wind_speed)
    assert str(e.value) == f"wind_speed should be positive."


@pytest.mark.parametrize('wind_speed', [0, 1, 100, 360])
def test_prediction_input_schema__wind_speed_is_valid(wind_speed):
    assert PredictionInputSchema()._validate_wind_speed(wind_speed) == wind_speed


def test_prediction_input_schema__invalid_prediction_input_data(prediction_input_data):
    del prediction_input_data['origin_icao']
    with pytest.raises(ValidationError) as e:
        PredictionInputSchema().load(**prediction_input_data)
    assert str(e.value) == f"Invalid input."


def test_prediction_input_schema__valid_prediction_input_data__returns_prediction_input(
    prediction_input_data
):
    prediction_input = PredictionInputSchema().load(**prediction_input_data)
    assert prediction_input.origin_icao == prediction_input_data['origin_icao'].upper()
    assert prediction_input.destination_icao == prediction_input_data['destination_icao'].upper()
    assert prediction_input.date_time.timestamp() == prediction_input_data['timestamp']
    assert prediction_input.wind_direction == prediction_input_data['wind_direction']
    assert prediction_input.wind_speed == prediction_input_data['wind_speed']
