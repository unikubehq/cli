import subprocess
import sys
import unittest

from src.authentication.web import get_callback_port, is_port_available


class WebTest(unittest.TestCase):
    def test_is_port_available_true(self):
        result = is_port_available(host="localhost", port=44444)
        self.assertTrue(result)

    def test_is_port_available_false(self):
        webserver = subprocess.Popen([sys.executable, "webserver.py"])

        result = is_port_available(host="localhost", port=8000)
        self.assertFalse(result)

        webserver.kill()

    def test_get_callback_port(self):
        port = get_callback_port(44444, 44445)
        self.assertEqual(port, 44444)

    def test_get_callback_port_blocked(self):
        webserver = subprocess.Popen([sys.executable, "webserver.py"])

        port = get_callback_port(range_start=8000, range_end=8002)
        self.assertEqual(port, 8001)

        webserver.kill()

    def test_get_callback_port_range_none(self):
        with self.assertRaises(Exception):
            _ = get_callback_port(range_start=8000, range_end=8000)

    def test_get_callback_port_range_blocked(self):
        webserver = subprocess.Popen([sys.executable, "webserver.py"])

        with self.assertRaises(Exception):
            _ = get_callback_port(range_start=8000, range_end=8001)

        webserver.kill()
