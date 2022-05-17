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
import datetime
from unittest import mock

import pytest
from pandas import Timestamp

from predicted_runway.adapters.met.query import TAFAirportFilesQuery, METARAirportFilesQuery, \
    AirportFilesQuery


@pytest.fixture
def first_taf_file(taf_files_dir):
    return next(taf_files_dir.glob("*.json"))


@pytest.fixture
def first_metar_file(metar_files_dir):
    return next(metar_files_dir.glob("*.json"))


@mock.patch.object(AirportFilesQuery, 'list_files')
def test_airport_files_query__get_file__no_existing_files__returns_none(
    mock_list_files, taf_files_dir
):
    mock_list_files.return_value = []
    assert AirportFilesQuery(files_dir=taf_files_dir).get_file(before_timestamp=1650564000) is None


def test_airport_files_query__list_files(taf_files_dir):
    assert AirportFilesQuery(files_dir=taf_files_dir).list_files() == \
        sorted(list(taf_files_dir.glob('*.json')))


def test_airport_files_query__list_files__reverse_order(taf_files_dir):
    assert AirportFilesQuery(files_dir=taf_files_dir).list_files(reverse_order=True) == \
        sorted(list(taf_files_dir.glob('*.json')), reverse=True)


@pytest.mark.parametrize('timestamp, is_before', [
    (1650564000, True),
    (1647613805, True),
    (1647613803, False),
])
def test_airport_files_query__file_is_before_timestamp(
        first_taf_file, timestamp, is_before, taf_files_dir
):
    assert AirportFilesQuery(files_dir=taf_files_dir).file_is_before_timestamp(
        first_taf_file, timestamp) == is_before


@pytest.mark.parametrize(
    'file_is_before_timestamp, file_contains_timestamp, expected_file_has_timestamp', [
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, True),
])
@mock.patch.object(AirportFilesQuery, 'file_contains_timestamp')
@mock.patch.object(AirportFilesQuery, 'file_is_before_timestamp')
def test_airport_files_query__file_has_timestamp(
    mock_file_is_before_timestamp,
    mock_file_contains_timestamp,
    file_is_before_timestamp,
    file_contains_timestamp,
    expected_file_has_timestamp,
    taf_files_dir
):
    mock_file_is_before_timestamp.return_value = file_is_before_timestamp
    mock_file_contains_timestamp.return_value = file_contains_timestamp

    assert AirportFilesQuery(files_dir=taf_files_dir).file_has_timestamp(
        file=mock.Mock(), timestamp=1650564000) == expected_file_has_timestamp


@pytest.mark.parametrize('before_timestamp, actual_timestamp', [
    (int(Timestamp("2022-03-22T09:00:00Z").timestamp()), '2022-03-21T09:03:14.401472Z'),
    (1647608406 + 500, "2022-03-18T13:00:07.883260Z")
])
def test_taf_airport_files_query__file_is_found(before_timestamp, actual_timestamp, taf_files_dir):
    query = TAFAirportFilesQuery(files_dir=taf_files_dir)
    taf = query.get_file(before_timestamp=before_timestamp)

    with open(taf, 'r') as f:
        content = json.load(f)

    tested_taf_timestamp = content['meta']['timestamp']
    assert actual_timestamp == tested_taf_timestamp


@pytest.mark.parametrize('forecast_dict, value_key, expected_forecast_value', [
    ({'key': {'value': 1}}, 'key', 1),
    ({'key': {'value': 1.2}}, 'key', 1.2),
    ({'key': {'val': 1.2}}, 'key', None),
    ({'key': {'value': 1}}, 'invalid_key', None),
    ({'key': {'value': 'invalid_value'}}, 'key', None),
    ({'key': {'value': None}}, 'key', None),
])
def test_taf_get_forecast_value__invalid_float(
        forecast_dict, value_key, expected_forecast_value, taf_files_dir
):
    assert TAFAirportFilesQuery(files_dir=taf_files_dir)._get_forecast_value(forecast_dict, value_key) \
           == expected_forecast_value


