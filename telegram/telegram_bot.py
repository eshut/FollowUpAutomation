from telethon import TelegramClient
from telethon.errors import FloodWaitError
from typing import Optional, List, Dict
import logging
import asyncio

from config import Config, DEFAULT_MESSAGE_TEMPLATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramMessenger:
    def __init__(self):
        config = Config().telegram
        self.api_id = config.api_id
        self.api_hash = config.api_hash
        self.phone = config.phone
        self.session_name = config.session_name
        self.client = None
    
    async def connect(self) -> bool:
        try:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.info("Not authorized. Attempting to sign in...")
                await self.client.send_code_request(self.phone)
                logger.info("Code sent to your Telegram app. Please check and enter it.")
                return False
            
            logger.info("Successfully connected to Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Telegram: {e}")
            return False
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram")
    
    async def send_message(self, username: str, message: str) -> bool:
        if not self.client:
            logger.error("Client not connected")
            return False
        
        username = username.lstrip('@')
        
        try:
            entity = await self.client.get_entity(username)
            await self.client.send_message(entity, message)
            logger.info(f"Message sent to @{username}")
            return True
            
        except FloodWaitError as e:
            logger.error(f"Flood wait error. Need to wait {e.seconds} seconds")
            return False
        except Exception as e:
            logger.error(f"Error sending message to @{username}: {e}")
            return False
    
    async def send_message_to_partners(
        self,
        partners: List[Dict],
        message_template: Optional[str] = None,
        delay_seconds: int = 2
    ) -> Dict[str, int]:
        if not self.client:
            logger.error("Client not connected")
            return {'success': 0, 'failed': 0}
        
        message = message_template or DEFAULT_MESSAGE_TEMPLATE
        results = {'success': 0, 'failed': 0}
        
        for partner in partners:
            telegram_tag = partner.get('telegram_tag')
            name = partner.get('name', 'Unknown')
            
            if not telegram_tag:
                logger.warning(f"Partner {name} has no telegram tag, skipping")
                results['failed'] += 1
                continue
            
            personalized_message = message.replace('{name}', name)
            
            success = await self.send_message(telegram_tag, personalized_message)
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        logger.info(
            f"Messaging complete. Success: {results['success']}, "
            f"Failed: {results['failed']}"
        )
        return results
    
    async def check_user_exists(self, username: str) -> bool:
        if not self.client:
            logger.error("Client not connected")
            return False
        
        username = username.lstrip('@')
        
        try:
            await self.client.get_entity(username)
            return True
        except Exception as e:
            logger.error(f"User @{username} not found: {e}")
            return False


class TelegramService:
    @staticmethod
    async def send_messages(
        partners: List[Dict],
        message: Optional[str] = None,
        delay: int = 2
    ) -> Dict[str, int]:
        messenger = TelegramMessenger()
        
        try:
            connected = await messenger.connect()
            if not connected:
                logger.error("Failed to connect to Telegram")
                return {'success': 0, 'failed': len(partners)}
            
            results = await messenger.send_message_to_partners(
                partners,
                message,
                delay
            )
            
            return results
            
        finally:
            await messenger.disconnect()
    
    @staticmethod
    def send_messages_sync(
        partners: List[Dict],
        message: Optional[str] = None,
        delay: int = 2
    ) -> Dict[str, int]:
        return asyncio.run(TelegramService.send_messages(partners, message, delay))

