def valid_icao_code(icao_code: str) -> bool:
    return isinstance(icao_code, str) \
           and len(icao_code) == 4


def valid_wind_speed(wind_speed: float) -> bool:
    return isinstance(wind_speed, float) \
           and wind_speed >= 0


def valid_wind_direction(wind_direction: float) -> bool:
    return isinstance(wind_direction, float) \
           and 0 <= wind_direction <= 360
