"""Unit tests for loggers.py TsvLogger class."""

import sys
from unittest.mock import MagicMock

# Mock heavy external modules before importing loggers.py
sys.modules["gspread"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["oauth2client"] = MagicMock()
sys.modules["oauth2client.service_account"] = MagicMock()

import os
import tempfile
import unittest

from loggers import TsvLogger


class TestTsvLogger(unittest.TestCase):
  """Tests the TsvLogger implementation."""

  def setUp(self):
    """Sets up a temporary file path for the logger."""
    self.test_dir = tempfile.TemporaryDirectory()
    self.log_file = os.path.join(self.test_dir.name, "test_log.tsv")
    self.header = ["timestamp", "temp", "gravity"]

  def tearDown(self):
    """Cleans up the temporary directory."""
    self.test_dir.cleanup()

  def test_initialization_creates_file_with_header(self):
    """Verifies that initialization writes the header row."""
    logger = TsvLogger(self.log_file, self.header)
    self.assertTrue(os.path.exists(self.log_file))

    with open(self.log_file, "r") as f:
      lines = f.readlines()
    self.assertEqual(len(lines), 1)
    self.assertEqual(lines[0].strip(), "timestamp\ttemp\tgravity")

  def test_append_row_correct_length(self):
    """Verifies that appending a row writes it correctly."""
    logger = TsvLogger(self.log_file, self.header)
    logger.append_row(["10:00", 68.5, 1.055])

    with open(self.log_file, "r") as f:
      lines = f.readlines()
    self.assertEqual(len(lines), 2)
    self.assertEqual(lines[1].strip(), "10:00\t68.5\t1.055")

  def test_append_row_incorrect_length_raises_error(self):
    """Verifies that mismatching columns raise a ValueError."""
    logger = TsvLogger(self.log_file, self.header)
    with self.assertRaises(ValueError):
      logger.append_row(["10:00", 68.5])  # Missing gravity column


if __name__ == "__main__":
  unittest.main()
