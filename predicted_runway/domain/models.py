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

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol, Optional, Any

import holidays


class WindInputSource(Enum):
    METAR = 'METAR'
    TAF = 'TAF'
    USER = 'USER'

    @classmethod
    def choices(cls):
        return [v.value for v in cls.__members__.values()]

    def __str__(self):
        return f"from {self.value}"


@dataclass
class Timestamp:
    value: int

    def __post_init__(self):
        self._datetime = datetime.fromtimestamp(self.value).astimezone(timezone.utc)

    def __str__(self):
        return self._datetime.strftime('%a, %d %b %Y %H:%M:%S %Z')

    @property
    def quarter_of_day(self):
        minutes_so_far = (self._datetime.hour * 60) + self._datetime.minute

        return int(minutes_so_far / 15)

    @property
    def hour_of_day(self):
        return self._datetime.hour

    def is_summer_season(self) -> bool:
        return 5 <= self._datetime.month <= 10

    def is_workday(self, country: str) -> bool:
        return self._datetime.day != 6 and self._datetime not in holidays.country_holidays(country)


@dataclass
class Runway:
    name: str
    true_bearing: float
    coordinates_geojson: list[list[float]]


@dataclass
class Airport:
    icao: str
    iata: str
    name: str
    city: str
    state: str
    country: str
    elevation: int
    lat: float
    lon: float
    tz: str
    runways: Optional[list[Runway]]

    @property
    def searchable(self):
        return f"{self.icao} {self.name} {self.city} {self.state} {self.country}"

    @property
    def title(self):
        return f"{self.icao}: {self.name}, {self.city}, {self.state}, {self.country}"

    def get_runway(self, name) -> Optional[Runway]:
        for runway in self.runways:
            if runway.name == name:
                return runway


class PredictionInput(Protocol):

    def to_dict(self) -> dict:
        ...

    def to_display_dict(self) -> dict:
        ...

    def get_model_input_values(self, features: list[str]) -> list[Any]:
        ...


@dataclass
class RunwayPredictionInput:
    origin: Airport
    destination: Airport
    timestamp: Timestamp
    wind_input_source: WindInputSource
    wind_direction: float
    wind_speed: float

    def to_dict(self):
        return {
            "origin_icao": self.origin.icao,
            "destination_icao": self.destination.icao,
            "timestamp": self.timestamp.value,
            "wind_input_source": self.wind_input_source.value if self.wind_input_source else '',
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed
        }

    def to_display_dict(self) -> dict:
        return {
            "origin_icao": self.origin.icao,
            "destination_icao": self.destination.icao,
            "date_time": str(self.timestamp),
            "wind_input_source": str(self.wind_input_source),
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed,
        }

    def get_model_input_values(self, features: list[str]) -> list[Any]:
        _model_input_mapper = {
            "hour": self.timestamp.hour_of_day,
            "is_workday": self.timestamp.is_workday(self.destination.country),
            "is_summer_season": self.timestamp.is_summer_season(),
            "wind_speed": self.wind_speed,
            "wind_dir": self.wind_direction,
            "origin_angle": get_airports_angle(origin=self.origin, destination=self.destination)
        }

        return [_model_input_mapper[feature] for feature in features]


@dataclass
class RunwayConfigPredictionInput:
    destination: Airport
    timestamp: Timestamp
    wind_input_source: WindInputSource
    wind_direction: float
    wind_speed: float

    def to_dict(self):
        return {
            "destination_icao": self.destination.icao,
            "timestamp": self.timestamp.value,
            "wind_input_source": self.wind_input_source.value if self.wind_input_source else '',
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed
        }

    def to_display_dict(self) -> dict:
        return {
            "destination_icao": self.destination.icao,
            "date_time": str(self.timestamp),
            "wind_input_source": str(self.wind_input_source) if self.wind_input_source else '',
            "wind_direction": self.wind_direction,
            "wind_speed": self.wind_speed,
        }

    def get_model_input_values(self, features: list[str]) -> list[Any]:
        _model_input_mapper = {
            "15min_day_interval": self.timestamp.quarter_of_day,
            "is_workday": self.timestamp.is_workday(country=self.destination.country),
            "is_summer_season": self.timestamp.is_summer_season(),
            "wind_speed": self.wind_speed,
            "wind_dir": self.wind_direction
        }

        return [_model_input_mapper[feature] for feature in features]


class PredictionModelOutput(dict):
    ...


@dataclass
class RunwayProbability:
    runway_name: str
    value: float


@dataclass
class RunwayConfigProbability:
    runway_config: str
    value: float

    @property
    def runway_names(self):
        runways = self.runway_config.replace("(", "")\
                             .replace(")", "")\
                             .replace("'", "")\
                             .replace(" ", "")\
                             .split(",")

        return [runway for runway in runways if runway]


class PredictionOutput(Protocol):

    def to_geojson(self, exclude_zero_probas: bool = False) -> dict:
        ...


@dataclass
class RunwayPredictionOutput:
    probas: list[RunwayProbability]
    destination: Airport

    @property
    def sorted_probas(self):
        return sorted(self.probas, key=lambda x: x.value, reverse=True)

    def _get_runway_geojson(self, runway: Runway, proba: RunwayProbability) -> dict:
        return {
            "type": "Feature",
            "properties": {
                "runway_name": runway.name,
                "probability": proba.value,
                "true_bearing": runway.true_bearing
            },
            "geometry": {
                "type": "LineString",
                "coordinates": runway.coordinates_geojson
            }
        }

    def to_geojson(self, exclude_zero_probas: bool = False) -> dict:
        probas = self.sorted_probas

        if exclude_zero_probas:
            probas = [proba for proba in probas if proba.value > 0.01]

        return {
            "type": "FeatureCollection",
            "features": [
                self._get_runway_geojson(runway=self.destination.get_runway(proba.runway_name),
                                         proba=proba)

                for proba in probas
            ]
        }


@dataclass
class RunwayConfigPredictionOutput:
    probas: list[RunwayConfigProbability]
    destination: Airport

    @property
    def sorted_probas(self):
        return sorted(self.probas, key=lambda x: x.value, reverse=True)

    def _get_runway_config_geojson(self, proba: RunwayConfigProbability) -> dict:
        runways = [self.destination.get_runway(name) for name in proba.runway_names]

        return {
            "type": "Feature",
            "properties": {
                "probability": proba.value,
                "runways": [
                    {
                        "name": runway.name,
                        "true_bearing": runway.true_bearing
                    }
                    for runway in runways
                ],
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": [
                    runway.coordinates_geojson for runway in runways
                ]
            }
        }

    def to_geojson(self, exclude_zero_probas: bool = False) -> dict:
        probas = self.sorted_probas

        if exclude_zero_probas:
            probas = [proba for proba in probas if proba.value > 0.01]

        return {
            "type": "FeatureCollection",
            "features": [
                self._get_runway_config_geojson(proba)for proba in probas
            ]
        }


def get_airports_angle(origin: Airport, destination: Airport) -> float:
    origin_lat = math.radians(origin.lat)
    origin_lon = math.radians(origin.lon)
    destination_lat = math.radians(destination.lat)
    destination_lon = math.radians(destination.lon)

    diff_lon = destination_lon - origin_lon

    y = math.sin(diff_lon) * math.cos(destination_lat)
    x = math.cos(origin_lat) * math.sin(destination_lat) \
        - math.sin(origin_lat) * math.cos(destination_lat) * math.cos(diff_lon)

    bearing = math.atan2(y, x)

    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360

    return bearing
