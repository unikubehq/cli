import os
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from unikube.cluster.storage.cluster_storage import ClusterStorage


class ClusterStorageTest(unittest.TestCase):
    def setUp(self):
        self.temporary_path_object = tempfile.TemporaryDirectory()
        self.temporary_path = self.temporary_path_object.name

    def tearDown(self):
        self.temporary_path_object.cleanup()

    def test_missing_id(self):
        with self.assertRaises(Exception):
            _ = ClusterStorage(file_path=self.temporary_path)

    def test_save(self):
        cluster_storage = ClusterStorage(file_path=self.temporary_path, id=UUID("00000000-0000-0000-0000-000000000000"))
        cluster_storage.save()

        file = Path(os.path.join(cluster_storage.file_path, cluster_storage.file_name))

        self.assertTrue(file.exists())
        self.assertEqual(UUID("00000000-0000-0000-0000-000000000000"), cluster_storage.id)

    def test_load(self):
        cluster_storage_01 = ClusterStorage(
            file_path=self.temporary_path, id=UUID("00000000-0000-0000-0000-000000000000")
        )
        cluster_storage_01.name = "test"
        cluster_storage_01.save()

        cluster_storage_02 = ClusterStorage(
            file_path=self.temporary_path, id=UUID("00000000-0000-0000-0000-000000000000")
        )
        self.assertEqual("test", cluster_storage_02.name)
