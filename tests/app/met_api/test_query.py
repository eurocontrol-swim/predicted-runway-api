import unittest
from pathlib import Path
from pandas import Timestamp
from app.met_api.query import (_query_last_taf,
                               _query_last_metar,
                               get_last_wind_speed,
                               get_last_wind_dir)
from app.met_api import METARNotAvailable, ExpiredMETAR, ExpiredTAF, TAFNotAvailable

static_test_dir = Path(__file__).parent.parent.parent.resolve().joinpath('static')


class TestQueryLastTAF(unittest.TestCase):
    taf_dir = static_test_dir.joinpath('taf').joinpath('EHAM')

    def test_query_last(self):
        with self.subTest():
            actual_taf_timestamp = '2022-03-21T09:03:14.401472Z'
            before = int(Timestamp("2022-03-22T09:00:00Z").timestamp())
            taf = _query_last_taf(taf_path=self.taf_dir, before=before)
            tested_taf_timestamp = taf['meta']['timestamp']
            self.assertEqual(actual_taf_timestamp, tested_taf_timestamp)

        with self.subTest():
            actual_taf_timestamp = "2022-03-18T13:00:07.883260Z"
            before = 1647608406 + 500
            taf = _query_last_taf(taf_path=self.taf_dir, before=before)
            tested_taf_timestamp = taf['meta']['timestamp']
            self.assertEqual(actual_taf_timestamp, tested_taf_timestamp)

    def test_no_taf_available(self):
        with self.assertRaises(TAFNotAvailable):
            before = int(Timestamp('2022-03-22T12:00:00Z').timestamp() + 3600)
            _query_last_taf(taf_path=self.taf_dir, before=before)


class TestQueryLastMETAR(unittest.TestCase):
    metar_dir = static_test_dir.joinpath('metar').joinpath('EHAM')

    def test_no_metar_available(self):
        with self.assertRaises(METARNotAvailable):
            before = int(Timestamp("2022-03-18T13:00:04.522430Z").timestamp() - 50)
            _query_last_metar(metar_path=self.metar_dir, before=before)

    def test_expired_metar(self):
        with self.assertRaises(ExpiredMETAR):
            before = int(Timestamp("2022-03-18T17:16:08.291369Z").timestamp() + 3600 * 2.5)
            _query_last_metar(metar_path=self.metar_dir, before=before)

    def test_get_last(self):
        before = int(Timestamp('2022-03-18T14:25:00Z').timestamp() + 25 * 60)
        actual_metar_timestamp = '2022-03-18T14:30:06.009450Z'
        metar = _query_last_metar(metar_path=self.metar_dir, before=before)
        test_metar_timestamp = metar['meta']['timestamp']
        self.assertEqual(actual_metar_timestamp, test_metar_timestamp)


class TestGetLastWindSpeed(unittest.TestCase):

    def test_get_from_taf(self):
        before = int(Timestamp('2022-03-19T01:00:00Z').timestamp())
        expected_wind_speed = 10
        test_wind_speed = get_last_wind_speed(met_path=static_test_dir,
                                              airport='EHAM',
                                              before=before)
        self.assertEqual(expected_wind_speed, test_wind_speed)

    def test_get_from_metar(self):
        before = int(Timestamp('2022-03-18T16:30:05.481364Z').timestamp() + 1)
        expected_wind_speed = 13
        test_wind_speed = get_last_wind_speed(met_path=static_test_dir,
                                              airport='EHAM',
                                              before=before)
        self.assertEqual(expected_wind_speed, test_wind_speed)


class TestGetLastWindDirection(unittest.TestCase):

    def test_get_from_taf(self):
        before = int(Timestamp('2022-03-19T12:00:00Z').timestamp())
        expected_wind_direction = 80
        test_wind_direction = get_last_wind_dir(met_path=static_test_dir,
                                                airport='EHAM',
                                                before=before)
        self.assertEqual(expected_wind_direction, test_wind_direction)

    def test_get_from_metar(self):
        before = int(Timestamp('2022-03-18T16:30:05.481364Z').timestamp() + 1)
        expected_wind_direction = 359
        test_wind_direction = get_last_wind_dir(met_path=static_test_dir,
                                                airport='EHAM',
                                                before=before)
        self.assertEqual(expected_wind_direction, test_wind_direction)


if __name__ == '__main__':
    unittest.main()
