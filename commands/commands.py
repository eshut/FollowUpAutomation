import sys
import logging
from typing import Optional

from database import DatabaseManager, PartnerPrinter, PartnerFilter
from telegram import TelegramService

logger = logging.getLogger(__name__)


class PartnerListCommand:
    def __init__(self):
        self.db = DatabaseManager()
        self.printer = PartnerPrinter()
        self.partner_filter = PartnerFilter()
    
    def execute(self):
        try:
            with self.db:
                partners = self.db.get_all_partners()
                partners = self.partner_filter.filter_partners(
                    partners,
                    days_since_followup=30
                                                    )
                print(len(partners))
            return partners
        except Exception as e:
            logger.error(f"Error listing partners: {e}")
            sys.exit(1)


class PartnerListTelegramCommand:
    def __init__(self):
        self.db = DatabaseManager()
        self.printer = PartnerPrinter()
    
    def execute(self):
        try:
            with self.db:
                partners = self.db.get_partners_with_telegram()
                self.printer.print(partners)
        except Exception as e:
            logger.error(f"Error listing partners with Telegram: {e}")
            sys.exit(1)


class SendMessagesCommand:
    def __init__(
        self,
        message: Optional[str] = None,
        telegram_tag: Optional[str] = None,
        delay: int = 2
    ):
        self.db = DatabaseManager()
        self.telegram_service = TelegramService()
        self.message = message
        self.telegram_tag = telegram_tag
        self.delay = delay
    
    def execute(self):
        try:
            with self.db:
                partners = self._get_partners()
                
                if not partners:
                    logger.warning("No partners found to message")
                    return
                
                if not self._confirm_sending(partners):
                    print("Operation cancelled.")
                    return
                
                results = self.telegram_service.send_messages_sync(
                    partners,
                    self.message,
                    self.delay
                )
                
                self._display_results(results)
                self._update_contacts(partners)
        
        except Exception as e:
            logger.error(f"Error sending Telegram messages: {e}")
            sys.exit(1)
    
    def _get_partners(self):
        if self.telegram_tag:
            logger.info(f"Sending messages to partners with tag: {self.telegram_tag}")
            return self.db.get_partners_by_telegram_tag(self.telegram_tag)
        else:
            logger.info("Sending messages to all partners with Telegram tags")
            return self.db.get_partners_with_telegram()
    
    def _confirm_sending(self, partners):
        print(f"\nPreparing to message {len(partners)} partner(s)...")
        for partner in partners:
            print(f"  - {partner['name']} (@{partner['telegram_tag']})")
        
        response = input("\nDo you want to proceed? (yes/no): ")
        return response.lower() in ['yes', 'y']
    
    def _display_results(self, results):
        print(f"\nMessaging completed!")
        print(f"Successfully sent: {results['success']}")
        print(f"Failed: {results['failed']}")
    
    def _update_contacts(self, partners):
        for partner in partners:
            self.db.update_last_contacted(partner['id'])


class CommandFactory:
    @staticmethod
    def create(action: str, **kwargs):
        commands = {
            'list': PartnerListCommand,
            'list-telegram': PartnerListTelegramCommand,
            'send': lambda: SendMessagesCommand(
                message=kwargs.get('message'),
                telegram_tag=kwargs.get('tag'),
                delay=kwargs.get('delay', 2)
            )
        }
        
        command_class = commands.get(action)
        if callable(command_class):
            return command_class() if action != 'send' else command_class()
        return None

