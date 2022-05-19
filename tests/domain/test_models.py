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

import datetime

import pytest

from predicted_runway.adapters.airports import get_airport_by_icao
from predicted_runway.domain.models import Timestamp, Airport, Runway, RunwayPredictionInput, \
    WindInputSource, RunwayConfigPredictionInput, RunwayConfigProbability, RunwayPredictionOutput, \
    RunwayProbability, RunwayConfigPredictionOutput


@pytest.mark.parametrize('value, expected_datetime', [
    (int(datetime.datetime(2022, 5, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp()),
     datetime.datetime(2022, 5, 12, 14, 0, tzinfo=datetime.timezone.utc))
])
def test_timestamp__datetime(value, expected_datetime):
    assert Timestamp(value)._datetime == expected_datetime


@pytest.mark.parametrize('value, expected_str', [
    (int(datetime.datetime(2022, 5, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp()), 'Thu, 12 May 2022 14:00:00 UTC')
])
def test_timestamp__str(value, expected_str):
    assert str(Timestamp(value)) == expected_str


@pytest.mark.parametrize('value, expected_hour_of_day', [
    (int(datetime.datetime(2022, 5, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp()), 14),
    (int(datetime.datetime(2022, 5, 12, 2, 0, tzinfo=datetime.timezone.utc).timestamp()), 2)
])
def test_timestamp__hour_of_day(value, expected_hour_of_day):
    assert Timestamp(value).hour_of_day == expected_hour_of_day


@pytest.mark.parametrize('value, expected_is_summer_season', [
    (int(datetime.datetime(2022, 5, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp()), True),
    (int(datetime.datetime(2022, 7, 12, 14, 0, tzinfo=datetime.timezone.utc).timestamp()), True),
    (int(datetime.datetime(2022, 4, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp()), False),
    (int(datetime.datetime(2022, 11, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp()), False)
])
def test_timestamp__is_summer_season(value, expected_is_summer_season):
    assert Timestamp(value).is_summer_season() == expected_is_summer_season


@pytest.mark.parametrize('value, expected_is_workday', [
    (int(datetime.datetime
         .strptime("Sat, 23/04/2022 14:00", "%a, %d/%m/%Y %H:%M")
         .astimezone(datetime.timezone.utc).timestamp()), True),
    (int(datetime.datetime
         .strptime("Sun, 24/04/2022 14:00", "%a, %d/%m/%Y %H:%M")
         .astimezone(datetime.timezone.utc).timestamp()), False),
    (int(datetime.datetime
         .strptime("Thu, 26/05/2022 14:00", "%a, %d/%m/%Y %H:%M")
         .astimezone(datetime.timezone.utc).timestamp()), False),
])
def test_timestamp__is_workday(value, expected_is_workday):
    assert Timestamp(value).is_workday('BE') == expected_is_workday


@pytest.mark.parametrize('datetime, expected_quarter_of_day', [
    (datetime.datetime.strptime("23/04/2022 14:00", "%d/%m/%Y %H:%M"), 56),
    (datetime.datetime.strptime("23/04/2022 14:01", "%d/%m/%Y %H:%M"), 56),
    (datetime.datetime.strptime("23/04/2022 14:10", "%d/%m/%Y %H:%M"), 56),
    (datetime.datetime.strptime("23/04/2022 14:16", "%d/%m/%Y %H:%M"), 57),
])
def test_timestamp__quarter_of_day(datetime, expected_quarter_of_day):
    timestamp = Timestamp(value=1650751200)
    timestamp._datetime = datetime
    assert timestamp.quarter_of_day == expected_quarter_of_day


@pytest.mark.parametrize('airport, expected_searchable', [
    (
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
        ),
        'EBBR Brussels Airport Brussels Flanders BE'
    )
])
def test_airport__searchable(airport, expected_searchable):
    assert airport.searchable == expected_searchable


@pytest.mark.parametrize('airport, expected_title', [
    (
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
        ),
        'EBBR: Brussels Airport, Brussels, Flanders, BE'
    )
])
def test_airport__title(airport, expected_title):
    assert airport.title == expected_title


@pytest.mark.parametrize('airport, runway_name, expected_runway', [
    (
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
        ),
        '19',
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
    ),
    (
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
        ),
        '18',
        None
    )
])
def test_airport__get_runway(airport, runway_name, expected_runway):
    assert airport.get_runway(runway_name) == expected_runway


@pytest.mark.parametrize('runway_prediction_input, expected_dict', [
    (
        RunwayPredictionInput(
            origin=get_airport_by_icao('EBBR'),
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": 1650751200,
            "wind_input_source": "TAF",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    ),
    (
        RunwayPredictionInput(
            origin=get_airport_by_icao('EBBR'),
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=None,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "timestamp": 1650751200,
            "wind_input_source": "",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    )
])
def test_runway_prediction_input__to_dict(runway_prediction_input, expected_dict):
    assert runway_prediction_input.to_dict() == expected_dict


@pytest.mark.parametrize('runway_prediction_input, expected_dict', [
    (
        RunwayPredictionInput(
            origin=get_airport_by_icao('EBBR'),
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "date_time": "Sat, 23 Apr 2022 22:00:00 UTC",
            "wind_input_source": "from TAF",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    ),
    (
        RunwayPredictionInput(
            origin=get_airport_by_icao('EBBR'),
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=None,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "origin_icao": 'EBBR',
            "destination_icao": 'EHAM',
            "date_time": "Sat, 23 Apr 2022 22:00:00 UTC",
            "wind_input_source": "",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    )
])
def test_runway_prediction_input__to_display_dict(runway_prediction_input, expected_dict):
    assert runway_prediction_input.to_display_dict() == expected_dict


@pytest.mark.parametrize('runway_prediction_input', [
    (
        RunwayPredictionInput(
            origin=get_airport_by_icao('EBBR'),
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        )
    )
])
@pytest.mark.parametrize('features, expected_values', [
    (
        ["hour", "is_workday", "is_summer_season", "wind_speed", "wind_dir", "origin_angle"],
        [22, True, False, 15.0, 180.0, 6.921882923696614]
    ),
    (
        ["is_workday", "is_summer_season", "wind_dir", "wind_speed", "origin_angle", "hour"],
        [True, False, 180.0, 15.0, 6.921882923696614, 22]
    )
])
def test_runway_prediction_input__get_model_input_values(
    runway_prediction_input, features, expected_values
):
    assert runway_prediction_input.get_model_input_values(features) == expected_values


@pytest.mark.parametrize('runway_config_prediction_input, expected_dict', [
    (
        RunwayConfigPredictionInput(
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "destination_icao": 'EHAM',
            "timestamp": 1650751200,
            "wind_input_source": "TAF",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    ),
    (
        RunwayConfigPredictionInput(
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=None,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "destination_icao": 'EHAM',
            "timestamp": 1650751200,
            "wind_input_source": "",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    )
])
def test_runway_config_prediction_input__to_dict(runway_config_prediction_input, expected_dict):
    assert runway_config_prediction_input.to_dict() == expected_dict


@pytest.mark.parametrize('runway_config_prediction_input, expected_dict', [
    (
        RunwayConfigPredictionInput(
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "destination_icao": 'EHAM',
            "date_time": "Sat, 23 Apr 2022 22:00:00 UTC",
            "wind_input_source": "from TAF",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    ),
    (
        RunwayConfigPredictionInput(
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=None,
            wind_speed=15.0,
            wind_direction=180.0
        ),
        {
            "destination_icao": 'EHAM',
            "date_time": "Sat, 23 Apr 2022 22:00:00 UTC",
            "wind_input_source": "",
            "wind_speed": 15.0,
            "wind_direction": 180.0
        }
    )
])
def test_runway_config_prediction_input__to_display_dict(runway_config_prediction_input, expected_dict):
    assert runway_config_prediction_input.to_display_dict() == expected_dict


@pytest.mark.parametrize('runway_config_prediction_input', [
    (
        RunwayConfigPredictionInput(
            destination=get_airport_by_icao('EHAM'),
            timestamp=Timestamp(1650751200),
            wind_input_source=WindInputSource.TAF,
            wind_speed=15.0,
            wind_direction=180.0
        )
    )
])
@pytest.mark.parametrize('features, expected_values', [
    (
        ["15min_day_interval", "is_workday", "is_summer_season", "wind_speed", "wind_dir"],
        [88, True, False, 15.0, 180.0]
    ),
    (
        ["is_workday", "is_summer_season", "wind_dir", "wind_speed", "15min_day_interval"],
        [True, False, 180.0, 15.0, 88]
    )
])
def test_runway_config_prediction_input__get_model_input_values(
    runway_config_prediction_input, features, expected_values
):
    assert runway_config_prediction_input.get_model_input_values(features) == expected_values


@pytest.mark.parametrize('runway_config, expected_runway_names', [
    (
        "('18C', '18R')", ["18C", "18R"]
    )
])
def test_runway_config_probability__runway_names(runway_config, expected_runway_names):
    assert RunwayConfigProbability(runway_config=runway_config, value=0.9).runway_names \
           == expected_runway_names


@pytest.mark.parametrize('runway_prediction_output, expected_geojson', [
    (
        RunwayPredictionOutput(
            probas=[
                RunwayProbability(
                    runway_name='19',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='1',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='25L',
                    value=0.4
                ),
                RunwayProbability(
                    runway_name='07R',
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EBBR')
        ),
        {'features': [{'geometry': {'coordinates': [[4.5233, 50.898941666666666],
                                                    [4.482055555555555,
                                                     50.88941388888889]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.4,
                                      'runway_name': '25L',
                                      'true_bearing': 249.89},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[4.501238888888889,
                                                     50.91101111111111],
                                                    [4.491577777777778,
                                                     50.88733055555556]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.3,
                                      'runway_name': '19',
                                      'true_bearing': 194.43},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[4.491577777777778,
                                                     50.88733055555556],
                                                    [4.501238888888889,
                                                     50.91101111111111]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.3,
                                      'runway_name': '1',
                                      'true_bearing': 14.43},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[4.482055555555555,
                                                     50.88941388888889],
                                                    [4.5233, 50.898941666666666]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.001,
                                      'runway_name': '07R',
                                      'true_bearing': 69.89},
                       'type': 'Feature'}],
         'type': 'FeatureCollection'}
    )
])
def test_runway_prediction_output__to_geojson(runway_prediction_output, expected_geojson):
    assert runway_prediction_output.to_geojson() == expected_geojson


@pytest.mark.parametrize('runway_prediction_output, expected_geojson', [
    (
        RunwayPredictionOutput(
            probas=[
                RunwayProbability(
                    runway_name='19',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='1',
                    value=0.3
                ),
                RunwayProbability(
                    runway_name='25L',
                    value=0.4
                ),
                RunwayProbability(
                    runway_name='07R',
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EBBR')
        ),
        {'features': [{'geometry': {'coordinates': [[4.5233, 50.898941666666666],
                                                    [4.482055555555555,
                                                     50.88941388888889]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.4,
                                      'runway_name': '25L',
                                      'true_bearing': 249.89},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[4.501238888888889,
                                                     50.91101111111111],
                                                    [4.491577777777778,
                                                     50.88733055555556]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.3,
                                      'runway_name': '19',
                                      'true_bearing': 194.43},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[4.491577777777778,
                                                     50.88733055555556],
                                                    [4.501238888888889,
                                                     50.91101111111111]],
                                    'type': 'LineString'},
                       'properties': {'probability': 0.3,
                                      'runway_name': '1',
                                      'true_bearing': 14.43},
                       'type': 'Feature'}],
         'type': 'FeatureCollection'}
    )
])
def test_runway_prediction_output__to_geojson__exclude_zero_probas(
    runway_prediction_output, expected_geojson
):
    assert runway_prediction_output.to_geojson(exclude_zero_probas=True) == expected_geojson


@pytest.mark.parametrize('runway_config_prediction_output, expected_geojson', [
    (
        RunwayConfigPredictionOutput(
            probas=[
                RunwayConfigProbability(
                    runway_config="('25L', '1')",
                    value=0.3
                ),
                RunwayConfigProbability(
                    runway_config="('1', '19')",
                    value=0.6
                ),
                RunwayConfigProbability(
                    runway_config="('25L',)",
                    value=0.1
                ),
                RunwayConfigProbability(
                    runway_config="('25L', '07R')",
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EBBR')
        ),
        {'features': [{'geometry': {'coordinates': [[[4.491577777777778,
                                                      50.88733055555556],
                                                     [4.501238888888889,
                                                      50.91101111111111]],
                                                    [[4.501238888888889,
                                                      50.91101111111111],
                                                     [4.491577777777778,
                                                      50.88733055555556]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.6,
                                      'runways': [{'name': '1', 'true_bearing': 14.43},
                                                  {'name': '19',
                                                   'true_bearing': 194.43}]},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[[4.5233, 50.898941666666666],
                                                     [4.482055555555555,
                                                      50.88941388888889]],
                                                    [[4.491577777777778,
                                                      50.88733055555556],
                                                     [4.501238888888889,
                                                      50.91101111111111]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.3,
                                      'runways': [{'name': '25L',
                                                   'true_bearing': 249.89},
                                                  {'name': '1',
                                                   'true_bearing': 14.43}]},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[[4.5233, 50.898941666666666],
                                                     [4.482055555555555,
                                                      50.88941388888889]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.1,
                                      'runways': [{'name': '25L',
                                                   'true_bearing': 249.89}]},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[[4.5233, 50.898941666666666],
                                                     [4.482055555555555,
                                                      50.88941388888889]],
                                                    [[4.482055555555555,
                                                      50.88941388888889],
                                                     [4.5233, 50.898941666666666]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.001,
                                      'runways': [{'name': '25L',
                                                   'true_bearing': 249.89},
                                                  {'name': '07R',
                                                   'true_bearing': 69.89}]},
                       'type': 'Feature'}],
         'type': 'FeatureCollection'}
    )
])
def test_runway_config_prediction_output__to_geojson(
    runway_config_prediction_output, expected_geojson
):
    assert runway_config_prediction_output.to_geojson() == expected_geojson


@pytest.mark.parametrize('runway_config_prediction_output, expected_geojson', [
    (
        RunwayConfigPredictionOutput(
            probas=[
                RunwayConfigProbability(
                    runway_config="('25L', '1')",
                    value=0.3
                ),
                RunwayConfigProbability(
                    runway_config="('1', '19')",
                    value=0.6
                ),
                RunwayConfigProbability(
                    runway_config="('25L',)",
                    value=0.1
                ),
                RunwayConfigProbability(
                    runway_config="('25L', '07R')",
                    value=0.001
                )
            ],
            destination=get_airport_by_icao('EBBR')
        ),
        {'features': [{'geometry': {'coordinates': [[[4.491577777777778,
                                                      50.88733055555556],
                                                     [4.501238888888889,
                                                      50.91101111111111]],
                                                    [[4.501238888888889,
                                                      50.91101111111111],
                                                     [4.491577777777778,
                                                      50.88733055555556]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.6,
                                      'runways': [{'name': '1', 'true_bearing': 14.43},
                                                  {'name': '19',
                                                   'true_bearing': 194.43}]},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[[4.5233, 50.898941666666666],
                                                     [4.482055555555555,
                                                      50.88941388888889]],
                                                    [[4.491577777777778,
                                                      50.88733055555556],
                                                     [4.501238888888889,
                                                      50.91101111111111]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.3,
                                      'runways': [{'name': '25L',
                                                   'true_bearing': 249.89},
                                                  {'name': '1',
                                                   'true_bearing': 14.43}]},
                       'type': 'Feature'},
                      {'geometry': {'coordinates': [[[4.5233, 50.898941666666666],
                                                     [4.482055555555555,
                                                      50.88941388888889]]],
                                    'type': 'MultiLineString'},
                       'properties': {'probability': 0.1,
                                      'runways': [{'name': '25L',
                                                   'true_bearing': 249.89}]},
                       'type': 'Feature'}],
         'type': 'FeatureCollection'}
    )
])
def test_runway_config_prediction_output__to_geojson__exclude_zero_probas(
    runway_config_prediction_output, expected_geojson
):
    assert runway_config_prediction_output.to_geojson(exclude_zero_probas=True) == expected_geojson
