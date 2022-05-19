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

import pytest

from predicted_runway.domain.factory import RunwayFactory, AirportFactory
from predicted_runway.domain.models import Runway, Airport


@pytest.mark.parametrize('name, data, expected_runway', [
    (
        '19',
        {
            "true_bearing": 194.43,
            "coordinates_geojson": [
                [
                    4.501238888888889,
                    50.91101111111111
                ],
                [
                    4.491577777777778,
                    50.88733055555556
                ]
            ]
        },
        Runway(
            name='19',
            true_bearing=194.43,
            coordinates_geojson=[
                [
                    4.501238888888889,
                    50.91101111111111
                ],
                [
                    4.491577777777778,
                    50.88733055555556
                ]
            ]
        )
    )
])
def test_runway_factory(name, data, expected_runway):
    assert RunwayFactory.create_from_data(name, data) == expected_runway


@pytest.mark.parametrize('data, expected_airport', [
    (
        {
            "icao": "EBBR",
            "iata": "BRU",
            "name": "Brussels Airport",
            "city": "Brussels",
            "state": "Flanders",
            "country": "BE",
            "elevation": 184,
            "lat": 50.9014015198,
            "lon": 4.4844398499,
            "tz": "Europe/Brussels",
            "isSchengen": 1,
            "runways": {
                "19": {
                    "true_bearing": 194.43,
                    "coordinates_geojson": [
                        [
                            4.501238888888889,
                            50.91101111111111
                        ],
                        [
                            4.491577777777778,
                            50.88733055555556
                        ]
                    ]
                }
            }
        },
        Airport(
            icao="EBBR",
            iata="BRU",
            name="Brussels Airport",
            city="Brussels",
            state="Flanders",
            country="BE",
            elevation=184,
            lat=50.9014015198,
            lon=4.4844398499,
            tz="Europe/Brussels",
            runways=[
                Runway(
                    name='19',
                    true_bearing=194.43,
                    coordinates_geojson=[
                        [
                            4.501238888888889,
                            50.91101111111111
                        ],
                        [
                            4.491577777777778,
                            50.88733055555556
                        ]
                    ]
                )
            ]
        )
    )
])
def test_airport_factory(data, expected_airport):
    assert AirportFactory.create_from_data(data) == expected_airport
