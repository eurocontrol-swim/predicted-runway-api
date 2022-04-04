from flask import (abort,
                   request,
                   jsonify,
                   Blueprint)
from app.models.query import predict_runway
from datetime import datetime
import logging


logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route("/api/0.1/runway-prediction/airport/<string:airport>", methods=['GET'])
def api_runway_prediction(airport: str):
    args = request.args
    origin = args.get('origin', type=str)

    # These two are optional, if provided we use user input. Otherwise attempt to retrieve
    wind_direction = args.get('wind-dir', type=float)
    wind_speed = args.get('wind-speed', type=float)

    try:
        response = predict_runway(airport=airport,
                                  dt=datetime.now(),
                                  origin=origin)
        return jsonify(response)
    except ValueError:
        logger.exception("An error occurred parsing the inputs")
        return abort(400)


@api_blueprint.route("/api/0.1/runway-config/airport/<string:airport>")
def api_runway_config_prediction(airport: str):
    return
