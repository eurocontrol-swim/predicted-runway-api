import json
import math
from datetime import datetime
from typing import List
from app.config.file_dir import icao_airports_catalog_path
from app.config.file_dir import meteo_dir
from app.met_api.query import (get_last_wind_dir,
                               get_last_wind_speed)


with icao_airports_catalog_path.open('r', encoding="utf-8") as f:
    icao_airports_dict = json.load(f)


def process_datetime(dt: datetime) -> List:
    # month = dt.month
    # day_week = dt.weekday()
    hour = dt.hour
    return [hour]


class AirportNotFound(Exception):
    def __init__(self, message="Airport not found"):
        self.message = message
        super().__init__(self.message)


def get_angle_icao_airports(origin_icao_code: str, destination_icao_code: str):
    if origin_icao_code not in icao_airports_dict.keys():
        raise AirportNotFound("origin_icao_code = {} not found in the Airport DB".format(origin_icao_code))
    if destination_icao_code not in icao_airports_dict.keys():
        raise AirportNotFound("destination_icao_code = {} not found in the Airport DB".format(destination_icao_code))


    origin_lat = icao_airports_dict[origin_icao_code]['lat']
    origin_lon = icao_airports_dict[origin_icao_code]['lon']
    destination_lat = icao_airports_dict[destination_icao_code]['lat']
    destination_lon = icao_airports_dict[destination_icao_code]['lon']

    origin_lat = math.radians(origin_lat)
    origin_lon = math.radians(origin_lon)
    destination_lat = math.radians(destination_lat)
    destination_lon = math.radians(destination_lon)

    d_lon = destination_lon - origin_lon

    y = math.sin(d_lon) * math.cos(destination_lat)
    x = math.cos(origin_lat) * math.sin(destination_lat) - math.sin(origin_lat) * math.cos(
        destination_lat) * math.cos(d_lon)

    bearing = math.atan2(y, x)

    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    # bearing = 360 - bearing (uncomment to count degrees counterclockwise)

    return bearing


def get_wind(airport: str, dt: datetime) -> List:
    wind_speed = get_last_wind_speed(met_path=meteo_dir, airport=airport, before=int(dt.timestamp()))
    wind_dir = get_last_wind_dir(met_path=meteo_dir, airport=airport, before=int(dt.timestamp()))
    return [wind_speed, wind_dir]
