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
from typing import Optional, Any

import pandas as pd

from app.config import DESTINATION_ICAOS
from app.domain.airports import get_destination_airports_data, get_destination_airport_metrics
from app.domain.runway.factory import PredictionInputFactory
from app.domain.runway.models import PredictionInput, WindInputSource


class ValidationError(Exception):
    ...


class PredictionInputSchema:
    def load(self, **kwargs):
        validated_kwargs = self._load_validated(**kwargs)

        return PredictionInputFactory.create_prediction_input(**validated_kwargs)

    def _load_validated(self, **kwargs):
        try:
            return self._validate(**kwargs)
        except TypeError:
            raise ValidationError('Invalid input.')

    def _validate(self,
                  origin_icao: str,
                  destination_icao: str,
                  timestamp: int,
                  wind_direction: Optional[float] = None,
                  wind_speed: Optional[float] = None,
                  wind_input_source: Optional[str] = None,
                  ) -> dict:
        validated_data = {
            "origin_icao": self._validate_origin_icao(origin_icao),
            "destination_icao": self._validate_destination_icao(destination_icao),
            "timestamp": self._validate_timestamp(timestamp),
        }

        if wind_direction and wind_speed:
            validated_data["wind_direction"] = self._validate_wind_direction(wind_direction)
            validated_data["wind_speed"] = self._validate_wind_speed(wind_speed)

        if wind_input_source:
            try:
                validated_data["wind_input_source"] = WindInputSource(wind_input_source)
            except ValueError:
                validated_data["wind_input_source"] = None

        return validated_data

    @staticmethod
    def _is_valid_icao(icao: str):
        return isinstance(icao, str) and len(icao) == 4

    @staticmethod
    def _validate_origin_icao(value: Any) -> str:
        if not PredictionInputSchema._is_valid_icao(value):
            raise ValidationError("origin_icao should be a string of 4 characters.")

        return value.upper()

    @staticmethod
    def _validate_destination_icao(value: Any) -> str:
        if not PredictionInputSchema._is_valid_icao(value):
            raise ValidationError("destination_icao should be a string of 4 characters.")

        if value not in DESTINATION_ICAOS:
            raise ValidationError(f"destination_icao should be one of {', '.join(DESTINATION_ICAOS)}.")

        return value.upper()

    @staticmethod
    def _validate_timestamp(value: Any) -> int:
        if not (isinstance(value, int)):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError("timestamp should be an integer.")

        try:
            datetime.fromtimestamp(value)
        except (TypeError, ValueError, OSError, OverflowError):
            raise ValidationError("Invalid timestamp.")

        return value

    @staticmethod
    def _validate_wind_direction(value: Any) -> float:
        if not isinstance(value, int):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValidationError("wind_direction should be a float.")

        if not 0 <= value <= 360:
            raise ValidationError('wind_direction should be between 0 and 360.')

        return value

    @staticmethod
    def _validate_wind_speed(value: any) -> float:
        if not isinstance(value, int):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValidationError("wind_speed should be a float.")

        if value < 0:
            raise ValidationError('wind_speed should be positive.')

        return value


class PredictionOutputContext:
    def __init__(self,
                 prediction_input: PredictionInput,
                 prediction_result: pd.Series,
                 ):
        self.prediction_input = prediction_input
        self.prediction_result = prediction_result
        self.prediction_output = {}


class RunwaysProbabilitiesBuilder:
    @classmethod
    def build(cls, context: PredictionOutputContext):
        context.prediction_output = {
            "runways": [
               {"name": runway, "probability": probability} for runway, probability in
               context.prediction_result.sort_values(ascending=False).items()
           ]
        }



class PredictionInputBuilder:
    @classmethod
    def build(cls, context: PredictionOutputContext):
        context.prediction_output["prediction_input"] = context.prediction_input.to_dict()


class GeodataBuilder:
    @classmethod
    def build(cls, context: PredictionOutputContext):
        airport_data = get_destination_airports_data()[context.prediction_input.destination_icao]

        context.prediction_output['airport_coordinates'] = [airport_data['lat'], airport_data['lon']]

        for i, runway in enumerate(context.prediction_output['runways']):
            context.prediction_output['runways'][i]['coordinates_geojson'] = \
                airport_data['runways_geodata'][runway['name']]['geojson']
            context.prediction_output['runways'][i]['true_bearing'] = \
                airport_data['runways_geodata'][runway['name']]['true_bearing']


class MetricsBuilder:
    @classmethod
    def build(cls, context: PredictionOutputContext):
        context.prediction_output['metrics'] = get_destination_airport_metrics(
            context.prediction_input.destination_icao
        )


def get_web_prediction_output(prediction_input: PredictionInput,
                              prediction_result: pd.Series):

    context = PredictionOutputContext(prediction_input,
                                      prediction_result)

    for builder in [RunwaysProbabilitiesBuilder,
                    PredictionInputBuilder,
                    GeodataBuilder,
                    MetricsBuilder]:
        builder.build(context)

    return context.prediction_output


def get_api_prediction_output(prediction_input: PredictionInput,
                              prediction_result: pd.Series):

    context = PredictionOutputContext(prediction_input,
                                      prediction_result)

    for builder in [RunwaysProbabilitiesBuilder]:
        builder.build(context)

    return context.prediction_output
