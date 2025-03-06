import unittest
import sqlite3
from src.db.database import Database

class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = Database('test.db')
        cls.db.create_tables()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        import os
        os.remove('test.db')

    def test_insert_channel_list(self):
        channel_data = {
            'channel_name': 'Test Channel',
            'channel_id': '12345',
            'capacity': 1000000
        }
        channel_id = self.db.insert_channel_list(channel_data)
        self.assertIsNotNone(channel_id)

    def test_update_channel_list(self):
        channel_data = {
            'channel_name': 'Updated Channel',
            'channel_id': '12345',
            'capacity': 2000000
        }
        self.db.update_channel_list(1, channel_data)
        updated_channel = self.db.get_channel_list(1)
        self.assertEqual(updated_channel['channel_name'], 'Updated Channel')

    def test_delete_channel_list(self):
        self.db.delete_channel_list(1)
        channel = self.db.get_channel_list(1)
        self.assertIsNone(channel)

    def test_insert_channel_data(self):
        channel_data = {
            'id': 1,
            'date': '2023-10-01',
            'local_balance': 500000,
            'local_fee': 100,
            'local_infee': 50,
            'remote_balance': 500000,
            'remote_fee': 100,
            'remote_infee': 50
        }
        data_id = self.db.insert_channel_data(channel_data)
        self.assertIsNotNone(data_id)

    def test_delete_old_data(self):
        self.db.delete_old_data(1)  # Assuming 1 month retention
        # Add assertions to verify old data deletion

if __name__ == '__main__':
    unittest.main()