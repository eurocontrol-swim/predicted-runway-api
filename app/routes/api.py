from flask import (abort,
                   request,
                   jsonify,
                   Blueprint)
from app.domain.runway.predictor import predict_runway
from datetime import datetime
import logging

from app.met_api import METException
from app.routes.schemas import PredictionInputSchema, ValidationError, get_api_prediction_output

logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route("/api/0.1/runway-prediction/arrivals/<string:destination_icao>", methods=['GET'])
def api_runway_prediction(destination_icao: str):

    request_args = dict(request.args)
    request_args.update({'destination_icao': destination_icao})
    try:
        prediction_input = PredictionInputSchema().load(**request_args)
    except ValidationError as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Invalid input"}), 400

    try:
        prediction_result = predict_runway(prediction_input=prediction_input)
    except METException as e:
        logger.exception(e)
        message = f"There is no meteorological information available for "\
                  f"{prediction_input.date_time_str}. "\
                  f"Please try another arrival time and/or departure airport."
        return jsonify({"error": message}), 400

    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Internal error"}), 500

    prediction_output = get_api_prediction_output(prediction_input=prediction_input,
                                                  prediction_result=prediction_result)

    return jsonify(prediction_output), 200


@api_blueprint.route("/api/0.1/runway-config/airport/<string:airport>")
def api_runway_config_prediction(airport: str):
    return
