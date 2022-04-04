from datetime import datetime
import pandas as pd

from app.models.runway.data_pipeline.input_processing import (process_datetime,
                                                              get_angle_icao_airports,
                                                              get_wind)


def _input_pipeline(dt: datetime, origin: str, destination: str,
                    wind_direction: float = None, wind_speed: float = None) -> pd.DataFrame:
    datetime_inputs = process_datetime(dt)
    if wind_direction is not None and wind_speed is not None:
        wind_direction = wind_direction % 360
        wind_speed = abs(wind_speed)
        wind_inputs = [wind_speed, wind_direction]
    else:
        wind_inputs = get_wind(destination.upper(), dt=dt)

    origin_inputs = get_angle_icao_airports(origin_icao_code=origin.upper(), destination_icao_code=destination.upper())
    _inputs = [datetime_inputs + wind_inputs + [origin_inputs]]
    inputs = pd.DataFrame(_inputs,
                          columns=["hour", "wind_speed", "wind_dir", "origin_angle"])
    return inputs


def eham_input_pipeline(dt: datetime, origin: str,
                        wind_direction: float = None, wind_speed: float = None) -> pd.DataFrame:
    return _input_pipeline(dt=dt, origin=origin, destination="EHAM",
                           wind_direction=wind_direction, wind_speed=wind_speed)


def lfbo_input_pipeline(dt: datetime, origin: str,
                        wind_direction: float = None, wind_speed: float = None) -> pd.DataFrame:
    return _input_pipeline(dt=dt, origin=origin, destination="LFBO",
                           wind_direction=wind_direction, wind_speed=wind_speed)


def lfpo_input_pipeline(dt: datetime, origin: str,
                        wind_direction: float = None, wind_speed: float = None) -> pd.DataFrame:
    return _input_pipeline(dt=dt, origin=origin, destination="LFPO",
                           wind_direction=wind_direction, wind_speed=wind_speed)
