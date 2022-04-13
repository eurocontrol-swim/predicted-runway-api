from typing import Optional

from flask import (render_template,
                   abort,
                   request,
                   flash,
                   redirect,
                   url_for,
                   Blueprint)
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
    return render_template('index.html', airports=DESTINATION_AIRPORTS)


@web_blueprint.route("/runway-prediction/arrivals", methods=['GET'])
def web_runway_prediction():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    timestamp = request.args.get('timestamp', type=int)
    if timestamp:
        timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # wind_direction = request.args.get('wind_direction')
    # wind_speed = request.args.get('wind_speed')

    # TODO: validate input

    if origin is None and destination is None and timestamp is None:
        return _load_prediction_template()

    try:
        response = predict_runway(airport=destination,
                                  dt=timestamp,
                                  origin=origin,
                                  wind_direction=None,
                                  wind_speed=None)
        return _load_prediction_template(response=response)
    except METException as e:
        logger.exception(e)
        return _load_prediction_template_with_warning(
            f"We don't have meteorological information available at "
            f"{timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    except ValueError as e:
        logger.exception(e)
        return _load_prediction_template_with_warning("Invalid data")
    except Exception as e:
        logger.exception(e)
        return abort(500)


def _load_prediction_template(response: Optional[dict] = None):
    return render_template('runwayPrediction.html',
                           response=response,
                           origin_airports_data=_get_origin_airports_data(),
                           destination_airports=DESTINATION_AIRPORTS)


def _load_prediction_template_with_warning(message: str):
    flash(message, category="warning")
    return _load_prediction_template()


def _reload_form_with_warning(message: str, airport: str):
    flash(message, category="warning")
    return redirect(url_for('web.web_runway_prediction_form', airport=airport))


def _get_origin_airports_data():
    airport_data = get_airport_data()

    return [
        {
            "icao": icao,
            "label": f"{icao}: {data['name']}, {data['city']}, {data['state']}, {data['country']}"
        }

        for icao, data in airport_data.items()
    ]
