import unittest

from unikube.context.helper import is_valid_uuid4


class IsValidUuid4Test(unittest.TestCase):
    def test_is_valid_uuid4_valid(self):
        result = is_valid_uuid4("51b1d6b3-8375-4859-94f6-73afc05d7275")
        self.assertTrue(result)

    def test_is_valid_uuid4_invalid(self):
        result = is_valid_uuid4("invalid")
        self.assertFalse(result)
