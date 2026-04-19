import os

class Config:
    SECRET_KEY = 'warehouse_ms_secret_key_2026'
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    DB_FILE = os.path.join(DATA_DIR, 'db.json')

    @staticmethod
    def init_data_folder():
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)