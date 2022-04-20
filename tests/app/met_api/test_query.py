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

import pytest
from pandas import Timestamp

from app.met.query import TAFAirportFilesQuery, METARAirportFilesQuery


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
