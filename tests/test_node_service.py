import unittest
from src.api.node_service import NodeService
from unittest.mock import patch, MagicMock

class TestNodeService(unittest.TestCase):

    @patch('src.api.lightning_client.get_channel_list')
    @patch('src.db.database.insert_channel_list')
    def test_update_channel_list(self, mock_insert_channel_list, mock_get_channel_list):
        mock_get_channel_list.return_value = [
            {'channel_name': 'channel1', 'channel_id': '123', 'capacity': 1000000},
            {'channel_name': 'channel2', 'channel_id': '456', 'capacity': 2000000}
        ]
        
        service = NodeService()
        service.update_channel_list()

        mock_get_channel_list.assert_called_once()
        self.assertEqual(mock_insert_channel_list.call_count, 2)

    @patch('src.api.lightning_client.get_channel_data')
    @patch('src.db.database.insert_channel_data')
    def test_update_channel_data(self, mock_insert_channel_data, mock_get_channel_data):
        mock_get_channel_data.return_value = {
            'local_balance': 500000,
            'local_fee': 100,
            'local_infee': 50,
            'remote_balance': 600000,
            'remote_fee': 150,
            'remote_infee': 75
        }
        
        service = NodeService()
        service.update_channel_data('123')

        mock_get_channel_data.assert_called_once_with('123')
        mock_insert_channel_data.assert_called_once()

    @patch('src.db.database.delete_old_data')
    def test_delete_old_data(self, mock_delete_old_data):
        service = NodeService()
        service.delete_old_data(3)

        mock_delete_old_data.assert_called_once_with(3)

if __name__ == '__main__':
    unittest.main()