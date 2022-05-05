from flask import request, jsonify, Blueprint
from app.domain.predictor import  get_runway_prediction_output, \
    get_runway_config_prediction_output
import logging

from app.adapters.met.api import METNotAvailable
from app.routes.factory import RunwayPredictionInputFactory, RunwayConfigPredictionInputFactory
from app.routes.schemas import ValidationError, RunwayPredictionInputSchema, \
    RunwayConfigPredictionInputSchema, RunwayConfigPredictionOutputSchema, \
    RunwayPredictionOutputSchema

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route("/api/0.1/runway-prediction/arrivals", methods=['GET'])
def runway_prediction():

    try:
        validated_input = RunwayPredictionInputSchema().validate(**request.args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400

    try:
        prediction_input = RunwayPredictionInputFactory.create(**validated_input)
    except METNotAvailable as e:
        logger.exception(e)
        message = f"There is no meteorological information available for provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"error": message}), 400

    try:
        prediction_output = get_runway_prediction_output(prediction_input)
    except Exception as e:
        logger.exception(e)
        return jsonify({
            "error": "Something went wrong during the prediction. Please try again later."
        }), 500

    result = RunwayPredictionOutputSchema(prediction_input, prediction_output).to_api()

    return jsonify(result), 200


@api_blueprint.route("/api/0.1/runway-config-prediction/arrivals")
def runway_config_prediction():

    try:
        validated_input = RunwayConfigPredictionInputSchema().validate(**request.args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400

    try:
        prediction_input = RunwayConfigPredictionInputFactory.create(**validated_input)
    except METNotAvailable as e:
        logger.exception(e)
        message = f"There is no meteorological information available for provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"error": message}), 400

    try:
        prediction_output = get_runway_config_prediction_output(prediction_input)
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Server error"}), 500

    result = RunwayConfigPredictionOutputSchema(prediction_input, prediction_output).to_api()

    return jsonify(result), 200
