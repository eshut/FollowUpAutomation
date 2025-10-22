import os
from pathlib import Path
from dotenv import load_dotenv

from .constants import DEFAULT_DB_PORT, DEFAULT_TELEGRAM_SESSION_NAME


class Config:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.env_path = self.base_dir / '.env'
        load_dotenv(self.env_path)
        
        self.db = self.DatabaseConfig()
        self.telegram = self.TelegramConfig()
    
    class DatabaseConfig:
        def __init__(self):
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = int(os.getenv('DB_PORT', DEFAULT_DB_PORT))
            self.database = os.getenv('DB_NAME')
            self.user = os.getenv('DB_USER')
            self.password = os.getenv('DB_PASSWORD')
        
        def to_dict(self):
            return {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password
            }
    
    class TelegramConfig:
        def __init__(self):
            self.api_id = os.getenv('TELEGRAM_API_ID')
            self.api_hash = os.getenv('TELEGRAM_API_HASH')
            self.phone = os.getenv('TELEGRAM_PHONE')
            self.session_name = os.getenv('TELEGRAM_SESSION_NAME', DEFAULT_TELEGRAM_SESSION_NAME)
        
        def to_dict(self):
            return {
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'phone': self.phone,
                'session_name': self.session_name
            }

