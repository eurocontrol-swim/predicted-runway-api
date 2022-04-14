import os
from pathlib import Path


current_path = Path(__file__)
current_dir = current_path.parent
base_dir = current_dir.parent

meteo_dir = Path(os.getenv("MET_UPDATE_DIR", "/data/met"))
metar_dir = meteo_dir.joinpath('metar')
taf_dir = meteo_dir.joinpath('taf')

runway_models_path = Path("/data/models")
runway_models_dir = Path(runway_models_path)

runway_model_metrics_path = Path("/data/metrics")
runway_model_metrics_dir = Path(runway_model_metrics_path)

icao_airports_catalog_path = base_dir.joinpath('static').joinpath('icao_airports_catalog.json')

templates_dir = base_dir.joinpath('templates')