@pytest.mark.parametrize('file_content, before_timestamp, expected_backup_value', [
    (
        {
            'forecast': [
                {
                    'start_time': {'dt': '2022-03-19T07:00:00Z'},
                    'end_time': {'dt': '2022-03-19T09:00:00Z'},
                    'wind_speed': {'value': 1.1}
                },
                {
                    'start_time': {'dt': '2022-03-19T10:00:00Z'},
                    'end_time': {'dt': '2022-03-20T12:00:00Z'},
                    'wind_speed': {'value': None}
                }
            ]
        },
        int(datetime.datetime(2022, 3, 19, 8, 1, 40).timestamp()),
        1.1
    ),
    (
        {
            'forecast': [
                {
                    'start_time': {'dt': '2022-03-19T03:00:00Z'},
                    'end_time': {'dt': '2022-03-20T05:00:00Z'},
                    'wind_speed': {'value': None}
                },
                {
                    'start_time': {'dt': '2022-03-19T07:00:00Z'},
                    'end_time': {'dt': '2022-03-19T09:00:00Z'},
                    'wind_speed': {'value': 1.1}
                },
                {
                    'start_time': {'dt': '2022-03-19T10:00:00Z'},
                    'end_time': {'dt': '2022-03-20T12:00:00Z'},
                    'wind_speed': {'value': None}
                }
            ]
        },
        int(datetime.datetime(2022, 7, 13, 2, 48, 20).timestamp()),
        1.1
    )
])
@mock.patch.object(TAFAirportFilesQuery, '_read_file')
def test_get_wind_value_from_file__return_the_backup_value_in_case_none_is_found(
    mock_read_file, file_content, before_timestamp, expected_backup_value, taf_files_dir
):
    mock_read_file.return_value = file_content
    assert TAFAirportFilesQuery(files_dir=taf_files_dir)._get_wind_value_from_file(
        file=mock.Mock(),
        before_timestamp=before_timestamp,
        value_key='wind_speed') == expected_backup_value


def test_taf_airport_files_query__file_not_found(taf_files_dir):
    query = TAFAirportFilesQuery(files_dir=taf_files_dir)
    before_timestamp = int(Timestamp('2022-03-22T12:00:00Z').timestamp() + 3600)

    assert query.get_file(before_timestamp=before_timestamp) is None


@pytest.mark.parametrize('before_timestamp, expected_wind_speed', [
    (int(Timestamp('2022-03-19T01:00:00Z').timestamp()), 10)
])
def test_taf_airport_files_query__get_wind_speed(before_timestamp, expected_wind_speed, taf_files_dir):
    query = TAFAirportFilesQuery(files_dir=taf_files_dir)
    assert query.get_wind_speed(before_timestamp=before_timestamp) == expected_wind_speed


@pytest.mark.parametrize('before_timestamp, expected_wind_direction', [
    (int(Timestamp('2022-03-19T12:00:00Z').timestamp()), 80)
])
def test_taf_airport_files_query__get_wind_direction(before_timestamp, expected_wind_direction, taf_files_dir):
    query = TAFAirportFilesQuery(files_dir=taf_files_dir)
    assert query.get_wind_direction(before_timestamp=before_timestamp) == expected_wind_direction


@pytest.mark.parametrize('expected_range', [
    (datetime.datetime(2022, 3, 18, 12, 0, tzinfo=datetime.timezone.utc),
     datetime.datetime(2022, 3, 22, 12, 0, tzinfo=datetime.timezone.utc))
])
def test_taf_airport_files_query__get_datetime_range(expected_range, taf_files_dir):
    query = TAFAirportFilesQuery(files_dir=taf_files_dir)
    assert query.get_datetime_range() == expected_range


