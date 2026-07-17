import json
import os

class Config:
    def __init__(self):
        # 修复：文件名是 config.json 不是 setting.json
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r") as f:
            data = json.load(f)
        
        self.base_url = data.get("base_url", "")
        self.username = data.get("credentials", {}).get("username", "")
        self.password = data.get("credentials", {}).get("password", "")
        self.headless = data.get("browser_settings", {}).get("headless", False)

config = Config()
