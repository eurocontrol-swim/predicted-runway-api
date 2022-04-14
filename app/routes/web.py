import json
import os
from typing import Optional

from flask import (render_template,
                   abort,
                   request,
                   flash,
                   Blueprint, jsonify)
from datetime import datetime

from app.config.file_dir import taf_dir
from app.domain.airports import extract_airport_data, get_destination_airports_data, \
    get_airport_data
from app.met_api import METException
from app.domain.query import predict_runway
import logging

from app.routes.schemas import PredictionInputSchema, get_web_prediction_output, ValidationError

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


web_blueprint = Blueprint('web', __name__)


@web_blueprint.route("/")
def index():
    return render_template('index.html',
                           destination_airports_data=get_destination_airports_data())


@web_blueprint.route("/runway-prediction/arrivals/<string:destination_icao>", methods=['GET'])
def web_runway_prediction(destination_icao: str):

    request_args = dict(request.args)
    request_args.update({'destination_icao': destination_icao})
    try:
        prediction_input = PredictionInputSchema().load(**request_args)
    except ValidationError as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(message=str(e), destination_icao=destination_icao)
    except Exception as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(message="Invalid input.",
                                                      destination_icao=destination_icao)

    try:
        prediction_result = predict_runway(prediction_input=prediction_input)
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            f"There is no meteorological information available for {prediction_input.date_time_str}. "
            f"Please try another arrival time and/or departure airport.",
            destination_icao=destination_icao)
    except Exception as e:
        logger.exception(e)
        return abort(500)

    prediction_output = get_web_prediction_output(destination_icao=destination_icao,
                                                  prediction_input=prediction_input,
                                                  prediction_result=prediction_result)

    return _load_prediction_template(destination_icao=destination_icao,
                                     prediction_output=prediction_output)


@web_blueprint.route("/airports-data/<string:search_value>", methods=['GET'])
def airports_data(search_value: str):
    if not search_value:
        return []

    return jsonify(
        [
            extract_airport_data(data)
            for _, data in get_airport_data().items()
            if _airport_data_matches(data, search_value)
        ]
    ), 200


@web_blueprint.route("/forecast-timestamp-range/<string:destination_icao>", methods=['GET'])
def get_forecast_timestamp_range(destination_icao: str):
    start_time_datetime, end_time_datetime = _get_taf_datetime_range(destination_icao)

    delta_in_hours = int((end_time_datetime - start_time_datetime).total_seconds() / 3600)

    return {
        'start_timestamp': int(start_time_datetime.timestamp()),
        'end_timestamp': int(end_time_datetime.timestamp()),
        'delta_in_hours': delta_in_hours
    }, 200


def _get_taf_datetime_range(destination_icao) -> tuple[datetime, datetime]:
    path = taf_dir.joinpath(destination_icao)

    first_file, *_, last_file = sorted(os.listdir(path))

    with open(path.joinpath(first_file), 'r') as f:
        first_file_data = json.load(f)

    with open(path.joinpath(last_file), 'r') as f:
        last_file_data = json.load(f)

    start_time, end_time = first_file_data['start_time']['dt'], last_file_data['end_time']['dt']

    return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z"), \
        datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")


# def _enhance_response_with_metrics(response):
#     response['metrics'] = get_destination_airport_metrics(response['airport'])
#
#     return response
#
#
# def _enhance_response_with_geodata(response: dict) -> dict:
#     airport_data = get_destination_airports_data()[response['airport']]
#
#     response['airport_coordinates'] = [airport_data['lat'], airport_data['lon']]
#
#     for i, prediction in enumerate(response['predictions']):
#         for j, runway in enumerate(prediction['arrivalRunways']):
#             response['predictions'][i]['arrivalRunways'][j]['coordinates_geojson'] = \
#                 airport_data['runways_geojson'][runway['runway']]
#
#     return response


def _load_prediction_template(destination_icao: str, prediction_output: Optional[dict] = None):
    destination_airports_data = get_destination_airports_data()

    return render_template('runwayPrediction.html',
                           destination_icao=destination_icao,
                           prediction_output=prediction_output,
                           destination_airports_data=destination_airports_data)


def _load_prediction_template_with_warning(message: str, destination_icao: str):
    flash(message, category="warning")
    return _load_prediction_template(destination_icao)


def _airport_data_matches(data: dict, search_value: str) -> bool:
    search_value = search_value.lower()
    searchable_keys = ['icao', 'name', 'city', 'state', 'country']

    return any(
        [search_value in data[key].lower() for key in searchable_keys]
    )
