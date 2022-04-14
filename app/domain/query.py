import pandas as pd

from app.config.file_dir import meteo_dir
from app.domain.runway.predictor import Predictor
from app.domain.runway.models import PredictionInput
from app.met_api.query import get_last_wind_speed, get_last_wind_dir


def _update_prediction_input_with_wind(prediction_input: PredictionInput) -> PredictionInput:
    prediction_input.wind_speed = get_last_wind_speed(
        met_path=meteo_dir,
        airport=prediction_input.destination_icao,
        before=prediction_input.timestamp
    )
    prediction_input.wind_direction = get_last_wind_dir(
        met_path=meteo_dir,
        airport=prediction_input.destination_icao,
        before=prediction_input.timestamp
    )

    return prediction_input


def predict_runway(prediction_input: PredictionInput) -> pd.Series:
    if prediction_input.wind_direction is None and prediction_input.wind_speed is None:
        prediction_input = _update_prediction_input_with_wind(prediction_input)

    return Predictor.predict(prediction_input)
