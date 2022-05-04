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

from pathlib import Path

import pandas as pd
from joblib import load
from sklearn.ensemble import RandomForestClassifier

from app.config import get_runway_model_path, get_runway_config_model_path
from app.domain.models import RunwayPredictionInput, RunwayConfigPredictionInput, \
    RunwayPredictionOutput, RunwayConfigPredictionOutput, PredictionModelOutput, RunwayProbability, \
    RunwayConfigProbability, PredictionInput


class Predictor:

    def __init__(self, trained_model: RandomForestClassifier):
        self.trained_model = trained_model

    @classmethod
    def from_path(cls, path: Path):
        return cls(trained_model=load(path))

    def predict(self, prediction_input: PredictionInput) -> PredictionModelOutput:
        features = list(self.trained_model.feature_names_in_)
        values = prediction_input.get_model_input_values(features=features)

        model_input = pd.DataFrame([values], columns=features)

        prediction_result = self.trained_model.predict_proba(model_input)

        return PredictionModelOutput(zip(self.trained_model.classes_, prediction_result[0]))


def predict_runway(prediction_input: RunwayPredictionInput) -> list[RunwayProbability]:
    model_path = get_runway_model_path(airport_icao=prediction_input.destination.icao)

    predictor = Predictor.from_path(model_path)

    model_output = predictor.predict(prediction_input=prediction_input)

    return [
        RunwayProbability(runway_name=runway_name, value=proba)
        for runway_name, proba in model_output.items()
    ]


def get_runway_prediction_output(prediction_input: RunwayPredictionInput) -> RunwayPredictionOutput:
    probas = predict_runway(prediction_input)

    return RunwayPredictionOutput(probas=probas, destination=prediction_input.destination)


def predict_runway_config(prediction_input: RunwayConfigPredictionInput) \
        -> list[RunwayConfigProbability]:

    model_path = get_runway_config_model_path(airport_icao=prediction_input.destination.icao)

    predictor = Predictor.from_path(model_path)

    model_output = predictor.predict(prediction_input=prediction_input)

    return [
        RunwayConfigProbability(runway_config=runway_config, value=proba)
        for runway_config, proba in model_output.items()
    ]


def get_runway_config_prediction_output(prediction_input: RunwayConfigPredictionInput) \
        -> RunwayConfigPredictionOutput:

    probas = predict_runway_config(prediction_input)

    return RunwayConfigPredictionOutput(probas=probas, destination=prediction_input.destination)
