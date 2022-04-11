from flask import (render_template,
                   abort,
                   request,
                   flash,
                   redirect,
                   url_for,
                   Blueprint)
from datetime import datetime, time, timezone

from app.models.runway import AIRPORTS
from app.routes.input_validation import *
from app.met_api import METException
from app.models.query import predict_runway
import logging


logging.basicConfig(format='[%(asctime)s] - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


web_blueprint = Blueprint('web', __name__)


@web_blueprint.route("/")
def index():
    return render_template('index.html', airports=AIRPORTS)


@web_blueprint.route("/runway-prediction/airport/<string:airport>", methods=['GET', 'POST'])
def web_runway_prediction(airport: str):
    if request.method == 'GET':
        return render_template('runwayPredictionForm.html', airport=airport)
    if request.method == 'POST':
        origin = request.form.get('origin')
        if not valid_icao_code(icao_code=origin):
            flash("ICAO code not valid.",
                  category="warning")
            return redirect(url_for('web.web_runway_prediction', airport=airport))
        date_input = request.form.get('date', type=str)
        hour = request.form.get('hour', type=int)

        try:
            parsed_date = datetime.strptime(date_input, "%Y/%m/%d")
            parsed_hour = time(hour=hour)
            dt = datetime.combine(parsed_date, parsed_hour, tzinfo=timezone.utc)
        except Exception:
            flash("Date and/or hour format not valid.",
                  category="warning")
            return redirect(url_for('web.web_runway_prediction', airport=airport))

        wind_direction = request.form.get('wind-dir', type=float, default=None)
        if wind_direction is not None:
            if not valid_wind_direction(wind_direction):
                flash("Wind direction must be a number in the range [0, 360)",
                      category="warning")
                return redirect(url_for('web.web_runway_prediction', airport=airport))

        wind_speed = request.form.get('wind-speed', type=float, default=None)
        if wind_speed is not None:
            if not valid_wind_speed(wind_speed):
                flash("Wind speed must be a positive number",
                      category="warning")
                return redirect(url_for('web.web_runway_prediction', airport=airport))

        try:
            response = predict_runway(airport=airport,
                                      dt=dt,
                                      origin=origin,
                                      wind_direction=wind_direction,
                                      wind_speed=wind_speed)
            return render_template('runwayPrediction.html', response=response)
        except METException as e:
            logger.exception(e)
            flash("We don't have meteorological information available for the given date and hour. You can use the optional fields to introduce your own estimates.",
                  category="warning")
            return redirect(url_for('web.web_runway_prediction', airport=airport))
        except ValueError as e:
            logger.exception(e)
            return abort(400)
        except Exception as e:
            logger.exception(e)
            return abort(500)
