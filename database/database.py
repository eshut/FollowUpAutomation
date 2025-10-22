import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import logging

from config import Config
from .queries import PartnerQueries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.config = Config().db.to_dict()
        self.connection = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.config)
            logger.info("Successfully connected to the database")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def get_all_partners(self) -> List[Dict]:
        query = PartnerQueries.get_all_partners()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                partners = cursor.fetchall()
                logger.info(f"Retrieved {len(partners)} partners from database")
                return [dict(partner) for partner in partners]
        except psycopg2.Error as e:
            logger.error(f"Error fetching partners: {e}")
            return []
    
    def get_partners_by_telegram_tag(self, telegram_tag: str) -> List[Dict]:
        query = PartnerQueries.get_partners_by_tag()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (telegram_tag,))
                partners = cursor.fetchall()
                logger.info(f"Retrieved {len(partners)} partners with tag {telegram_tag}")
                return [dict(partner) for partner in partners]
        except psycopg2.Error as e:
            logger.error(f"Error fetching partners by tag: {e}")
            return []
    
    def get_partners_with_telegram(self) -> List[Dict]:
        query = PartnerQueries.get_partners_with_telegram()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                partners = cursor.fetchall()
                logger.info(f"Retrieved {len(partners)} partners with telegram tags")
                return [dict(partner) for partner in partners]
        except psycopg2.Error as e:
            logger.error(f"Error fetching partners with telegram: {e}")
            return []
    
    def update_last_contacted(self, partner_id: int) -> bool:
        query = PartnerQueries.update_last_contacted()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (partner_id,))
                self.connection.commit()
                logger.info(f"Updated last_contacted for partner ID {partner_id}")
                return True
        except psycopg2.Error as e:
            logger.error(f"Error updating last_contacted: {e}")
            self.connection.rollback()
            return False


class PartnerPrinter:
    @staticmethod
    def print(partners: List[Dict]):
        if not partners:
            print("No partners found.")
            return
        
        print("\n" + "="*70)
        print(f"{'PARTNERS LIST':^70}")
        print("="*70)
        
        for partner in partners:
            name = partner.get('name', 'N/A')
            link = partner.get('link', 'N/A')
            telegram_tag = partner.get('telegram_tag', '')
            
            print(f"\n{name} - {link}")
            if telegram_tag:
                print(f"  Telegram: {telegram_tag}")
        
        print("\n" + "="*70)
        print(f"Total partners: {len(partners)}")
        print("="*70 + "\n")

