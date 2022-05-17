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

from typing import Any
from dataclasses import dataclass
from datetime import datetime

import marshmallow as ma

from predicted_runway.config import DESTINATION_ICAOS
from predicted_runway.adapters.stats import get_runway_airport_stats, get_runway_config_airport_stats
from predicted_runway.domain.models import RunwayPredictionInput, WindInputSource, RunwayConfigPredictionInput, \
    RunwayPredictionOutput, RunwayConfigPredictionOutput


def _is_valid_icao(icao: str):
    return isinstance(icao, str) and len(icao) == 4


def _validate_origin_icao(value: Any) -> str:
    if not _is_valid_icao(value):
        raise ma.ValidationError("Should be a string of 4 characters.")

    return value


def _validate_destination_icao(value: Any) -> str:
    if not _is_valid_icao(value):
        raise ma.ValidationError("Should be a string of 4 characters.")

    if value not in DESTINATION_ICAOS:
        raise ma.ValidationError(f"Should be one of {', '.join(DESTINATION_ICAOS)}.")

    return value


def _validate_timestamp(value: Any) -> int:
    if not (isinstance(value, int)):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ma.ValidationError("Should be an integer.")

    try:
        datetime.fromtimestamp(value)
    except (TypeError, ValueError, OSError, OverflowError):
        raise ma.ValidationError("Invalid timestamp.")

    return value


def _validate_wind_direction(value: Any) -> float:
    if not isinstance(value, int):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ma.ValidationError("Should be a float.")

    if not 0 <= value <= 360:
        raise ma.ValidationError('Should be between 0 and 360.')

    return value


def _validate_wind_speed(value: Any) -> float:
    if not isinstance(value, int):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ma.ValidationError("Should be a float.")

    if value < 0:
        raise ma.ValidationError('Should be positive.')

    return value


def _validate_wind_input_source(value: Any) -> str:
    try:
        WindInputSource(value)
    except ValueError:
        raise ma.ValidationError('Invalid wind_input_source')

    return value


class PredictionInputSchema(ma.Schema):
    destination_icao = ma.fields.Str(required=True, validate=_validate_destination_icao)
    timestamp = ma.fields.Int(required=True, validate=_validate_timestamp)
    wind_speed = ma.fields.Float(validate=_validate_wind_speed)
    wind_direction = ma.fields.Float(validate=_validate_wind_direction)
    wind_input_source = ma.fields.Str(validate=_validate_wind_input_source)


class RunwayPredictionInputSchema(PredictionInputSchema):
    origin_icao = ma.fields.Str(required=True, validate=_validate_origin_icao)


class RunwayConfigPredictionInputSchema(PredictionInputSchema):
    ...


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
