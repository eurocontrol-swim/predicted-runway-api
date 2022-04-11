from random import uniform
import unittest
from app.routes.input_validation import (valid_icao_code,
                                         valid_wind_speed,
                                         valid_wind_direction)


class TestICAOCode(unittest.TestCase):
    def test_valid_icao_code(self):
        with self.subTest():
            valid = 'LEMD'
            self.assertTrue(valid_icao_code(valid))

        with self.subTest():
            valid = 'LOWW'
            self.assertTrue(valid_icao_code(valid))

        with self.subTest():
            valid = 'KJFK'
            self.assertTrue(valid_icao_code(valid))

        with self.subTest():
            valid = 'L0WW'
            self.assertTrue(valid_icao_code(valid))

    def test_invalid_icao_code(self):
        with self.subTest():
            invalid = 'ILEMD'
            self.assertFalse(valid_icao_code(invalid))

        with self.subTest():
            invalid = 1234
            self.assertFalse(valid_icao_code(invalid))


class TestWindSpeed(unittest.TestCase):

    def test_valid_wind_speed(self):
        for _ in range(10):
            with self.subTest():
                valid = uniform(0, 1000)
                self.assertTrue(valid_wind_speed(valid))

    def test_invalid_negative_wind_speed(self):
        for _ in range(10):
            with self.subTest():
                invalid = uniform(-0.01, -1000)
                self.assertFalse(valid_wind_speed(invalid))

    def test_invalid_NaN(self):
        invalid = '3.14'
        self.assertFalse(valid_wind_speed(invalid))


class TestWindDirection(unittest.TestCase):

    def test_valid_wind_dir(self):
        for _ in range(10):
            with self.subTest():
                valid = uniform(0, 360)
                self.assertTrue(valid_wind_direction(valid))

    def test_invalid_negative_wind_dir(self):
        for _ in range(10):
            with self.subTest():
                invalid = uniform(-0.01, -1000)
                self.assertFalse(valid_wind_direction(invalid))

    def test_invalid_NaN(self):
        invalid = '3.14'
        self.assertFalse(valid_wind_direction(invalid))

if __name__ == '__main__':
    unittest.main()
