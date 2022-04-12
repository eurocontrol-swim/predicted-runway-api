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


@web_blueprint.route("/runway-prediction/airport/<string:airport>", methods=['GET'])
def web_runway_prediction(airport: str):
    origin = request.args.get('origin')
    timestamp = request.args.get('timestamp', type=int)
    # wind_direction = request.args.get('wind_direction')
    # wind_speed = request.args.get('wind_speed')

    try:
        response = predict_runway(airport=airport,
                                  dt=datetime.fromtimestamp(timestamp),
                                  origin=origin,
                                  wind_direction=None,
                                  wind_speed=None)
        return render_template('runwayPrediction.html', response=response)
    except METException as e:
        logger.exception(e)
        return _reload_form_with_warning(
            "We don't have meteorological information available for the given timestamp.",
            airport=airport)
    except ValueError as e:
        logger.exception(e)
        return _reload_form_with_warning("Invalid data", airport=airport)
    except Exception as e:
        logger.exception(e)
        return abort(500)


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


@web_blueprint.route("/runway-prediction/airport/<string:airport>/form", methods=['GET', 'POST'])
def web_runway_prediction_form(airport: str):
    if request.method == 'GET':
        return render_template('runwayPredictionForm.html',
                               airport=airport,
                               origin_airports_data=_get_origin_airports_data())

    if request.method == 'POST':
        origin = request.form.get('origin')
        if not valid_icao_code(icao_code=origin):
            return _reload_form_with_warning("ICAO code not valid.", airport=airport)

        timestamp = request.form.get('timestamp', type=int)
        try:
            datetime.fromtimestamp(timestamp)
        except Exception:
            return _reload_form_with_warning("Timestamp not valid.", airport=airport)

        # wind_direction = request.form.get('wind-dir', type=float, default=None)
        # if wind_direction is not None:
        #     if not valid_wind_direction(wind_direction):
        #         return _reload_form_with_warning(
        #             "Wind direction must be a number in the range [0, 360)",
        #             airport=airport)
        #
        # wind_speed = request.form.get('wind-speed', type=float, default=None)
        # if wind_speed is not None:
        #     if not valid_wind_speed(wind_speed):
        #         return _reload_form_with_warning("Wind speed must be a positive number",
        #                                          airport=airport)

        return redirect(
            url_for(
                'web.web_runway_prediction',
                airport=airport,
                timestamp=timestamp,
                origin=origin,
                # wind_direction=wind_direction,
                # wind_speed=wind_speed
            )
        )
