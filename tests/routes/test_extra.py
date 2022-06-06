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
from datetime import datetime, timezone
from unittest import mock

import pytest
from met_update_db import repo as met_repo

from predicted_runway.adapters.airports import get_airport_by_icao


AIRPORTS_DATA_URL = '/api/0.1/airports-data'
LAST_TAF_END_TIME_URL = '/api/0.1/latest-taf-end-time'


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
        {'detail': 'destination_icao EBBR is not supported. Please choose one of EHAM, LEMD, LFPO, LOWW'}
    )
])
def test_get_forecast_timestamp_range__destination_icao_not_supported__returns_404(
    test_client, invalid_destination_icao, expected_message
):
    response = test_client.get(f"{LAST_TAF_END_TIME_URL}/{invalid_destination_icao}")

    assert response.status_code == 404

    response_data = json.loads(response.data)

    assert response_data == expected_message


@pytest.mark.parametrize('destination_icao, expected_message', [
    (
        'EHAM',
        {'detail': 'No meteorological data available'}
    )
])
@mock.patch('met_update_db.repo.get_last_taf_end_time')
def test_get_forecast_timestamp_range__met_not_available__returns_409(
    mock_get_last_taf_end_time, test_client, destination_icao, expected_message
):
    mock_get_last_taf_end_time.side_effect = met_repo.METNotAvailable()

    response = test_client.get(f"{LAST_TAF_END_TIME_URL}/{destination_icao}")

    assert response.status_code == 409

    response_data = json.loads(response.data)

    assert response_data == expected_message


@pytest.mark.parametrize('destination_icao, last_taf_end_time, expected_message', [
    (
        'EHAM',
        datetime(2022, 5, 20, 18, tzinfo=timezone.utc),
        {
            'end_timestamp': 1653069600
        }
    )
])
@mock.patch('met_update_db.repo.get_last_taf_end_time')
def test_get_forecast_timestamp_range__no_errors__returns_200_and_the_range(
    mock_get_last_taf_end_time, test_client, destination_icao, last_taf_end_time, expected_message
):
    mock_get_last_taf_end_time.return_value = last_taf_end_time

    response = test_client.get(f"{LAST_TAF_END_TIME_URL}/{destination_icao}")

    assert response.status_code == 200

    response_data = json.loads(response.data)

    assert response_data == expected_message
