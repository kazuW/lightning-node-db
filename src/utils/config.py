import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_file=None):
        # デフォルトのconfig.yamlの場所を指定
        if config_file is None:
            # プロジェクトのルートディレクトリを基準にした設定ファイルのパス
            project_root = Path(__file__).parent.parent.parent
            config_file = os.path.join(project_root, 'config.yaml')
        
        self.config_file = config_file
        self.settings = self.load_config()
    
    def load_config(self):
        if not os.path.exists(self.config_file):
            # ファイルが見つからない場合はデフォルト設定を返す
            print(f"警告: 設定ファイル '{self.config_file}' が見つかりません。デフォルト設定を使用します。")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """デフォルトの設定値を返す"""
        return {
            'database': {
                'path': os.path.join(Path(__file__).parent.parent.parent, 'data', 'lightning_node.db')
            },
            'retention_period': 3
        }

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def get_database_config(self):
        return self.get('database', {})

    def get_retention_period(self):
        return self.get('retention_period', 3)  # Default to 3 months if not specified