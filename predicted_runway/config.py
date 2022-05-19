import os
from pathlib import Path


DESTINATION_ICAOS = [
    'EHAM',
    'LEMD',
    'LFPO',
    'LOWW'
]

BASE_DIR = Path(__file__).parent

METEO_DIR = Path(os.getenv("MET_UPDATE_DIR", "/data/met"))
METAR_DIR = METEO_DIR.joinpath('metar')
TAF_DIR = METEO_DIR.joinpath('taf')

RUNWAY_MODELS_DIR = Path("/data/models/runway")
RUNWAY_CONFIG_MODELS_DIR = Path("/data/models/runway_config")

RUNWAY_MODEL_STATS_DIR = Path("/data/stats/runway")
RUNWAY_CONFIG_MODEL_STATS_DIR = Path("/data/stats/runway_config")

ICAO_AIRPORTS_CATALOG_PATH = BASE_DIR.joinpath('static/data').joinpath('icao_airports_catalog.json')

TEMPLATES_DIR = BASE_DIR.joinpath('templates')


def get_taf_dir_for_airport_icao(airport_icao: str) -> Path:
    return TAF_DIR.joinpath(airport_icao)


def get_metar_dir_for_airport_icao(airport_icao: str) -> Path:
    return METAR_DIR.joinpath(airport_icao)


def get_runway_model_path(airport_icao: str) -> Path:
    return RUNWAY_MODELS_DIR.joinpath(f'{airport_icao}.pkl').absolute()


def get_runway_config_model_path(airport_icao: str) -> Path:
    return RUNWAY_CONFIG_MODELS_DIR.joinpath(f'{airport_icao}.pkl').absolute()
