"""Unit tests for tilt.py mock hydrometer logic."""

import sys
from unittest.mock import MagicMock

# Mock bluetooth and blescan before importing tilt.py
sys.modules["bluetooth"] = MagicMock()
sys.modules["bluetooth._bluetooth"] = MagicMock()
sys.modules["blescan"] = MagicMock()
# Mock sensors since we don't have target hardware board module
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
from unittest.mock import patch

import tilt


class TestTilt(unittest.TestCase):
  """Tests Tilt hydrometer class logic."""

  @patch("tilt.get_tilt")
  def test_get_reading_fahrenheit(self, mock_get_tilt):
    """Verifies Fahrenheit mode returns temperature directly."""
    # Mock return value of get_tilt
    mock_tilt_obj = MagicMock()
    mock_tilt_obj.get_temp_f.return_value = 68.0
    mock_tilt_obj.get_gravity.return_value = 1.045
    mock_get_tilt.return_value = mock_tilt_obj

    sensor = tilt.TiltHydrometerSensor(color="black", use_celcius=False)
    reading = sensor.get_reading()

    self.assertIn("temperature_F", reading)
    self.assertEqual(reading["temperature_F"], 68.0)
    self.assertEqual(reading["gravity"], 1.045)

  @patch("tilt.get_tilt")
  def test_get_reading_celcius(self, mock_get_tilt):
    """Verifies Celsius mode performs Fahrenheit to Celcius conversion."""
    # Mock return value of get_tilt
    mock_tilt_obj = MagicMock()
    mock_tilt_obj.get_temp_f.return_value = 32.0  # 32 F is 0 C
    mock_tilt_obj.get_gravity.return_value = 1.000
    mock_get_tilt.return_value = mock_tilt_obj

    sensor = tilt.TiltHydrometerSensor(color="black", use_celcius=True)
    reading = sensor.get_reading()

    self.assertIn("temperature_C", reading)
    self.assertAlmostEqual(reading["temperature_C"], 0.0)
    self.assertEqual(reading["gravity"], 1.0)


if __name__ == "__main__":
  unittest.main()
