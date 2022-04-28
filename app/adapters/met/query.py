"""
Copyright 2022 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of
conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to
endorse
   or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open
Source Initiative: http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""

__author__ = "EUROCONTROL (SWIM)"

import abc
import json
from pathlib import Path
from typing import Optional
from datetime import timedelta, datetime

import pandas as pd


class AirportFilesQuery(abc.ABC):
    def __init__(self, files_dir: Path) -> None:
        self.files_dir = files_dir

    @staticmethod
    def file_is_before_timestamp(file: Path, timestamp: int) -> bool:
        file_timestamp, _ = file.stem.split('_')

        return int(file_timestamp) <= timestamp

    @staticmethod
    def _read_file(file: Path):
        with file.open('r', encoding="utf-8") as f:
            return json.load(f)

    def get_file(self, before_timestamp: int) -> Optional[Path]:
        reverse_ordered_files = self.list_files(reverse_order=True)

        if not reverse_ordered_files:
            return

        if not before_timestamp:
            last_file, *_ = reverse_ordered_files
            return last_file

        for file in reverse_ordered_files:
            if self.file_has_timestamp(file=file, timestamp=before_timestamp):
                return file

    def list_files(self, reverse_order: bool = False) -> list[Path]:
        result = [f for f in self.files_dir.glob('*.json')]

        if reverse_order:
            result = sorted(result, reverse=True)

        return result

    def file_has_timestamp(self, file: Path, timestamp: int) -> bool:
        return self.file_is_before_timestamp(file, timestamp=timestamp) \
               and self.file_contains_timestamp(file=file, timestamp=timestamp)

    @abc.abstractmethod
    def file_contains_timestamp(self, file: Path, timestamp: int) -> bool:
        ...

    @abc.abstractmethod
    def get_wind_speed(self, before_timestamp: Optional[int] = None) \
            -> Optional[float]:
        ...

    @abc.abstractmethod
    def get_wind_direction(self, before_timestamp: Optional[int] = None) \
            -> Optional[float]:
        ...


class TAFAirportFilesQuery(AirportFilesQuery):

    def file_contains_timestamp(self, file: Path, timestamp: int) -> bool:
        content = self._read_file(file)

        taf_start_time_timestamp = pd.Timestamp(content['start_time']['dt']).timestamp()
        taf_end_time_timestamp = pd.Timestamp(content['end_time']['dt']).timestamp()

        return taf_start_time_timestamp <= timestamp <= taf_end_time_timestamp

    @staticmethod
    def _get_forecast_value(forecast: dict, value_key: str) -> Optional[float]:
        try:
            result = float(forecast[value_key]['value'])
        except (KeyError, TypeError, ValueError):
            result = None

        return result

    def _get_wind_value_from_file(self, file: Path, before_timestamp: int, value_key: str) \
            -> Optional[float]:

        content = self._read_file(file=file)

        backup_value = None
        for forecast in content['forecast']:
            start_time_timestamp = pd.Timestamp(forecast['start_time']['dt']).timestamp()
            end_time_timestamp = pd.Timestamp(forecast['end_time']['dt']).timestamp()

            if start_time_timestamp <= before_timestamp:
                temp = self._get_forecast_value(forecast=forecast, value_key=value_key)

                if temp is not None:
                    backup_value = temp
                    if before_timestamp <= end_time_timestamp:
                        return backup_value

        return backup_value

    def get_wind_speed(self, before_timestamp: Optional[int] = None) -> Optional[int]:
        file = self.get_file(before_timestamp=before_timestamp)

        if file:
            return self._get_wind_value_from_file(file=file,
                                                  before_timestamp=before_timestamp,
                                                  value_key='wind_speed')

    def get_wind_direction(self, before_timestamp: Optional[int] = None) -> Optional[int]:
        file = self.get_file(before_timestamp=before_timestamp)

        if file:
            return self._get_wind_value_from_file(file=file,
                                                  before_timestamp=before_timestamp,
                                                  value_key='wind_direction')

    def get_datetime_range(self) -> Optional[tuple[datetime, datetime]]:
        files = sorted(self.list_files())

        if not files:
            return

        if len(files) == 1:
            first_file, last_file = files[0], files[0]
        else:
            first_file, *_, last_file = sorted(self.list_files())

        first_file_content = self._read_file(first_file)
        last_file_content = self._read_file(last_file)

        start_time, end_time = first_file_content['start_time']['dt'], \
            last_file_content['end_time']['dt']

        return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z"), \
            datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")


class METARAirportFilesQuery(AirportFilesQuery):

    def file_contains_timestamp(self, file: Path, timestamp: int) -> bool:
        content = self._read_file(file)

        content_timestamp = pd.Timestamp(content['time']['dt']).timestamp()
        timestamp_two_hours_ago = timestamp - timedelta(hours=2).total_seconds()

        return timestamp_two_hours_ago <= content_timestamp <= timestamp

    def _get_wind_value_from_file(self, file: Path, wind_value: str) -> Optional[float]:
        content = self._read_file(file)
        try:
            result = float(content[wind_value]['value'])
        except (KeyError, TypeError, ValueError):
            result = None

        return result

    def get_wind_speed(self, before_timestamp: Optional[int] = None) -> Optional[float]:
        file = self.get_file(before_timestamp=before_timestamp)

        if file:
            return self._get_wind_value_from_file(file, wind_value='wind_speed')

    def get_wind_direction(self, before_timestamp: Optional[int] = None) -> Optional[float]:
        file = self.get_file(before_timestamp=before_timestamp)

        if file:
            return self._get_wind_value_from_file(file, wind_value='wind_direction')
