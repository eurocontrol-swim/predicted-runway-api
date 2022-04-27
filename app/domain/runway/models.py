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
from enum import Enum


class WindInputSource(Enum):
    FROM_METAR = 'FROM_METAR'
    FROM_TAF = 'FROM_TAF'

    @classmethod
    def choices(cls):
        return [v.value for v in cls.__members__.values()]


class PredictionInput:
    def __init__(self,
                 origin_icao: str,
                 destination_icao: str,
                 date_time: datetime,
                 wind_input_source: WindInputSource,
                 wind_direction: float,
                 wind_speed: float,
                 ) -> None:
        self.origin_icao = origin_icao
        self.destination_icao = destination_icao
        self.date_time = date_time
        self.wind_input_source = wind_input_source
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed

    @property
    def date_time_str(self):
        return self.date_time.strftime('%a, %d %b %Y %H:%M:%S %Z')

    @property
    def timestamp(self):
        return int(self.date_time.timestamp())

    @property
    def date_time_hour(self):
        return self.date_time.hour

    def to_dict(self):
        wind_input_source_mapper = {
            WindInputSource.FROM_METAR: 'from METAR',
            WindInputSource.FROM_TAF: 'from TAF'
        }

        return {
            "origin_icao": self.origin_icao,
            "destination_icao": self.destination_icao,
            "date_time": self.date_time_str,
            "wind_input_source": wind_input_source_mapper.get(self.wind_input_source, ''),
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed,
        }

    def to_query_string_dict(self):
        return {
            "origin_icao": self.origin_icao,
            "destination_icao": self.destination_icao,
            "timestamp": self.timestamp,
            "wind_input_source": self.wind_input_source.value or '',
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed
        }
