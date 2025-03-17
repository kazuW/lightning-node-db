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

def resource_path(relative_path):
    """実行環境に応じたリソースパスを返す"""
    try:
        # PyInstallerの環境かチェック
        base_path = sys._MEIPASS
        is_exe = True
    except Exception:
        # 通常のPython実行環境
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        is_exe = False
    
    return os.path.join(base_path, relative_path), is_exe

def main(delete_old_data=None, update=False):
    # リソースパスとexe環境かどうかを取得
    config_path, is_exe = resource_path('config.yaml')
    
    if is_exe:
        # exe環境では複数のパスを試す
        print(f"設定ファイルのパス (exe環境): {config_path}")
        if not os.path.exists(config_path):
            print(f"警告: 設定ファイルが見つかりません: {config_path}")
            # 複数の代替パスを試す
            alt_paths = [
                os.path.join(os.getcwd(), 'config.yaml'),  
                os.path.join(os.path.expanduser('~'), '.lightning-node-db', 'config.yaml')
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    config_path = alt_path
                    print(f"代替設定ファイルを使用: {alt_path}")
                    break
    
    # ConfigクラスはPath(__file__).parent.parent.parentを使用しているので、
    # 明示的にパスを渡すとよい
    config = Config(config_file=config_path)
    
    # データベースパスの確認（exe環境の場合のみ）
    db_path = config.get_database_config().get('path')
    if is_exe:
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            print(f"データディレクトリを作成: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
    
    db = Database(db_path)
    
    # Initialize database and create tables
    db.initialize()

    # アップデートモードの場合、channel_datasテーブルに'active'カラムを追加して終了
    if update:
        print("データベースの更新を実行しています...")
        db.add_active_column_to_channel_datas()
        print("データベースの更新が完了しました。")
        return

    # 通常モード: データ取得と更新
    
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
    parser.add_argument('--update', action='store_true', help="Update database schema only (add 'active' column to channel_datas)")
    args = parser.parse_args()

    main(delete_old_data=args.delete, update=args.update)