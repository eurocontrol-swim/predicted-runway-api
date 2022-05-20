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

from datetime import datetime

from predicted_runway.config import get_metar_dir_for_airport_icao, get_taf_dir_for_airport_icao
from predicted_runway.domain.models import WindInputSource
from predicted_runway.adapters.met.query import METARAirportFilesQuery, TAFAirportFilesQuery, AirportFilesQuery


class METNotAvailable(Exception):
    ...


def _get_wind_input_from_source(source_query: AirportFilesQuery, before_timestamp: int) \
        -> tuple[float, float] | None:

    wind_direction = source_query.get_wind_direction(before_timestamp=before_timestamp)
    if wind_direction is not None:
        wind_speed = source_query.get_wind_speed(before_timestamp=before_timestamp)
        if wind_speed is not None:
            return wind_direction, wind_speed


def get_wind_input_from_metar(airport_icao: str, before_timestamp: int) -> tuple[float, float] | None:

    query = METARAirportFilesQuery(files_dir=get_metar_dir_for_airport_icao(airport_icao))

    return _get_wind_input_from_source(source_query=query, before_timestamp=before_timestamp)


def get_wind_input_from_taf(airport_icao: str, before_timestamp: int) -> tuple[float, float] | None:

    query = TAFAirportFilesQuery(files_dir=get_taf_dir_for_airport_icao(airport_icao))

    return _get_wind_input_from_source(source_query=query, before_timestamp=before_timestamp)


def get_wind_input(airport_icao: str, before_timestamp: int) -> tuple[float, float, WindInputSource]:
    source = WindInputSource.METAR
    wind_input = get_wind_input_from_metar(airport_icao=airport_icao,
                                           before_timestamp=before_timestamp)

    if not wind_input:
        source = WindInputSource.TAF
        wind_input = get_wind_input_from_taf(airport_icao=airport_icao,
                                             before_timestamp=before_timestamp)

    if not wind_input:
        raise METNotAvailable()

    wind_direction, wind_speed = wind_input
    return wind_direction, wind_speed, source


def get_taf_datetime_range(destination_icao) -> tuple[datetime, datetime]:
    fq = TAFAirportFilesQuery(files_dir=get_taf_dir_for_airport_icao(airport_icao=destination_icao))

    datetime_range = fq.get_datetime_range()

    if datetime_range is None:
        raise METNotAvailable()

    return datetime_range
