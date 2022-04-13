from typing import Optional

from flask import (render_template,
                   abort,
                   request,
                   flash,
                   redirect,
                   url_for,
                   Blueprint, jsonify)
from datetime import datetime, time, timezone

from app.models.airports import get_airport_data
from app.models.runway import DESTINATION_AIRPORTS
from app.routes.input_validation import *
from app.met_api import METException
from app.models.query import predict_runway
import logging


logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


web_blueprint = Blueprint('web', __name__)


@web_blueprint.route("/")
def index():
    return render_template('index.html',
                           destination_airports_data=_get_destination_airports_data())


@web_blueprint.route("/runway-prediction/arrivals/<string:airport_icao>", methods=['GET'])
def web_runway_prediction(airport_icao: str):
    origin = request.args.get('origin')
    timestamp = request.args.get('timestamp', type=int)
    if timestamp:
        timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # wind_direction = request.args.get('wind_direction')
    # wind_speed = request.args.get('wind_speed')

    # TODO: if wind data is missing get them from files
    # TODO: validate input

    if origin is None and timestamp is None:
        return _load_prediction_template(airport_icao=airport_icao)

    try:
        response = predict_runway(airport=airport_icao,
                                  dt=timestamp,
                                  origin=origin,
                                  wind_direction=None,
                                  wind_speed=None)
        return _load_prediction_template(airport_icao=airport_icao, response=response)
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            message=f"There is no meteorological information available at "
                    f"{timestamp.strftime('%d/%m/%Y %H:%M:%S')}",
            airport_icao=airport_icao)
    except ValueError as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            message="Invalid data",
            airport_icao=airport_icao
        )
    except Exception as e:
        logger.exception(e)
        return abort(500)


@web_blueprint.route("/airports-data/<string:search_value>", methods=['GET'])
def airports_data(search_value: str):
    if not search_value:
        return []

    return jsonify(
        [
            _extract_airport_data(data)
            for _, data in get_airport_data().items()
            if _airport_data_matches(data, search_value)
        ]
    ), 200


def _load_prediction_template(airport_icao: str, response: Optional[dict] = None):
    return render_template('runwayPrediction.html',
                           airport_icao=airport_icao,
                           response=response,
                           destination_airports_data=_get_destination_airports_data())


def _load_prediction_template_with_warning(message: str, airport_icao: str):
    flash(message, category="warning")
    return _load_prediction_template(airport_icao)


def _airport_data_matches(data: dict, search_value: str) -> bool:
    search_value = search_value.lower()
    searchable_keys = ['icao', 'name', 'city', 'state', 'country']

    return any(
        [search_value in data[key].lower() for key in searchable_keys]
    )


def _extract_airport_data(data: dict, with_runways: bool = False) -> dict:
    extracted = {
        "icao": data['icao'],
        "label": f"{data['icao']}: {data['name']}, {data['city']}, {data['state']}, {data['country']}"
    }

    if with_runways:
        extracted["runways"] = data.get('runways', {})

    return extracted


def _get_destination_airports_data():
    return [
        _extract_airport_data(data, with_runways=True)
        for icao, data in get_airport_data().items()
        if icao in DESTINATION_AIRPORTS
    ]
