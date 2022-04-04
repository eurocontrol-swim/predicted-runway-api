from datetime import datetime
import pandas as pd
from .runway import models as runway_models


class ModelNotFound(Exception):
    def __init__(self, message="Model not found"):
        self.message = message
        super().__init__(self.message)


def predict_runway(airport: str,
                   dt: datetime,
                   origin: str,
                   wind_direction: float=None,
                   wind_speed: float=None):
    airport = airport.upper()
    if airport not in runway_models.keys():
        raise ModelNotFound(f'No model exists for airport = {airport}')

    if not origin.isalpha():
        raise ValueError('Origin = {} is not alphanumeric'.format(origin))

    if not len(origin) == 4:
        raise ValueError(f"Origin is not a valid ICAO code")

    predictor = runway_models[airport]
    _result = predictor.predict_proba({"dt": dt,
                                       "origin": origin,
                                       "wind_direction": wind_direction,
                                       "wind_speed": wind_speed})
    result = pd.Series(_result[0], index=predictor.model.classes_)

    output = {'airport': airport,
              'predictions': [
                  {"timestamp": dt.isoformat(),
                   "arrivalRunways": [
                       {"runway": runway, "probability": probability} for runway, probability in
                       result.sort_values(ascending=False).iteritems()
                   ]}
              ]}

    return output
