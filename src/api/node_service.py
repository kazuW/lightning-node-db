from datetime import datetime
from src.db.database import Database
from src.api.lightning_client import LightningClient

class NodeService:
    def __init__(self, db_path):
        self.db = Database(db_path)
        self.client = LightningClient()

    def update_channel_list(self):
        channel_list = self.client.get_channel_list()
        for channel in channel_list:
            self.db.upsert_channel(channel)

    def update_channel_data(self):
        channel_data = self.client.get_channel_data()
        for data in channel_data:
            self.db.insert_channel_data(data)

    def delete_old_data(self, months):
        cutoff_date = datetime.now().replace(day=1) - timedelta(days=months*30)
        self.db.delete_old_channel_data(cutoff_date)

    def run(self, delete_months=None):
        self.update_channel_list()
        self.update_channel_data()
        if delete_months:
            self.delete_old_data(delete_months)