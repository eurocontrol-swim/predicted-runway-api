from flask import request, jsonify, Blueprint
from marshmallow import ValidationError

from predicted_runway.domain.predictor import  get_runway_prediction_output, \
    get_runway_config_prediction_output
import logging

from predicted_runway.adapters.met.api import METNotAvailable
from predicted_runway.routes.factory import RunwayPredictionInputFactory, RunwayConfigPredictionInputFactory
from predicted_runway.routes.schemas import RunwayPredictionInputSchema, \
    RunwayConfigPredictionInputSchema, RunwayConfigPredictionOutputSchema, \
    RunwayPredictionOutputSchema

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


def runway_prediction():

    try:
        validated_input = RunwayPredictionInputSchema().load(request.args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400

    try:
        prediction_input = RunwayPredictionInputFactory.create(**validated_input)
    except METNotAvailable as e:
        logger.exception(e)
        message = f"There is no meteorological information available for provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"error": message}), 409

    try:
        prediction_output = get_runway_prediction_output(prediction_input)
    except Exception as e:
        logger.exception(e)
        return jsonify({
            "error": "Something went wrong during the prediction. Please try again later."
        }), 500

    result = RunwayPredictionOutputSchema(prediction_input, prediction_output).to_api()

    return jsonify(result), 200


def runway_config_prediction():

    try:
        validated_input = RunwayConfigPredictionInputSchema().load(request.args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400

    try:
        prediction_input = RunwayConfigPredictionInputFactory.create(**validated_input)
    except METNotAvailable as e:
        logger.exception(e)
        message = f"There is no meteorological information available for provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"error": message}), 409

    try:
        prediction_output = get_runway_config_prediction_output(prediction_input)
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Server error"}), 500

    result = RunwayConfigPredictionOutputSchema(prediction_input, prediction_output).to_api()

    return jsonify(result), 200
