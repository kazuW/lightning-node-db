import os
import sys
import argparse
from pathlib import Path

# インポートパスをプロジェクトルートに設定（最初に実行）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 修正後のインポート文
from src.db.database import Database
from src.api.lightning_client import get_channel_lists, get_channel_data, get_amboss_fee
from src.utils.config import Config  # load_config ではなく Config をインポート

def main(delete_old_data=None):
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
        #amboss_fee = get_amboss_fee(channel['remote_pubkey'], config)
        amboss_fee = get_amboss_fee("039cdd937f8d83fb2f78c8d7ddc92ae28c9dbb5c4827181cfc80df60dee1b7bf19", config)
        db.update_channel_data(channel, channel_data, amboss_fee)

    # Optionally delete old data
    if delete_old_data:
        db.delete_old_data(delete_old_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightning Node Database Management")
    parser.add_argument('--delete', type=int, help="Delete data older than x months")
    args = parser.parse_args()

    main(delete_old_data=args.delete)