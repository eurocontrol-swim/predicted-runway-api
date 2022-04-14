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

import pandas as pd
from joblib import load
from sklearn.ensemble import RandomForestClassifier

from app.config.file_dir import runway_models_dir
from app.domain.airports import get_airport_data
from app.domain.runway.models import PredictionInput


class Predictor:

    @staticmethod
    def predict(prediction_input: PredictionInput) -> pd.Series:
        model_inputs = Predictor._get_model_inputs(prediction_input)

        model = Predictor._get_model(prediction_input.destination_icao)

        prediction_result = model.predict_proba(model_inputs)

        return pd.Series(prediction_result[0], index=model.classes_)

    @staticmethod
    def _get_model(destination_icao: str) -> RandomForestClassifier:
        _model_path = runway_models_dir.joinpath(f'{destination_icao}.pkl').absolute()

        return load(_model_path)

    @staticmethod
    def _get_model_inputs(prediction_input: PredictionInput) -> pd.DataFrame:
        angle_icao_airports = Predictor._get_angle_icao_airports(
            origin_icao=prediction_input.origin_icao,
            destination_icao=prediction_input.destination_icao
        )

        _inputs = [
            [prediction_input.date_time_hour] +
            [prediction_input.wind_speed, prediction_input.wind_direction] +
            [angle_icao_airports]
        ]

        return pd.DataFrame(_inputs, columns=["hour", "wind_speed", "wind_dir", "origin_angle"])

    @staticmethod
    def _get_angle_icao_airports(origin_icao: str, destination_icao: str):
        icao_airports_dict = get_airport_data()

        departure_lat = icao_airports_dict[origin_icao]['lat']
        departure_lon = icao_airports_dict[origin_icao]['lon']
        destination_lat = icao_airports_dict[destination_icao]['lat']
        destination_lon = icao_airports_dict[destination_icao]['lon']

        departure_lat = math.radians(departure_lat)
        departure_lon = math.radians(departure_lon)
        destination_lat = math.radians(destination_lat)
        destination_lon = math.radians(destination_lon)

        d_lon = destination_lon - departure_lon

        y = math.sin(d_lon) * math.cos(destination_lat)
        x = math.cos(departure_lat) * math.sin(destination_lat) - math.sin(departure_lat) * math.cos(
            destination_lat) * math.cos(d_lon)

        bearing = math.atan2(y, x)

        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        # bearing = 360 - bearing (uncomment to count degrees counterclockwise)

        return bearing
