from flask import request, jsonify, Blueprint
from app.domain.runway.predictor import predict_runway
import logging

from app.met.api import METNotAvailable
from app.routes.schemas import PredictionInputSchema, ValidationError, get_api_prediction_output

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route("/api/0.1/runway-prediction/arrivals", methods=['GET'])
def api_runway_prediction():

    try:
        prediction_input = PredictionInputSchema().load(**request.args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400
    except METNotAvailable as e:
        logger.exception(e)
        message = f"There is no meteorological information available for provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"error": message}), 400

    try:
        prediction_result = predict_runway(prediction_input)
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Server error"}), 500

    prediction_output = get_api_prediction_output(prediction_input, prediction_result)

    return jsonify(prediction_output), 200


@api_blueprint.route("/api/0.1/runway-config/airport/<string:airport>")
def api_runway_config_prediction(airport: str):
    return
