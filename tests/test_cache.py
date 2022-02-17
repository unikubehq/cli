import os
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from src.cache.cache import Cache


class CacheTest(unittest.TestCase):
    def setUp(self):
        self.temporary_path_object = tempfile.TemporaryDirectory()
        self.temporary_path = self.temporary_path_object.name

    def tearDown(self):
        self.temporary_path_object.cleanup()

    def test_cache_empty(self):
        cache = Cache(file_path=self.temporary_path)
        self.assertEqual(UUID("00000000-0000-0000-0000-000000000000"), cache.userId)

    def test_cache_save(self):
        cache = Cache(file_path=self.temporary_path)
        cache.file_path = self.temporary_path
        cache.save()

        file = Path(os.path.join(cache.file_path, cache.file_name))

        self.assertTrue(file.exists())
        self.assertEqual(UUID("00000000-0000-0000-0000-000000000000"), cache.userId)

    def test_cache_load(self):
        cache_01 = Cache(file_path=self.temporary_path)
        cache_01.userId = UUID("00000000-0000-0000-0000-000000000001")
        cache_01.save()

        cache_02 = Cache(file_path=self.temporary_path)
        self.assertEqual(UUID("00000000-0000-0000-0000-000000000001"), cache_02.userId)
