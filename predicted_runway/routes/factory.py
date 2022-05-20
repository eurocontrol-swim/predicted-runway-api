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

from predicted_runway.adapters.met import api as met_api
from predicted_runway.adapters.airports import get_airport_by_icao
from predicted_runway.domain.models import WindInputSource, RunwayPredictionInput, \
    RunwayConfigPredictionInput, Timestamp


def _handle_wind_input(
    destination_icao: str,
    timestamp: int,
    wind_direction: float = None,
    wind_speed: float = None,
    wind_input_source: str = None,
) -> tuple[float, float, WindInputSource]:

    if wind_direction is None and wind_speed is None:
        wind_direction, wind_speed, wind_input_source = met_api.get_wind_input(
            airport_icao=destination_icao,
            before_timestamp=timestamp
        )
    elif wind_input_source is None:
        wind_input_source = WindInputSource.USER

    return wind_direction, wind_speed, wind_input_source


class RunwayPredictionInputFactory:

    @staticmethod
    def create(origin_icao: str,
               destination_icao: str,
               timestamp: int,
               wind_direction: float = None,
               wind_speed: float = None,
               wind_input_source: str = None
               ):

        wind_direction, wind_speed, wind_input_source = _handle_wind_input(
            destination_icao, timestamp, wind_direction, wind_speed, wind_input_source
        )

        return RunwayPredictionInput(
            origin=get_airport_by_icao(origin_icao),
            destination=get_airport_by_icao(destination_icao),
            timestamp=Timestamp(timestamp),
            wind_input_source=WindInputSource(wind_input_source) if wind_input_source else None,
            wind_direction=wind_direction,
            wind_speed=wind_speed
        )


class RunwayConfigPredictionInputFactory:

    @staticmethod
    def create(destination_icao: str,
               timestamp: int,
               wind_direction: float = None,
               wind_speed: float = None,
               wind_input_source: str = None
               ):

        wind_direction, wind_speed, wind_input_source = _handle_wind_input(
            destination_icao, timestamp, wind_direction, wind_speed, wind_input_source
        )

        return RunwayConfigPredictionInput(
            destination=get_airport_by_icao(destination_icao),
            timestamp=Timestamp(timestamp),
            wind_input_source=WindInputSource(wind_input_source) if wind_input_source else None,
            wind_direction=wind_direction,
            wind_speed=wind_speed
        )
