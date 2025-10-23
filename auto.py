import logging
from typing import Optional

from commands import PartnerListCommand
from config import DEFAULT_MESSAGE_TEMPLATE, MINUTE, MONTH
from database import DatabaseManager, PartnerFilter
from telegram import TelegramService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoMessenger:
    def __init__(self, min_message_interval: int = 60):
        self.db_manager = DatabaseManager()
        self.min_message_interval = min_message_interval
    
    def update_partner_followup_date(self, partner_id: str, set_datetime=None) -> bool:
        set_date = None
        if set_datetime:
            if hasattr(set_datetime, 'date'):
                set_date = set_datetime.date()
            else:
                set_date = set_datetime
        
        with DatabaseManager() as db:
            return db.update_last_contacted(partner_id, set_date=set_date)
    
    def send_messages_to_filtered_partners(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        days_since_followup: Optional[int] = None,
        message_template: Optional[str] = None,
        delay_between_messages: int = 2
    ):
        with self.db_manager:
            all_partners = self.db_manager.get_all_partners()
            
            filtered_partners = PartnerFilter.filter_partners(
                all_partners,
                status=status,
                priority=priority,
                days_since_followup=days_since_followup
            )
            
            logger.info(f"Found {len(filtered_partners)} partners matching filters")
            
            results = {
                'sent': 0,
                'skipped_no_telegram': 0,
                'skipped_too_soon': 0,
                'failed': 0
            }
            
            for partner in filtered_partners:
                telegram_link = partner.get('telegramLinkPrimaryLinkUrl')
                name = partner.get('name', 'Unknown')
                
                if not telegram_link:
                    logger.info(f"Skipping {name} - no Telegram link")
                    results['skipped_no_telegram'] += 1
                    continue
                
                message = message_template.replace('{name}', name) if message_template else f"Hello {name}!"
                
                result = TelegramService.send_message_with_time_check(
                    telegram_link,
                    message,
                    self.min_message_interval
                )
                
                if result['sent']:
                    logger.info(f"Message sent to {name}")
                    results['sent'] += 1
                    self.update_partner_followup_date(
                        partner['id'], 
                        set_datetime=result.get('last_msg_time')
                    )
                elif result['reason'] == 'too_soon':
                    logger.info(f"Skipped {name} - message sent {result['seconds_since_last']:.0f}s ago")
                    results['skipped_too_soon'] += 1
                else:
                    logger.error(f"Failed to send message to {name}")
                    results['failed'] += 1
                
                if delay_between_messages > 0:
                    import time
                    time.sleep(delay_between_messages)
            
            return results
    
    def send_to_high_priority_needing_followup(self, days: int = 30):
        logger.info(f"Sending messages to HIGH priority partners needing follow-up (>{days} days)")
        
        message = "Hi {name}! Just following up on our previous conversation. How are things going?"
        
        results = self.send_messages_to_filtered_partners(
            status='ACTIVE',
            priority='HIGH',
            days_since_followup=days,
            message_template=message,
            delay_between_messages=3
        )
        
        logger.info(f"Results: {results}")
        return results
    
    def message_single_user(self, user_id: str, message: str = "Test message"):
        logger.info("Step 1: Getting chat messages...")
        messages = TelegramService.get_chat_messages(user_id, limit=5)
        
        if messages:
            logger.info(f"Found {len(messages)} recent messages:")
            for msg in messages:
                direction = "OUT" if msg['out'] else "IN"
                text = msg['text'][:50] if msg['text'] else "[no text]"
                logger.info(f"  [{direction}] {msg['date']}: {text}")
        else:
            logger.info("No messages found")
        
        logger.info("\nStep 2: Checking last outgoing message time...")
        result = TelegramService.send_message_with_time_check(
            user_id,
            message,
            self.min_message_interval
        )
        
        logger.info(f"\nStep 3: Send result:")
        logger.info(f"  Sent: {result['sent']}")
        logger.info(f"  Reason: {result['reason']}")
        
        if 'seconds_since_last' in result:
            logger.info(f"  Seconds since last message: {result['seconds_since_last']:.0f}")
            logger.info(f"  Minimum required: {result['min_required']}")
        
        return result


class Auto:
    def __init__(self):
        self.auto = AutoMessenger(min_message_interval=MONTH)
        self.tg = 0

    def main(self):
        partners_from_db = PartnerListCommand().execute()
        for partner in partners_from_db:
            # TELEGRAM:
            if partner.get("telegramLinkPrimaryLinkUrl") != "":
                self.process_telegram_entry(partner)
                self.tg += 1

    def process_telegram_entry(self, partner):
        print(partner.get('name'), partner.get("telegramLinkPrimaryLinkUrl"))
        result = self.auto.message_single_user(partner.get('telegramLinkPrimaryLinkUrl'), DEFAULT_MESSAGE_TEMPLATE)
        if result.get('sent'):
            self.auto.update_partner_followup_date(partner_id=partner.get('id'))
            print(result, partner.get('id'), partner.get('name'))
        else:
            print(f"SKIP | USER: {partner.get('name')} WAS MESSAGED BEFORE")
            self.auto.update_partner_followup_date(partner_id=partner.get('id'),
                                              set_datetime=result.get('last_msg_time'))


if __name__ == '__main__':
    a = Auto()
    a.main()
    print(a.tg)
