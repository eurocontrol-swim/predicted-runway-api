import logging
from typing import Optional

from flask import (render_template,
                   abort,
                   request,
                   flash,
                   Blueprint, jsonify, redirect, url_for)

from app.met import METException
from app.met.api import get_taf_datetime_range
from app.domain.runway.predictor import predict_runway
from app.domain.airports import get_destination_airports_data, search_airport_data
from app.routes.schemas import PredictionInputSchema, get_web_prediction_output, ValidationError

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


web_blueprint = Blueprint('web', __name__)


@web_blueprint.route("/")
def index():
    return render_template('index.html',
                           destination_airports_data=get_destination_airports_data())


@web_blueprint.route("/runway-prediction/arrivals", methods=['GET', 'POST'])
def web_runway_prediction():
    if request.method == 'GET':
        return _get_web_runway_prediction()

    if request.method == 'POST':
        return _post_web_runway_prediction()


def _post_web_runway_prediction():
    input_data = dict(request.form)

    try:
        prediction_input = PredictionInputSchema().load(**input_data)
    except ValidationError as e:
        return _load_prediction_template_with_warning(message=str(e))
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            f"There is no meteorological information available for provided timestamp. "
            f"Please try again with different value.")

    return redirect(url_for('web.web_runway_prediction', **prediction_input.to_query_string_dict()))


def _get_web_runway_prediction():

    try:
        prediction_input = PredictionInputSchema().load(**request.args)
    except ValidationError as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(message=str(e))
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            f"There is no meteorological information available for the wind input. "
            f"Please try again with different source or custom values.")

    try:
        prediction_result = predict_runway(prediction_input)
    except Exception as e:
        logger.exception(e)
        return abort(500)

    prediction_output = get_web_prediction_output(prediction_input, prediction_result)

    return _load_prediction_template(prediction_output=prediction_output)


@web_blueprint.route("/airports-data/<string:search_value>", methods=['GET'])
def airports_data(search_value: str):
    if not search_value:
        return []

    result = search_airport_data(search_value)

    return jsonify(result), 200


@web_blueprint.route("/forecast-timestamp-range/<string:destination_icao>", methods=['GET'])
def get_forecast_timestamp_range(destination_icao: str):
    start_time_datetime, end_time_datetime = get_taf_datetime_range(destination_icao)

    return {
        'start_timestamp': int(start_time_datetime.timestamp()),
        'end_timestamp': int(end_time_datetime.timestamp()),
    }, 200


def _load_prediction_template(prediction_output: Optional[dict] = None):
    destination_airports_data = get_destination_airports_data()

    return render_template('runwayPrediction.html',
                           prediction_output=prediction_output,
                           destination_airports_data=destination_airports_data)


def _load_prediction_template_with_warning(message: str):
    flash(message, category="warning")
    return _load_prediction_template()


