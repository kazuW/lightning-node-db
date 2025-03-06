import os
import sys
import argparse
from db.database import Database
from api.lightning_client import get_channel_lists, get_channel_data, get_amboss_fee
from utils.config import Config  # load_config ではなく Config をインポート

def main(delete_old_data=None):
    # Config クラスのインスタンスを作成して使用
    config = Config()
    db = Database(config.get_database_config().get('path'))

    # Initialize database and create tables
    db.initialize()

    # Retrieve channel lists and update database
    # Config オブジェクトを渡す
    channel_lists = get_channel_lists(config)
    db.update_channel_lists(channel_lists)

    # Retrieve channel data and update database
    for channel in channel_lists:
        channel_data = get_channel_data(channel['chan_id'], config)
        amboss_fee = get_amboss_fee(channel['remote_pubkey'])
        
        #amboss_fee = get_amboss_fee("039cdd937f8d83fb2f78c8d7ddc92ae28c9dbb5c4827181cfc80df60dee1b7bf19", config)
        #print(f"Amboss fee: {amboss_fee}")

        db.update_channel_data(channel, channel_data, amboss_fee)

    # Optionally delete old data
    if delete_old_data:
        db.delete_old_data(delete_old_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightning Node Database Management")
    parser.add_argument('--delete', type=int, help="Delete data older than x months")
    args = parser.parse_args()

    main(delete_old_data=args.delete)

def create_channel_lists_table(self):
    """Create the channel_lists table with proper indexes."""
    sql_table = '''CREATE TABLE IF NOT EXISTS channel_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT NOT NULL,
                channel_id TEXT NOT NULL UNIQUE,
                capacity INTEGER NOT NULL
              );'''
              
    sql_index = '''CREATE INDEX IF NOT EXISTS idx_channel_id 
                   ON channel_lists(channel_id);'''
    
    try:
        cursor = self.conn.cursor()
        cursor.execute(sql_table)
        cursor.execute(sql_index)
    except Error as e:
        print(f"Error creating channel_lists table: {e}")
        
def create_channel_datas_table(self):
    """Create the channel_datas table with indexes."""
    sql_table = '''CREATE TABLE IF NOT EXISTS channel_datas (
                id INTEGER NOT NULL,
                date TEXT NOT NULL,
                local_balance INTEGER,
                local_fee INTEGER,
                local_infee INTEGER,
                remote_balance INTEGER,
                remote_fee INTEGER,
                remote_infee INTEGER,
                FOREIGN KEY (id) REFERENCES channel_lists (id)
              );'''
              
    sql_index1 = '''CREATE INDEX IF NOT EXISTS idx_channel_datas_id 
                    ON channel_datas(id);'''
                    
    sql_index2 = '''CREATE INDEX IF NOT EXISTS idx_channel_datas_date 
                    ON channel_datas(date);'''
    
    try:
        cursor = self.conn.cursor()
        cursor.execute(sql_table)
        cursor.execute(sql_index1)
        cursor.execute(sql_index2)
    except Error as e:
        print(f"Error creating channel_datas table: {e}")