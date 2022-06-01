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

import logging

from flask import request, jsonify
from marshmallow import ValidationError

from met_update_db import repo as met_repo

from predicted_runway.domain import predictor
from predicted_runway.routes.factory import RunwayPredictionInputFactory, \
    RunwayConfigPredictionInputFactory
from predicted_runway.routes.schemas import RunwayPredictionInputSchema, \
    RunwayConfigPredictionInputSchema, RunwayConfigPredictionOutputSchema, \
    RunwayPredictionOutputSchema

_logger = logging.getLogger(__name__)


def runway_prediction():

    try:
        validated_input = RunwayPredictionInputSchema().load(request.args)
    except ValidationError as e:
        _logger.exception(e)
        return jsonify({"detail": str(e)}), 400

    try:
        prediction_input = RunwayPredictionInputFactory.create(**validated_input)
    except met_repo.METNotAvailable as e:
        _logger.exception(e)
        message = f"There is no meteorological information available for the provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"detail": message}), 409

    try:
        prediction_output = predictor.get_runway_prediction_output(prediction_input)
    except Exception as e:
        _logger.exception(e)
        return jsonify({
            "detail": "Something went wrong during the prediction. Please try again later."
        }), 500

    result = RunwayPredictionOutputSchema(prediction_input, prediction_output).to_api_response()

    return jsonify(result), 200


def runway_config_prediction():

    try:
        validated_input = RunwayConfigPredictionInputSchema().load(request.args)
    except ValidationError as e:
        _logger.exception(e)
        return jsonify({"detail": str(e)}), 400

    try:
        prediction_input = RunwayConfigPredictionInputFactory.create(**validated_input)
    except met_repo.METNotAvailable as e:
        _logger.exception(e)
        message = f"There is no meteorological information available for the provided timestamp. " \
                  f"Please try again with different value."
        return jsonify({"detail": message}), 409

    try:
        prediction_output = predictor.get_runway_config_prediction_output(prediction_input)
    except Exception as e:
        _logger.exception(e)
        return jsonify({
            "detail": "Something went wrong during the prediction. Please try again later."
        }), 500

    result = RunwayConfigPredictionOutputSchema(prediction_input,
                                                prediction_output).to_api_response()

    return jsonify(result), 200