@mock.patch.object(TAFAirportFilesQuery, 'list_files')
def test_taf_airport_files_query__get_datetime_range__no_files__returns_none(
    mock_list_files, taf_files_dir
):
    mock_list_files.return_value = []
    assert TAFAirportFilesQuery(files_dir=taf_files_dir).get_datetime_range() is None


@mock.patch.object(TAFAirportFilesQuery, 'list_files')
def test_taf_airport_files_query__get_datetime_range__has_only_one_files__returns_values_of_the_file(
    mock_list_files, taf_files_dir, first_taf_file
):
    mock_list_files.return_value = [first_taf_file]
    assert TAFAirportFilesQuery(files_dir=taf_files_dir).get_datetime_range() \
           == (datetime.datetime(2022, 3, 18, 12, 0, tzinfo=datetime.timezone.utc),
               datetime.datetime(2022, 3, 19, 18, 0, tzinfo=datetime.timezone.utc))


@pytest.mark.parametrize('before_timestamp', [
    int(Timestamp("2022-03-18T13:00:04.522430Z").timestamp() - 50),
    int(Timestamp("2022-03-18T17:16:08.291369Z").timestamp() + 3600 * 2.5)
])
def test_metar_airport_files_query__file_not_found(before_timestamp, metar_files_dir):
    query = METARAirportFilesQuery(files_dir=metar_files_dir)

    assert query.get_file(before_timestamp=before_timestamp) is None


@pytest.mark.parametrize('before_timestamp, actual_timestamp', [
    (int(Timestamp('2022-03-18T14:25:00Z').timestamp() + 25 * 60), '2022-03-18T14:30:06.009450Z')
])
def test_metar_airport_files_query__file_is_found(before_timestamp, actual_timestamp, metar_files_dir):
    query = METARAirportFilesQuery(files_dir=metar_files_dir)
    taf = query.get_file(before_timestamp=before_timestamp)

    with open(taf, 'r') as f:
        content = json.load(f)

    tested_taf_timestamp = content['meta']['timestamp']
    assert actual_timestamp == tested_taf_timestamp


@pytest.mark.parametrize('before_timestamp, expected_wind_speed', [
    (int(Timestamp('2022-03-18T16:30:05.481364Z').timestamp() + 1), 13)
])
def test_metar_airport_files_query__get_wind_speed(before_timestamp, expected_wind_speed, metar_files_dir):
    query = METARAirportFilesQuery(files_dir=metar_files_dir)
    assert query.get_wind_speed(before_timestamp=before_timestamp) == expected_wind_speed


@pytest.mark.parametrize('before_timestamp, expected_wind_direction', [
    (int(Timestamp('2022-03-18T16:30:05.481364Z').timestamp() + 1), 359)
])
def test_metar_airport_files_query__get_wind_direction(before_timestamp, expected_wind_direction, metar_files_dir):
    query = METARAirportFilesQuery(files_dir=metar_files_dir)
    assert query.get_wind_direction(before_timestamp=before_timestamp) == expected_wind_direction


@pytest.mark.parametrize('file_content, expected_wind_value', [
    ({'wind_speed': {'value': 1}}, 1),
    ({'wind_speed': {'value': 1.2}}, 1.2),
    ({'wind_speed': {'val': 1.2}}, None),
    ({'invalid_value': {'value': 1}}, None),
    ({'wind_speed': {'value': 'invalid_value'}}, None),
    ({'wind_speed': {'value': None}}, None),
])
@mock.patch.object(METARAirportFilesQuery, '_read_file')
def test_metar_airport_files_query__get_wind_value_from_file(
    mock_read_file,
    file_content,
    expected_wind_value,
    taf_files_dir
):
    mock_read_file.return_value = file_content
    assert METARAirportFilesQuery(files_dir=taf_files_dir)._get_wind_value_from_file(
        file=mock.Mock(), wind_value='wind_speed') == expected_wind_value
