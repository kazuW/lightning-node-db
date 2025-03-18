import sqlite3
from sqlite3 import Error
from datetime import datetime
import os

class Database:
    """SQLite3 database manager for Lightning Network node channel data."""
    
    def __init__(self, db_path):
        """Initialize with database file path."""
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Create a database connection to the SQLite database with UTF-8 support."""
        try:
            # SQLite データベースに接続する際に UTF-8 をデフォルトとして設定
            self.conn = sqlite3.connect(self.db_path)
            
            # テキストの読み取り/書き込み時に UTF-8 を使用するよう設定
            self.conn.text_factory = str  # Python 3 では UTF-8 がデフォルト
            
            # 外部キー制約を有効にする
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # クエリ結果を辞書形式で取得できるように設定（オプション）
            self.conn.row_factory = sqlite3.Row
            
            return True
        except Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def initialize(self, update_channel=False):
        """必要なテーブルを作成してデータベースを初期化します。"""
        if not self.conn:
            if not self.connect():
                return False
        
        # update_channel フラグが True の場合、channel_lists テーブルを再構築
        if update_channel:
            self.rebuild_channel_lists_table()
        else:
            self.create_channel_lists_table()
            
        self.create_channel_datas_table()
        return True

    def rebuild_channel_lists_table(self):
        """channel_lists テーブルを削除し、更新されたスキーマで再作成します。"""
        try:
            cursor = self.conn.cursor()
            
            # トランザクション開始
            self.conn.execute("BEGIN TRANSACTION")
            
            # 一時的に外部キー制約を無効化
            self.conn.execute("PRAGMA foreign_keys = OFF")
            
            # channel_datas テーブルのデータをバックアップ（またはチャンネルIDを保存）
            cursor.execute("SELECT DISTINCT channel_id FROM channel_datas")
            channel_ids = [row[0] for row in cursor.fetchall()]
            
            # 既存のテーブルを削除
            cursor.execute("DROP TABLE IF EXISTS channel_lists")
            
            # 新しいスキーマでテーブルを作成
            self.create_channel_lists_table()
            
            # 外部キー制約を再度有効化
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # トランザクションをコミット
            self.conn.commit()
            print("channel_point カラムを追加して channel_lists テーブルの再構築に成功しました")
            
            # 重要な警告を表示
            if channel_ids:
                print(f"警告: {len(channel_ids)} 件のチャンネルが channel_datas テーブルから参照されています。")
                print("これらのチャンネル情報を channel_lists に再登録してください。そうしないとデータ整合性が失われます。")
        except Error as e:
            # エラー時はロールバック
            self.conn.rollback()
            # 外部キー制約を確実に再有効化
            try:
                self.conn.execute("PRAGMA foreign_keys = ON")
            except:
                pass
            print(f"channel_lists テーブル再構築中にエラー発生: {e}")

    def create_channel_lists_table(self):
        """channel_lists テーブルを作成します。"""
        sql = '''CREATE TABLE IF NOT EXISTS channel_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_name TEXT NOT NULL,
                    channel_id TEXT NOT NULL UNIQUE,
                    channel_point TEXT,
                    capacity INTEGER NOT NULL
                  );'''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except Error as e:
            print(f"channel_lists テーブル作成中にエラー発生: {e}")
    
    def create_channel_datas_table(self):
        """Create the channel_datas table with channel_id as foreign key."""
        sql = '''CREATE TABLE IF NOT EXISTS channel_datas (
                    channel_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    local_balance INTEGER,
                    local_fee INTEGER,
                    local_infee INTEGER,
                    remote_balance INTEGER,
                    remote_fee INTEGER,
                    remote_infee INTEGER,
                    num_updates INTEGER,
                    amboss_fee INTEGER,
                    active INTEGER,
                    FOREIGN KEY (channel_id) REFERENCES channel_lists (channel_id)
                  );'''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except Error as e:
            print(f"Error creating channel_datas table: {e}")
    
    def update_channel_lists(self, channels):
        """バルクアップデートのためのトランザクション最適化を実装"""
        if not self.conn:
            self.connect()
        
        try:
            # トランザクションを開始
            self.conn.execute("BEGIN TRANSACTION")
            
            # 現在のチャンネルデータを取得
            current_channels = self._get_current_channels()
            current_channel_ids = {channel['channel_id'] for channel in current_channels}
            
            # API から取得したチャンネル ID のセットを作成
            api_channel_ids = set()
            inserted_channels = []
            updated_channels = []
            
            # チャンネルを更新またはインサート
            for channel in channels:
                channel_id = channel.get('chan_id', '')
                if not channel_id:
                    continue
                    
                api_channel_ids.add(channel_id)
                
                #debug
                #print("##### channel #####")
                #print(channel)

                # チャンネルを更新またはインサート
                result = self.update_channel(
                    channel.get('peer_alias', ''), 
                    channel_id,
                    channel.get('channel_point', ''),  # channel_point を追加
                    channel.get('capacity', 0)
                )
                
                # 新規追加か更新かを判定
                if channel_id in current_channel_ids:
                    updated_channels.append(channel)
                else:
                    inserted_channels.append(channel)
            
            # API に存在しない古いチャンネルを削除
            deleted_channels = self._delete_removed_channels(current_channels, api_channel_ids)
            
            # トランザクションをコミット
            self.conn.commit()
            
            # ログ出力（トランザクション外で行う）
            self._log_channel_changes(inserted_channels, updated_channels, deleted_channels)
            
            return {
                'inserted': len(inserted_channels),
                'updated': len(updated_channels),
                'deleted': len(deleted_channels)
            }
        except Exception as e:
            # エラーが発生した場合はロールバック
            self.conn.rollback()
            print(f"データベース更新中にエラーが発生しました: {e}")
            return {'error': str(e)}

    def _get_current_channels(self):
        """現在のデータベースに存在するすべてのチャンネル情報を取得"""
        if not self.conn:
            self.connect()
            
        sql = "SELECT id, channel_id, channel_name, channel_point, capacity FROM channel_lists;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'channel_id': row[1],
                'channel_name': row[2],
                'channel_point': row[3],
                'capacity': row[4]
            } for row in rows]
        except Error as e:
            print(f"Error retrieving channels: {e}")
            return []

    def _delete_removed_channels(self, current_channels, api_channel_ids):
        """
        API に存在しないチャンネルをデータベースから削除
        
        Args:
            current_channels: 現在のデータベースに存在するチャンネル情報のリスト
            api_channel_ids: API から取得したチャンネル ID のセット
        
        Returns:
            deleted_channels: 削除されたチャンネル情報のリスト
        """
        if not self.conn:
            self.connect()
        
        # 削除するチャンネルを特定
        channels_to_delete = []
        for channel in current_channels:
            if channel['channel_id'] not in api_channel_ids:
                channels_to_delete.append(channel)
        
        if not channels_to_delete:
            return []  # 削除するものがない
        
        try:
            cursor = self.conn.cursor()
            
            # チャンネルIDリストを作成
            channel_ids_to_delete = [channel['channel_id'] for channel in channels_to_delete]
            placeholders = ', '.join(['?'] * len(channel_ids_to_delete))
            
            # チャンネルデータを削除 (外部キー制約のため先に削除)
            # 修正: channel_datasテーブルのカラムはidではなくchannel_idを参照する
            sql_delete_data = f"""DELETE FROM channel_datas 
                                 WHERE channel_id IN ({placeholders});"""
            cursor.execute(sql_delete_data, channel_ids_to_delete)
            
            # チャンネル自体を削除
            sql_delete_channel = f"DELETE FROM channel_lists WHERE channel_id IN ({placeholders});"
            cursor.execute(sql_delete_channel, channel_ids_to_delete)
            
            self.conn.commit()
            return channels_to_delete
        except Error as e:
            print(f"チャンネル削除中にエラーが発生しました: {e}")
            return []

    def _log_channel_changes(self, inserted, updated, deleted):
        """
        チャンネルの変更をログに記録
        
        Args:
            inserted: 新規追加されたチャンネルのリスト
            updated: 更新されたチャンネルのリスト
            deleted: 削除されたチャンネルのリスト
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # ログファイルパスを設定
        #log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        log_dir = "D:\LightningNetwork\lightning-node-db\logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'channel_changes.log')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            # ヘッダー
            f.write(f"\n===== チャンネル更新ログ: {timestamp} =====\n")
            
            # 新規追加チャンネル
            if inserted:
                f.write(f"\n--- 新規追加されたチャンネル ({len(inserted)}件) ---\n")
                for channel in inserted:
                    f.write(f"ID: {channel.get('channel_id')}, 名前: {channel.get('channel_name')}, 容量: {channel.get('capacity')}\n")
            
            # 更新されたチャンネル
            #if updated:
            #    f.write(f"\n--- 更新されたチャンネル ({len(updated)}件) ---\n")
            #    for channel in updated:
            #        f.write(f"ID: {channel.get('channel_id')}, 名前: {channel.get('channel_name')}, 容量: {channel.get('capacity')}\n")
         
            # 削除されたチャンネル
            if deleted:
                f.write(f"\n--- 削除されたチャンネル ({len(deleted)}件) ---\n")
                for channel in deleted:
                    f.write(f"ID: {channel.get('chan_id')}, 名前: {channel.get('peer_alias')}, 容量: {channel.get('capacity')}\n")
        
        # コンソールにも出力
        print(f"\nチャンネル更新ログ: {timestamp}")
        print(f"- 新規追加: {len(inserted)}件")
        print(f"- 更新: {len(updated)}件")
        print(f"- 削除: {len(deleted)}件")
        print(f"詳細ログは {log_file} に保存されました。")

    def update_channel(self, channel_name, channel_id, channel_point, capacity):
        """UTF-8エンコーディングを使用してchannel_listsテーブルにチャンネルを更新または挿入します。"""
        sql = '''INSERT INTO channel_lists (channel_name, channel_id, channel_point, capacity)
                 VALUES (?, ?, ?, ?)
                 ON CONFLICT(channel_id) DO UPDATE SET
                 channel_name=excluded.channel_name,
                 channel_point=excluded.channel_point,
                 capacity=excluded.capacity;'''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (channel_name, channel_id, channel_point, capacity))
            self.conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"チャンネル更新中にエラー発生: {e}")
            return None
    
    def update_channel_data(self, channel, data, amboss_fee):
        """Insert channel data for a specific channel."""
        sql = '''INSERT INTO channel_datas 
                 (channel_id, date, local_balance, local_fee, local_infee, 
                  remote_balance, remote_fee, remote_infee, num_updates, amboss_fee, active)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
        try:
            if channel.get('remote_pubkey', '') == data.get('node1_pub', ''):
                remote_fee = data.get('node1_policy', {}).get('fee_rate_milli_msat', 0)
                remote_infee = data.get('node1_policy', {}).get('inbound_fee_rate_milli_msat', 0)
                local_fee = data.get('node2_policy', {}).get('fee_rate_milli_msat', 0)
                local_infee = data.get('node2_policy', {}).get('inbound_fee_rate_milli_msat', 0)
            else:
                remote_fee = data.get('node2_policy', {}).get('fee_rate_milli_msat', 0)
                remote_infee = data.get('node2_policy', {}).get('inbound_fee_rate_milli_msat', 0)
                local_fee = data.get('node1_policy', {}).get('fee_rate_milli_msat', 0)
                local_infee = data.get('node1_policy', {}).get('inbound_fee_rate_milli_msat', 0)
            
            active_stat = int(channel.get('active', False))

            cursor = self.conn.cursor()
            cursor.execute(sql, (
                channel.get('chan_id', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                channel.get('local_balance', 0),
                local_fee,
                local_infee,
                channel.get('remote_balance', 0),
                remote_fee,
                remote_infee,
                channel.get('num_updates', 0),
                amboss_fee,
                active_stat
            ))
            self.conn.commit()
        except Error as e:
            print(f"Error updating channel data: {e}")
    
    def delete_old_data(self, months):
        """Delete old channel data older than specified months."""
        sql = '''DELETE FROM channel_datas
                 WHERE date < date('now', ?);'''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (f'-{months} months',))
            self.conn.commit()
            return cursor.rowcount
        except Error as e:
            print(f"Error deleting old data: {e}")
            return 0
    
    def get_channel_by_id(self, channel_id):
        """Get channel by channel_id."""
        sql = "SELECT * FROM channel_lists WHERE channel_id = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (channel_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error retrieving channel: {e}")
            return None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def bulk_insert_channels(self, channels):
        """複数チャンネルを一度に挿入（高速）"""
        if not channels:
            return 0
            
        sql = '''INSERT OR IGNORE INTO channel_lists (channel_name, channel_id, channel_point, capacity)
                 VALUES (?, ?, ?, ?);'''
        
        try:
            cursor = self.conn.cursor()
            # executemany を使用して一括処理
            values = [(ch.get('peer_alias', ''), ch.get('chan_id', ''), ch.get('channel_point', ''), ch.get('capacity', 0)) 
                     for ch in channels]
            cursor.executemany(sql, values)
            return cursor.rowcount
        except Error as e:
            print(f"バルク挿入エラー: {e}")
            return 0

    def add_active_column_to_channel_datas(self):
        """channel_datasテーブルにactiveカラムを追加し、既存のレコードを1に設定する"""
        try:
            # カラムが既に存在するかチェック
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(channel_datas)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'active' not in columns:
                print("'active'カラムをchannel_datasテーブルに追加しています...")
                
                # トランザクションを開始
                self.conn.execute("BEGIN TRANSACTION")
                
                # 新しいカラムを追加
                self.conn.execute("ALTER TABLE channel_datas ADD COLUMN active INTEGER DEFAULT 1")
                
                # 既存のレコードすべてに対してactive=1を設定
                self.conn.execute("UPDATE channel_datas SET active = 1")
                
                # トランザクションをコミット
                self.conn.commit()
                
                print("'active'カラムの追加が完了しました")
            else:
                print("'active'カラムは既に存在しています")
                
        except Exception as e:
            self.conn.rollback()
            print(f"データベース更新中にエラーが発生しました: {e}")
            raise