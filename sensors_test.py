"""Unit tests for sensors.py conversion utilities and Timestamp class."""

import sys
from unittest.mock import MagicMock

# Mock hardware and board modules before importing sensors.py
sys.modules["board"] = MagicMock()
sys.modules["adafruit_ina219"] = MagicMock()
sys.modules["adafruit_ina260"] = MagicMock()
sys.modules["adafruit_bh1750"] = MagicMock()
sys.modules["adafruit_veml6070"] = MagicMock()
sys.modules["adafruit_veml7700"] = MagicMock()
sys.modules["adafruit_tsl2591"] = MagicMock()
sys.modules["adafruit_mcp9808"] = MagicMock()
sys.modules["adafruit_bme280"] = MagicMock()
sys.modules["adafruit_bme280.basic"] = MagicMock()
sys.modules["adafruit_sgp30"] = MagicMock()

import unittest

from sensors import celcius_to_fahrenheit
from sensors import fahrenheit_to_celcius
from sensors import Timestamp


class TestSensors(unittest.TestCase):
  """Tests sensor utility functions."""

  def test_celcius_to_fahrenheit(self):
    """Verifies Celcius to Fahrenheit conversion values."""
    self.assertAlmostEqual(celcius_to_fahrenheit(0), 32.0)
    self.assertAlmostEqual(celcius_to_fahrenheit(100), 212.0)
    self.assertAlmostEqual(celcius_to_fahrenheit(-40), -40.0)

  def test_fahrenheit_to_celcius(self):
    """Verifies Fahrenheit to Celcius conversion values."""
    self.assertAlmostEqual(fahrenheit_to_celcius(32), 0.0)
    self.assertAlmostEqual(fahrenheit_to_celcius(212), 100.0)
    self.assertAlmostEqual(fahrenheit_to_celcius(-40), -40.0)

  def test_timestamp_reading(self):
    """Verifies Timestamp class returns expected keys and timezone format."""
    ts = Timestamp(timezone="UTC", format="%Y-%m-%d")
    reading = ts.get_reading()
    self.assertIn("time", reading)
    self.assertEqual(len(reading["time"].split("-")), 3)


if __name__ == "__main__":
  unittest.main()
