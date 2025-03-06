import os
import yaml

class Config:
    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.settings = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")
        
        with open(self.config_file, 'r') as file:
            return yaml.safe_load(file)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def get_database_config(self):
        return self.get('database', {})

    def get_retention_period(self):
        return self.get('retention_period', 3)  # Default to 3 months if not specified