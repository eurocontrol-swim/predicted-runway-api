import os
from pathlib import Path


CURRENT_PATH = Path(__file__)
CURRENT_DIR = CURRENT_PATH.parent
BASE_DIR = CURRENT_DIR.parent

METEO_DIR = Path(os.getenv("MET_UPDATE_DIR", "/data/met"))
METAR_DIR = METEO_DIR.joinpath('metar')
TAF_DIR = METEO_DIR.joinpath('taf')

RUNWAY_MODELS_DIR = Path("/data/models")

RUNWAY_MODEL_METRICS_DIR = Path("/data/metrics")

ICAO_AIRPORTS_CATALOG_PATH = BASE_DIR.joinpath('static').joinpath('icao_airports_catalog.json')

TEMPLATES_DIR = BASE_DIR.joinpath('templates')


def get_taf_dir_for_airport_icao(airport_icao: str) -> Path:
    return TAF_DIR.joinpath(airport_icao)


def get_metar_dir_for_airport_icao(airport_icao: str) -> Path:
    return METAR_DIR.joinpath(airport_icao)
