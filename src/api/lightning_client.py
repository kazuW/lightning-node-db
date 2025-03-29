import requests
import codecs
import json
import os
from datetime import datetime, timedelta
import sqlite3

def get_channel_lists(config=None):
    if not config:
        raise ValueError("Configuration is required")

    # 通常の実行時はAPI呼び出し
    # configを使用してLightningネットワークの接続設定を取得
    rest_host = config.get('lightning', {}).get('api_url')
    macaroon_path = config.get('lightning', {}).get('macaroon_path')
    tls_path = config.get('lightning', {}).get('tls_path')
    
    if not all([rest_host, macaroon_path, tls_path]):
        raise ValueError("Missing required Lightning configuration")

    url = f'{rest_host}/v1/channels'
    macaroon = codecs.encode(open(macaroon_path, 'rb').read(), 'hex')
    headers = {'Grpc-Metadata-macaroon': macaroon}
    
    # alias
    params = {
        "peer_alias_lookup": "true"
    }

    try:
        response = requests.get(url, headers=headers, verify=tls_path, params=params)
        response.raise_for_status()
        
        # APIレスポンスから必要なデータを抽出
        channel_lists_data = response.json().get('channels', [])
        return channel_lists_data
    except requests.exceptions.RequestException as e:
        # エラー発生時は、空のリストを返す
        return []

def get_channel_data(channel_id, config=None):
    if not config:
        raise ValueError("Configuration is required")

    # 通常の実行時はAPI呼び出し
    # configを使用してLightningネットワークの接続設定を取得
    rest_host = config.get('lightning', {}).get('api_url')
    macaroon_path = config.get('lightning', {}).get('macaroon_path')
    tls_path = config.get('lightning', {}).get('tls_path')
    
    if not all([rest_host, macaroon_path, tls_path]):
        raise ValueError("Missing required Lightning configuration")

    url = f'{rest_host}/v1/graph/edge/{channel_id}'
    macaroon = codecs.encode(open(macaroon_path, 'rb').read(), 'hex')
    headers = {'Grpc-Metadata-macaroon': macaroon}

    try:
        response = requests.get(url, headers=headers, verify=tls_path)
        response.raise_for_status()
        channel_data = response.json()
        return channel_data
    except requests.exceptions.RequestException as e:
        # エラー発生時は、エラー情報を含むディクショナリを返す
        return {"error": True, "message": str(e)}

def update_channel_list(db_connection, channel_data):
    cursor = db_connection.cursor()
    for channel in channel_data:
        cursor.execute("""
            INSERT INTO channel_lists (channel_name, channel_id, capacity)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                channel_name = excluded.channel_name,
                capacity = excluded.capacity
        """, (channel['channel_name'], channel['channel_id'], channel['capacity']))
    db_connection.commit()

def update_channel_data(db_connection, channel_id, data):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO channel_datas (id, date, local_balance, local_fee, local_infee, remote_balance, remote_fee, remote_infee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (channel_id, datetime.now(), data['local_balance'], data['local_fee'], data['local_infee'], data['remote_balance'], data['remote_fee'], data['remote_infee']))
    db_connection.commit()

def delete_old_data(db_connection, months):
    cursor = db_connection.cursor()
    cutoff_date = datetime.now().replace(day=1) - timedelta(days=months*30)
    cursor.execute("DELETE FROM channel_datas WHERE date < ?", (cutoff_date,))
    db_connection.commit()

def get_amboss_fee(remote_pubkey, config=None):
    """
    Amboss APIから指定されたノードの手数料情報を取得する
    整数値に変換して返す
    エラーが発生した場合はデフォルト値を返す
    """
    # デフォルト値を設定
    default_fee = 2000
    
    try:
        if not config:
            print("configがありません。デフォルト値を返します。")
            return default_fee

        # 通常の実行時はAPI呼び出し
        # configを使用してAmboss APIの接続設定を取得
        api_key = config.get('amboss', {}).get('api_key')
        rest_host = config.get('amboss', {}).get('api_url', 'api.amboss.space')
        
        if not api_key:
            print("Amboss API キーが設定されていません。デフォルト値を返します。")
            return default_fee

        url = f'{rest_host}/graphql'

        # GraphQLクエリ
        query = """
        query Query($pubkey: String!) {
        getNode(pubkey: $pubkey) {
            graph_info {
            channels {
                fee_info {
                remote {
                    weighted_corrected
                }
                }
            }
            }
        }
        }
        """

        # クエリの変数
        variables = {
            "pubkey": remote_pubkey
        }

        # ヘッダー設定
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # リクエストを送信
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

        # 例外処理
        response.raise_for_status()

        # レスポンスからデータを抽出
        response_data = response.json()
        #print("#### response data = ", response_data)

        # データを解析して手数料を取得
        try:
            fee_info = response_data.get('data', {}).get('getNode', {}).get('graph_info', {})
            channels = fee_info.get('channels', [])
            
            fee = channels.get('fee_info', {}).get('remote', {}).get('weighted_corrected')
            if fee is not None:
                # 浮動小数点数を整数に変換（小数点以下切り捨て）
                return int(float(fee))
            
            print(f"ノード {remote_pubkey} の手数料情報が取得できませんでした。デフォルト値を返します。")
            return default_fee
            
        except (KeyError, IndexError, ValueError) as e:
            print(f"手数料情報のパース中にエラーが発生しました: {e}")
            return default_fee

    except Exception as e:
        print(f"Amboss API呼び出し中にエラーが発生しました: {e}")
        return default_fee