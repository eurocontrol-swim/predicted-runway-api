import json
import os
from typing import Optional

from flask import (render_template,
                   abort,
                   request,
                   flash,
                   redirect,
                   url_for,
                   Blueprint, jsonify)
from datetime import datetime, time, timezone

from app.config.file_dir import runway_model_metrics_dir, taf_dir
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
        response = _enhance_response_with_geodata(response)
        response = _enhance_response_with_metrics(response)

        return _load_prediction_template(airport_icao=airport_icao, response=response)
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            message=f"There is no meteorological information available at "
                    f"{timestamp.strftime('%d/%m/%Y %H:%M:%S')}. "
                    f"Please try another arrival time and/or departure airport.",
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


@web_blueprint.route("/forecast-timestamp-range/<string:airport_icao>", methods=['GET'])
def get_forecast_timestamp_range(airport_icao: str):
    start_time_datetime, end_time_datetime = _get_taf_datetime_range(airport_icao)

    delta_in_hours = int((end_time_datetime - start_time_datetime).total_seconds() / 3600)

    return {
        'start_timestamp': int(start_time_datetime.timestamp()),
        'end_timestamp': int(end_time_datetime.timestamp()),
        'delta_in_hours': delta_in_hours
    }, 200


def _get_taf_datetime_range(airport_icao) -> tuple[datetime, datetime]:
    path = taf_dir.joinpath(airport_icao)

    first_file, *_, last_file = sorted(os.listdir(path))

    with open(path.joinpath(first_file), 'r') as f:
        first_file_data = json.load(f)

    with open(path.joinpath(last_file), 'r') as f:
        last_file_data = json.load(f)

    start_time, end_time = first_file_data['start_time']['dt'], last_file_data['end_time']['dt']

    return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z"), \
        datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")


def _get_airport_metrics(airport: str):
    path = runway_model_metrics_dir.joinpath(f"CV-Test_results_{airport}_100.json")

    with open(path, 'r') as f:
        return json.load(f)


def _enhance_response_with_metrics(response):
    response['metrics'] = _get_airport_metrics(response['airport'])

    return response


def _enhance_response_with_geodata(response: dict) -> dict:
    airport_data = _get_destination_airports_data()[response['airport']]

    response['airport_coordinates'] = [airport_data['lat'], airport_data['lon']]

    for i, prediction in enumerate(response['predictions']):
        for j, runway in enumerate(prediction['arrivalRunways']):
            response['predictions'][i]['arrivalRunways'][j]['coordinates_geojson'] = \
                airport_data['runways_geojson'][runway['runway']]

    return response


def _load_prediction_template(airport_icao: str, response: Optional[dict] = None):
    destination_airports_data = _get_destination_airports_data()

    return render_template('runwayPrediction.html',
                           airport_icao=airport_icao,
                           response=response,
                           destination_airports_data=destination_airports_data)


def _load_prediction_template_with_warning(message: str, airport_icao: str):
    flash(message, category="warning")
    return _load_prediction_template(airport_icao)


def _airport_data_matches(data: dict, search_value: str) -> bool:
    search_value = search_value.lower()
    searchable_keys = ['icao', 'name', 'city', 'state', 'country']

    return any(
        [search_value in data[key].lower() for key in searchable_keys]
    )


def _reverse_coordinates_geojson(coordinates_geojson: list[list]) -> list[list]:
    return [[coord[1], coord[0]] for coord in coordinates_geojson]


def _extract_airport_data(data: dict, with_geodata: bool = False) -> dict:
    extracted = {
        "icao": data['icao'],
        "label": f"{data['icao']}: {data['name']}, {data['city']}, {data['state']}, {data['country']}"
    }

    if with_geodata:
        extracted["lat"] = data["lat"]
        extracted["lon"] = data["lon"]
        extracted["runways_geojson"] = {
            runway: _reverse_coordinates_geojson(data["coordinates_geojson"])
            for runway, data in data.get("runways", {}).items()
        }

    return extracted


def _get_destination_airports_data():
    return {
        icao: _extract_airport_data(data, with_geodata=True)
        for icao, data in get_airport_data().items()
        if icao in DESTINATION_AIRPORTS
    }
