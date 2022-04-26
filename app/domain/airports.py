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

import json
from functools import lru_cache

from app.config.file_dir import ICAO_AIRPORTS_CATALOG_PATH, RUNWAY_MODEL_METRICS_DIR
from app.config import DESTINATION_ICAOS


@lru_cache
def get_airport_data():
    with open(ICAO_AIRPORTS_CATALOG_PATH, 'r') as f:
        return json.load(f)


def _reverse_coordinates_geojson(coordinates_geojson: list[list]) -> list[list]:
    return [[coord[1], coord[0]] for coord in coordinates_geojson]


def extract_airport_data(data: dict, with_geodata: bool = False) -> dict:
    extracted = {
        "icao": data['icao'],
        "label": f"{data['icao']}: {data['name']}, {data['city']}, {data['state']}, {data['country']}"
    }

    if with_geodata:
        extracted["lat"] = data["lat"]
        extracted["lon"] = data["lon"]
        extracted["runways_geodata"] = {
            runway: {
                'geojson': _reverse_coordinates_geojson(data["coordinates_geojson"]),
                'true_bearing': data['true_bearing']
            }
            for runway, data in data.get("runways", {}).items()
        }

    return extracted


def get_destination_airports_data():
    return {
        icao: extract_airport_data(data, with_geodata=True)
        for icao, data in get_airport_data().items()
        if icao in DESTINATION_ICAOS
    }


def get_destination_airport_metrics(airport: str):
    path = RUNWAY_MODEL_METRICS_DIR.joinpath(f"CV-Test_results_{airport}_100.json")

    with open(path, 'r') as f:
        return json.load(f)


def airport_data_matches(data: dict, search_value: str) -> bool:
    search_value = search_value.lower()
    searchable_keys = ['icao', 'name', 'city', 'state', 'country']

    return any(
        [search_value in data[key].lower() for key in searchable_keys]
    )


def search_airport_data(search_value: str) -> list:
    return [
        extract_airport_data(data)
        for _, data in get_airport_data().items()
        if airport_data_matches(data, search_value)
    ]
