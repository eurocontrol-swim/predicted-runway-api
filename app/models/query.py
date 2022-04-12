from datetime import datetime
import pandas as pd
from .runway import TRAINED_MODELS_PER_DESTINATION_AIRPORT


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
    if airport not in TRAINED_MODELS_PER_DESTINATION_AIRPORT.keys():
        raise ModelNotFound(f'No model exists for airport = {airport}')

    if not len(origin) == 4:
        raise ValueError(f"Origin is not a valid ICAO code")

    predictor = TRAINED_MODELS_PER_DESTINATION_AIRPORT[airport]
    _result = predictor.predict_proba({"dt": dt,
                                       "origin": origin,
                                       "wind_direction": wind_direction,
                                       "wind_speed": wind_speed})
    result = pd.Series(_result[0], index=predictor.model.classes_)

    output = {'airport': airport,
              'origin': origin,
              'predictions': [
                  {"timestamp": dt.strftime('%d/%m/%Y %H:%M:%S'),
                   "arrivalRunways": [
                       {"runway": runway, "probability": probability} for runway, probability in
                       result.sort_values(ascending=False).iteritems()
                   ]}
              ]}

    return output
