import json
from config import Config

class Database:
    @staticmethod
    def load():
        Config.init_data_folder()
        if os.path.exists(Config.DB_FILE):
            with open(Config.DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Dữ liệu mặc định
        default = {
            "contracts": [],
            "warehouse_cells": {
                "A-01": {"status": "occupied", "tenant": "Cty TNHH Tuấn Châu", "period": "01/08 - 31/12/2024", "area": "80m²"},
                "A-03": {"status": "available", "area": "80m²"},
                "B-04": {"status": "reserved", "tenant": "Sunrise Express", "period": "Đặt trước", "area": "100m²"}
            },
            "customers": [],
            "inventory": []
        }
        Database.save(default)
        return default

    @staticmethod
    def save(data):
        with open(Config.DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)