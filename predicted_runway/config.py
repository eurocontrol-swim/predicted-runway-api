import os
from pathlib import Path

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG"
        }
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "class": "logging.Formatter"
        }
    },
    "disable_existing_loggers": False,
    "root": {
        "level": "DEBUG",
        "handlers": [
            "console"
        ]
    },
    "loggers": {
        "met_update_db": {
            "level": "INFO"
        },
    }
}


DESTINATION_ICAOS = os.getenv("DESTINATION_ICAOS", "EHAM,LEMD,LFPO,LOWW").split(',')

MONGO = {
  "db": os.getenv("MET_UPDATE_DB_NAME", "met-update"),
  "host": os.getenv("MET_UPDATE_DB_HOST", "localhost"),
  "port": 27017
}

ARRIVALS_RUNWAY_MODELS_DIR = os.getenv("ARRIVALS_RUNWAY_MODELS_DIR", "/data/models/runway")

ARRIVALS_RUNWAY_CONFIG_MODELS_DIR = os.getenv("ARRIVALS_RUNWAY_CONFIG_MODELS_DIR",
                                              "/data/models/runway_config")

ARRIVALS_RUNWAY_MODEL_STATS_DIR = os.getenv("ARRIVALS_RUNWAY_MODEL_STATS_DIR",
                                            "/data/stats/runway")

ARRIVALS_RUNWAY_CONFIG_MODEL_STATS_DIR = os.getenv("ARRIVALS_RUNWAY_CONFIG_MODEL_STATS_DIR",
                                                   "/data/stats/runway_config")

ICAO_AIRPORTS_CATALOG_PATH = os.getenv("ICAO_AIRPORTS_CATALOG_PATH",
                                       "/data/airports/icao_airports_catalog.json")


def get_runway_model_path(airport_icao: str) -> Path:
    return Path(ARRIVALS_RUNWAY_MODELS_DIR).joinpath(f'{airport_icao}.pkl').absolute()


def get_runway_config_model_path(airport_icao: str) -> Path:
    return Path(ARRIVALS_RUNWAY_CONFIG_MODELS_DIR).joinpath(f'{airport_icao}.pkl').absolute()
