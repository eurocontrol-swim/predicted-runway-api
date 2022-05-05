import logging
from typing import Optional

from flask import render_template, request, flash, Blueprint, jsonify, redirect, url_for

from app.adapters.airports import get_destination_airports, get_airports
from app.adapters.met.api import get_taf_datetime_range, METNotAvailable
from app.domain.predictor import get_runway_prediction_output, \
    get_runway_config_prediction_output
from app.routes.factory import RunwayPredictionInputFactory, RunwayConfigPredictionInputFactory
from app.routes.schemas import ValidationError, RunwayPredictionInputSchema, \
    RunwayConfigPredictionInputSchema, RunwayPredictionOutputSchema, \
    RunwayConfigPredictionOutputSchema

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


web_blueprint = Blueprint('web', __name__)


@web_blueprint.route("/")
def index():
    return render_template('index.html',
                           destination_airports=get_destination_airports())


@web_blueprint.route("/runway-prediction/arrivals", methods=['GET', 'POST'])
def runway_prediction():
    if request.method == 'GET':
        return _get_runway_prediction()

    if request.method == 'POST':
        return _post_runway_prediction()


def _message_invalid_request_exception(exc: Exception) -> str:
    mapper = {
        ValidationError: str(exc),
        METNotAvailable:
            f"There is no meteorological information available for the provided timestamp. "
            f"Please try again with different value."
    }
    return mapper.get(type(exc), "Invalid input.")


def _runway_prediction_input_from_input_data(input_data):
    validated_input = RunwayPredictionInputSchema().load(input_data)

    return RunwayPredictionInputFactory.create(**validated_input)


def _post_runway_prediction():
    try:
        prediction_input = _runway_prediction_input_from_input_data(input_data=dict(request.form))
    except Exception as exc:
        message = _message_invalid_request_exception(exc)
        return _load_runway_prediction_template_with_warning(message)

    return redirect(url_for('web.runway_prediction', **prediction_input.to_dict()))


def _get_runway_prediction():

    try:
        prediction_input = _runway_prediction_input_from_input_data(input_data=request.args)
    except Exception as exc:
        logger.exception(exc)
        message = _message_invalid_request_exception(exc)
        return _load_runway_prediction_template_with_warning(message)

    try:
        prediction_output = get_runway_prediction_output(prediction_input)
    except Exception as exc:
        logger.exception(exc)
        return _load_runway_prediction_template_with_warning(
            "Something went wrong during the prediction. Please try again later."
        )

    result = RunwayPredictionOutputSchema(prediction_input, prediction_output).to_web()

    return _load_runway_prediction_template(result=result)


def _runway_config_prediction_input_from_input_data(input_data):
    validated_input = RunwayConfigPredictionInputSchema().load(input_data)

    return RunwayConfigPredictionInputFactory.create(**validated_input)


def _get_runway_config_prediction():

    try:
        prediction_input = _runway_config_prediction_input_from_input_data(input_data=request.args)
    except Exception as exc:
        logger.exception(exc)
        message = _message_invalid_request_exception(exc)
        return _load_runway_config_prediction_template_with_warning(message)

    try:
        prediction_output = get_runway_config_prediction_output(prediction_input)
    except Exception as exc:
        logger.exception(exc)
        return _load_runway_config_prediction_template_with_warning(
            "Something went wrong during the prediction. Please try again later."
        )

    result = RunwayConfigPredictionOutputSchema(prediction_input, prediction_output).to_web()

    return _load_runway_config_prediction_template(result=result)


def _post_runway_config_prediction():
    try:
        prediction_input = _runway_config_prediction_input_from_input_data(
            input_data=dict(request.form))
    except Exception as exc:
        logger.exception(exc)
        message = _message_invalid_request_exception(exc)
        return _load_runway_prediction_template_with_warning(message)

    return redirect(url_for('web.runway_config_prediction',
                            **prediction_input.to_dict()))


@web_blueprint.route("/runway-config-prediction/arrivals", methods=['GET', 'POST'])
def runway_config_prediction():
    if request.method == 'GET':
        return _get_runway_config_prediction()

    if request.method == 'POST':
        return _post_runway_config_prediction()


@web_blueprint.route("/airports-data/<string:search>", methods=['GET'])
def airports_data(search: str):
    if not search:
        return []

    airports = get_airports(search=search)

    result = [{"title": airport.title} for airport in airports]

    return jsonify(result), 200


@web_blueprint.route("/forecast-timestamp-range/<string:destination_icao>", methods=['GET'])
def get_forecast_timestamp_range(destination_icao: str):
    try:
        start_time_datetime, end_time_datetime = get_taf_datetime_range(destination_icao)
    except METNotAvailable:
        return {"error": "No meteorological data available"}, 404

    return {
        'start_timestamp': int(start_time_datetime.timestamp()),
        'end_timestamp': int(end_time_datetime.timestamp()),
    }, 200


def _load_runway_prediction_template(result: Optional[dict] = None):
    destination_airports = get_destination_airports()

    return render_template('runwayPrediction.html',
                           result=result,
                           destination_airports=destination_airports)


def _load_runway_prediction_template_with_warning(message: str):
    flash(message, category="warning")
    return _load_runway_prediction_template()


def _load_runway_config_prediction_template(result: Optional[dict] = None):
    destination_airports = get_destination_airports()

    return render_template('runwayConfigPrediction.html',
                           result=result,
                           destination_airports=destination_airports)


def _load_runway_config_prediction_template_with_warning(message: str):
    flash(message, category="warning")
    return _load_runway_config_prediction_template()


