import pandas as pd
from pathlib import Path
from datetime import timedelta
from pandas import Timestamp
from json import load
from typing import Dict

from app.met_api import ExpiredMETAR, METARNotAvailable, TAFNotAvailable


def _query_last_taf(taf_path: Path, before: int = None) -> Dict:
    files = taf_path.glob('*.json')
    ordered_files = sorted(files, reverse=True)

    if not before:
        try:
            last = ordered_files[0]
            with last.open('r', encoding="utf-8") as file:
                output = load(file)
            return output
        except IndexError as e:
            raise TAFNotAvailable()
    else:
        for file in ordered_files:
            retrieval_timestamp = int(file.stem.split('_')[0])
            if retrieval_timestamp <= before:
                with file.open('r', encoding="utf-8") as f:
                    file_content = load(f)
                end_time = Timestamp(file_content['end_time']['dt'])
                start_time = Timestamp(file_content['start_time']['dt'])
                print()
                if start_time.timestamp() <= before <= end_time.timestamp():
                    return file_content
            else:
                # If retrieval timestamp is greater than before we pass to the next one
                pass
        raise TAFNotAvailable()


def _query_last_metar(metar_path: Path, before: int=None) -> Dict:
    files = metar_path.glob('*.json')
    ordered_files = sorted(files, reverse=True)

    if not before:
        try:
            last = ordered_files[0]
            with last.open('r', encoding="utf-8") as file:
                output = load(file)
            return output
        except IndexError as e:
            raise METARNotAvailable()
    else:
        for file in ordered_files:
            retrieval_timestamp = int(file.stem.split('_')[0])
            if retrieval_timestamp <= before:
                with file.open('r', encoding="utf-8") as f:
                    file_content = load(f)

                content_timestamp = pd.Timestamp(file_content['time']['dt'])
                # If the timestamp of the report is not older than 2 hours we use it
                if before - timedelta(hours=2).total_seconds() <= content_timestamp.timestamp() <= before:
                    return file_content
                # Otherwise we raise an ExpiredMETAR
                else:
                    raise ExpiredMETAR()
            else:
                # If retrieval time is greater than before we go to the next file
                pass
        # If we exhaust the list of files we raise a METARNotAvailable
        raise METARNotAvailable()


def get_last_wind_speed(met_path: Path, airport: str, before: int) -> float:
    metar_path = met_path.joinpath('metar').joinpath(airport)
    taf_path = met_path.joinpath('taf').joinpath(airport)
    try:
        last_report = _query_last_metar(metar_path=metar_path, before=before)
        return float(last_report['wind_speed']['value'])
    except (METARNotAvailable, ExpiredMETAR):
        last_report = _query_last_taf(taf_path=taf_path, before=before)
        forecasts = last_report['forecast']
        for forecast in forecasts:
            start_time = pd.Timestamp(forecast['start_time']['dt'])
            end_time = pd.Timestamp(forecast['end_time']['dt'])
            if start_time.timestamp() <= before <= end_time.timestamp():
                try:
                    wind_speed = int(forecast['wind_speed']['value'])
                    return wind_speed
                except:
                    pass
        raise TAFNotAvailable()


def get_last_wind_dir(met_path: Path, airport: str, before: int) -> float:
    metar_path = met_path.joinpath('metar').joinpath(airport)
    taf_path = met_path.joinpath('taf').joinpath(airport)
    try:
        last_report = _query_last_metar(metar_path=metar_path, before=before)
        return float(last_report['wind_direction']['value'])
    except (METARNotAvailable, ExpiredMETAR):
        last_report = _query_last_taf(taf_path=taf_path, before=before)
        forecasts = last_report['forecast']
        for forecast in forecasts:
            start_time = pd.Timestamp(forecast['start_time']['dt'])
            end_time = pd.Timestamp(forecast['end_time']['dt'])
            if start_time.timestamp() <= before <= end_time.timestamp():
                try:
                    wind_dir = float(forecast['wind_direction']['value'])
                    return wind_dir
                except:
                    pass
        raise TAFNotAvailable()



