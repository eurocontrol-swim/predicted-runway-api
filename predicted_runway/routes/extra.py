"""
Copyright 2022 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of
conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to
endorse
   or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open
Source Initiative: http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""

__author__ = "EUROCONTROL (SWIM)"

import flask as f
from flask import jsonify
from met_update_db import repo as met_repo

from predicted_runway.adapters import airports as airports_api, stats
from predicted_runway.config import DESTINATION_ICAOS


def get_airports_data(search: str):
    airports = airports_api.get_airports(search=search)

    result = [{"title": airport.title} for airport in airports]

    return f.jsonify(result), 200


def get_latest_taf_end_time(destination_icao: str):
    if destination_icao not in DESTINATION_ICAOS:
        return jsonify({
            "detail": f'destination_icao should be one of {", ".join(DESTINATION_ICAOS)}'
        }), 404

    try:
        end_time_datetime = met_repo.get_last_taf_end_time(airport_icao=destination_icao)
    except met_repo.METNotAvailable:
        return {"detail": "Couldn't determine a future time window because no meteorological data "
                          "are available at the moment. Please try again later."}, 409

    return {
        'end_timestamp': int(end_time_datetime.timestamp())
    }, 200


def get_arrivals_runway_prediction_stats(destination_icao: str):
    if destination_icao not in DESTINATION_ICAOS:
        return jsonify({
            "detail": f'destination_icao should be one of {", ".join(DESTINATION_ICAOS)}'
        }), 404

    result = stats.get_arrivals_runway_airport_stats(destination_icao=destination_icao)

    return result, 200


def get_arrivals_runway_config_prediction_stats(destination_icao: str):
    if destination_icao not in DESTINATION_ICAOS:
        return jsonify({
            "detail": f'destination_icao should be one of {", ".join(DESTINATION_ICAOS)}'
        }), 404

    result = stats.get_arrivals_runway_config_airport_stats(destination_icao=destination_icao)

    return result, 200
