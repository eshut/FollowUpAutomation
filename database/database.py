import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from datetime import datetime, timedelta
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
        query = PartnerQueries.update_last_followup()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (partner_id,))
                self.connection.commit()
                logger.info(f"Updated lastFollowUp for partner ID {partner_id}")
                return True
        except psycopg2.Error as e:
            logger.error(f"Error updating lastFollowUp: {e}")
            self.connection.rollback()
            return False


class PartnerFilter:
    @staticmethod
    def filter_by_followup_date(partners: List[Dict], days_ago: int = 30) -> List[Dict]:
        cutoff_date = datetime.now().date() - timedelta(days=days_ago)
        
        filtered = []
        for partner in partners:
            last_followup = partner.get('lastFollowUp')
            if last_followup and last_followup < cutoff_date:
                filtered.append(partner)
        
        logger.info(f"Filtered {len(filtered)} partners with lastFollowUp > {days_ago} days ago")
        return filtered
    
    @staticmethod
    def filter_by_status(partners: List[Dict], status: str) -> List[Dict]:
        filtered = [p for p in partners if p.get('status') == status]
        logger.info(f"Filtered {len(filtered)} partners with status {status}")
        return filtered
    
    @staticmethod
    def filter_by_priority(partners: List[Dict], priority: str) -> List[Dict]:
        filtered = [p for p in partners if p.get('priopity') == priority]
        logger.info(f"Filtered {len(filtered)} partners with priority {priority}")
        return filtered
    
    @staticmethod
    def filter_partners(
        partners: List[Dict],
        status: Optional[str] = None,
        priority: Optional[str] = None,
        days_since_followup: Optional[int] = None
    ) -> List[Dict]:
        filtered = partners
        
        if status:
            filtered = PartnerFilter.filter_by_status(filtered, status)
        
        if priority:
            filtered = PartnerFilter.filter_by_priority(filtered, priority)
        
        if days_since_followup:
            filtered = PartnerFilter.filter_by_followup_date(filtered, days_since_followup)
        
        return filtered


class PartnerPrinter:
    @staticmethod
    def print(partners: List[Dict]):
        if not partners:
            print("No partners found.")
            return
        
        print("\n" + "="*100)
        print(f"{'PARTNERS LIST':^100}")
        print("="*100)
        
        for partner in partners:
            name = partner.get('name', 'N/A')
            telegram_link = partner.get('telegramLinkPrimaryLinkUrl', 'N/A')
            upwork_link = partner.get('upworkLinkPrimaryLinkUrl', 'N/A')
            status = partner.get('status', 'N/A')
            priority = partner.get('priopity', 'N/A')
            last_followup = partner.get('lastFollowUp', 'N/A')
            
            print(f"\n{name} - {upwork_link}")
            print(f"  Status: {status} | Priority: {priority} | Last Follow-up: {last_followup}")
            if telegram_link:
                print(f"  Telegram: {telegram_link}")
        
        print("\n" + "="*100)
        print(f"Total partners: {len(partners)}")
        print("="*100 + "\n")

