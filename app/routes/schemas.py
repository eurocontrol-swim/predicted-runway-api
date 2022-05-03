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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from app.config import DESTINATION_ICAOS
from app.adapters.stats import get_runway_airport_stats, get_runway_config_airport_stats
from app.domain.models import RunwayPredictionInput, WindInputSource, RunwayConfigPredictionInput, \
    RunwayPredictionOutput, RunwayConfigPredictionOutput


class ValidationError(Exception):
    ...


def _is_valid_icao(icao: str):
    return isinstance(icao, str) and len(icao) == 4


def _validate_origin_icao(value: Any) -> str:
    if not _is_valid_icao(value):
        raise ValueError("origin_icao should be a string of 4 characters.")

    return value


def _validate_destination_icao(value: Any) -> str:
    if not _is_valid_icao(value):
        raise ValueError("destination_icao should be a string of 4 characters.")

    if value not in DESTINATION_ICAOS:
        raise ValueError(f"destination_icao should be one of {', '.join(DESTINATION_ICAOS)}.")

    return value


def _validate_timestamp(value: Any) -> int:
    if not (isinstance(value, int)):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("timestamp should be an integer.")

    try:
        datetime.fromtimestamp(value)
    except (TypeError, ValueError, OSError, OverflowError):
        raise ValueError("Invalid timestamp.")

    return value


def _validate_wind_direction(value: Any) -> float:
    if not isinstance(value, int):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValueError("wind_direction should be a float.")

    if not 0 <= value <= 360:
        raise ValueError('wind_direction should be between 0 and 360.')

    return value


def _validate_wind_speed(value: any) -> float:
    if not isinstance(value, int):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValueError("wind_speed should be a float.")

    if value < 0:
        raise ValueError('wind_speed should be positive.')

    return value


class PredictionInputSchema(ABC):

    def validate(self, **kwargs) -> dict:
        try:
            return self._validate(**kwargs)
        except TypeError:
            raise ValidationError('Invalid input.')
        except ValueError as e:
            raise ValidationError(str(e))

    @abstractmethod
    def _validate(self, **kwargs) -> dict:
        ...


class RunwayPredictionInputSchema(PredictionInputSchema):

    def _validate(
        self,
        origin_icao: str,
        destination_icao: str,
        timestamp: int,
        wind_direction: Optional[float] = None,
        wind_speed: Optional[float] = None,
        wind_input_source: Optional[str] = None,
    ) -> dict:

        validated_data = {
            "origin_icao": _validate_origin_icao(origin_icao),
            "destination_icao": _validate_destination_icao(destination_icao),
            "timestamp": _validate_timestamp(timestamp),
        }

        if wind_direction is not None:
            validated_data["wind_direction"] = _validate_wind_direction(wind_direction)

        if wind_speed is not None:
            validated_data["wind_speed"] = _validate_wind_speed(wind_speed)

        try:
            validated_data["wind_input_source"] = WindInputSource(wind_input_source)
        except ValueError:
            pass

        return validated_data


class RunwayConfigPredictionInputSchema(PredictionInputSchema):

    def _validate(
        self,
        destination_icao: str,
        timestamp: int,
        wind_direction: Optional[float] = None,
        wind_speed: Optional[float] = None,
        wind_input_source: Optional[str] = None,
    ) -> dict:

        validated_data = {
            "destination_icao": _validate_destination_icao(destination_icao),
            "timestamp": _validate_timestamp(timestamp),
        }

        if wind_direction is not None:
            validated_data["wind_direction"] = _validate_wind_direction(wind_direction)

        if wind_speed is not None:
            validated_data["wind_speed"] = _validate_wind_speed(wind_speed)

        try:
            validated_data["wind_input_source"] = WindInputSource(wind_input_source)
        except ValueError:
            pass

        return validated_data


@dataclass
class RunwayPredictionOutputSchema:
    prediction_input: RunwayPredictionInput
    prediction_output: RunwayPredictionOutput

    def to_api(self) -> dict:
        return {
            "prediction_input": self.prediction_input.to_dict(),
            "prediction_output": self.prediction_output.to_geojson(),
        }

    def to_web(self) -> dict:
        return {
            "prediction_input": self.prediction_input.to_display_dict(),
            "prediction_output": self.prediction_output.to_geojson(exclude_zero_probas=True),
            "airport_coordinates": [self.prediction_input.destination.lon,
                                    self.prediction_input.destination.lat],
            "stats": get_runway_airport_stats(self.prediction_input.destination.icao)
        }


@dataclass
class RunwayConfigPredictionOutputSchema:
    prediction_input: RunwayConfigPredictionInput
    prediction_output: RunwayConfigPredictionOutput

    def to_api(self) -> dict:
        return {
            "prediction_input": self.prediction_input.to_dict(),
            "prediction_output": self.prediction_output.to_geojson(),
        }

    def to_web(self) -> dict:
        return {
            "prediction_input": self.prediction_input.to_display_dict(),
            "prediction_output": self.prediction_output.to_geojson(exclude_zero_probas=True),
            "airport_coordinates": [self.prediction_input.destination.lon,
                                    self.prediction_input.destination.lat],
            "stats": get_runway_config_airport_stats(self.prediction_input.destination.icao)
        }
