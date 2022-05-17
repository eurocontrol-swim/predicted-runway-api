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

from datetime import datetime, timezone
from unittest import mock

import pytest

from predicted_runway.domain.models import WindInputSource
from predicted_runway.adapters.met.api import get_wind_input_from_metar, get_wind_input_from_taf, \
    get_wind_input, \
    METNotAvailable, get_taf_datetime_range
from predicted_runway.adapters.met.query import METARAirportFilesQuery, TAFAirportFilesQuery


@pytest.fixture
def airport_icao():
    return 'EHAM'


@pytest.fixture
def before_timestamp():
    return int(datetime.now().timestamp())


@mock.patch.object(METARAirportFilesQuery, 'get_wind_direction')
def test_get_wind_from_metar__wind_direction_not_found__returns_none(
    mock_get_wind_direction, metar_files_dir, airport_icao, before_timestamp
):
    mock_get_wind_direction.return_value = None
    assert get_wind_input_from_metar(airport_icao=airport_icao,
                                     before_timestamp=before_timestamp) is None


@mock.patch.object(METARAirportFilesQuery, 'get_wind_speed')
def test_get_wind_from_metar__wind_speed_not_found__returns_none(
    mock_get_wind_speed, metar_files_dir, airport_icao, before_timestamp
):
    mock_get_wind_speed.return_value = None
    assert get_wind_input_from_metar(airport_icao='EHAM',
                                     before_timestamp=before_timestamp) is None


@mock.patch.object(TAFAirportFilesQuery, 'get_wind_direction')
def test_get_wind_from_taf__wind_direction_not_found__returns_none(
    mock_get_wind_direction, taf_files_dir, airport_icao, before_timestamp
):
    mock_get_wind_direction.return_value = None
    assert get_wind_input_from_taf(airport_icao=airport_icao,
                                   before_timestamp=before_timestamp) is None


@mock.patch.object(TAFAirportFilesQuery, 'get_wind_speed')
def test_get_wind_from_taf__wind_speed_not_found__returns_none(
    mock_get_wind_speed, taf_files_dir, airport_icao, before_timestamp
):
    mock_get_wind_speed.return_value = None
    assert get_wind_input_from_taf(airport_icao=airport_icao,
                                   before_timestamp=before_timestamp) is None


@mock.patch('predicted_runway.adapters.met.api.get_wind_input_from_metar')
def test_get_wind_input__found_in_metar__returns_values_and_source(
    mock_get_wind_input_from_metar, airport_icao, before_timestamp
):
    mock_get_wind_input_from_metar.return_value = 10, 10
    assert get_wind_input(airport_icao=airport_icao, before_timestamp=before_timestamp) \
           == (10, 10, WindInputSource.METAR)


@mock.patch('predicted_runway.adapters.met.api.get_wind_input_from_taf')
@mock.patch('predicted_runway.adapters.met.api.get_wind_input_from_metar')
def test_get_wind_input__not_found_in_metar__returns_taf_values_and_source(
    mock_get_wind_input_from_metar, mock_get_wind_input_from_taf, airport_icao, before_timestamp
):
    mock_get_wind_input_from_metar.return_value = None
    mock_get_wind_input_from_taf.return_value = 10, 10
    assert get_wind_input(airport_icao=airport_icao, before_timestamp=before_timestamp) \
           == (10, 10, WindInputSource.TAF)


@mock.patch('predicted_runway.adapters.met.api.get_wind_input_from_taf')
@mock.patch('predicted_runway.adapters.met.api.get_wind_input_from_metar')
def test_get_wind_input__not_found_in_neither_source__raises_metnotavailable(
    mock_get_wind_input_from_metar, mock_get_wind_input_from_taf, airport_icao, before_timestamp
):
    mock_get_wind_input_from_metar.return_value = None
    mock_get_wind_input_from_taf.return_value = None
    with pytest.raises(METNotAvailable):
        get_wind_input(airport_icao=airport_icao, before_timestamp=before_timestamp)


@pytest.mark.parametrize('expected_range', [
    (datetime(2022, 3, 18, 12, 0, tzinfo=timezone.utc),
     datetime(2022, 3, 22, 12, 0, tzinfo=timezone.utc))
])
@mock.patch.object(TAFAirportFilesQuery, 'get_datetime_range')
def test_get_taf_datetime_range(mock_get_datetime_range, expected_range, airport_icao):
    mock_get_datetime_range.return_value = expected_range

    assert get_taf_datetime_range(airport_icao) == expected_range


@mock.patch.object(TAFAirportFilesQuery, 'get_datetime_range')
def test_get_taf_datetime_range__range_is_none__raises_metnotavailable(
    mock_get_datetime_range, airport_icao
):
    mock_get_datetime_range.return_value = None

    with pytest.raises(METNotAvailable):
        get_taf_datetime_range(airport_icao)
