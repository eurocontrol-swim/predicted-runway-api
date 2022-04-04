from pathlib import Path
from os import getenv

current_path = Path(__file__)
current_dir = current_path.parent
base_dir = current_dir.parent

meteo_path = getenv('METEO_PATH')
meteo_dir = Path(meteo_path)
metar_dir = meteo_dir.joinpath('metar')
taf_dir = meteo_dir.joinpath('taf')

runway_models_path = getenv('RUNWAY_MODELS_PATH')
runway_models_dir = Path(runway_models_path)

icao_airports_catalog_path = base_dir.joinpath('models').joinpath('static').joinpath('icao_airports_catalog.json')

templates_dir = base_dir.joinpath('templates')
