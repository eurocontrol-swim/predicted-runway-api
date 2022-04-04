def valid_icao_code(icao_code: str) -> bool:
    if not isinstance(icao_code, str):
        return False
    else:
        return icao_code.isalpha() and len(icao_code) == 4


def valid_wind_speed(wind_speed: float) -> bool:
    if not isinstance(wind_speed, float):
        return False
    else:
        if wind_speed < 0:
            return False
        else:
            return True


def valid_wind_direction(wind_direction: float) -> bool:
    if not isinstance(wind_direction, float):
        return False
    else:
        if wind_direction < 0 or wind_direction > 360:
            return False
        else:
            return True
