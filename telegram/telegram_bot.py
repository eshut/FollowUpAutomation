from telethon import TelegramClient
from telethon.errors import FloodWaitError
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging
import asyncio
import re

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
    
    @staticmethod
    def parse_telegram_identifier(identifier):
        identifier = str(identifier).strip()
        
        if identifier.startswith('https://web.telegram.org/'):
            match = re.search(r'#(-?\d+)', identifier)
            if match:
                return int(match.group(1))
        
        if identifier.startswith('https://t.me/') or identifier.startswith('t.me/'):
            identifier = identifier.replace('https://t.me/', '')
            identifier = identifier.replace('t.me/', '')
            identifier = identifier.split('?')[0]
            identifier = identifier.lstrip('@')
            return identifier
        
        if identifier.startswith('-') or identifier.isdigit():
            return int(identifier)
        
        return identifier.lstrip('@')
    
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
                
                code = input("Enter the code you received in Telegram: ")
                
                try:
                    await self.client.sign_in(self.phone, code)
                    logger.info("Successfully signed in!")
                except Exception as e:
                    if "Two-steps verification" in str(e) or "password" in str(e).lower():
                        logger.info("2FA is enabled. Password required.")
                        password = input("Enter your 2FA password: ")
                        try:
                            await self.client.sign_in(password=password)
                            logger.info("Successfully signed in with 2FA!")
                        except Exception as pwd_error:
                            logger.error(f"Failed to sign in with password: {pwd_error}")
                            return False
                    else:
                        logger.error(f"Failed to sign in: {e}")
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
    
    async def send_message(self, username, message: str) -> bool:
        if not self.client:
            logger.error("Client not connected")
            return False
        
        identifier = self.parse_telegram_identifier(username)
        
        try:
            entity = await self.client.get_entity(identifier)
            await self.client.send_message(entity, message)
            logger.info(f"Message sent to {identifier}")
            return True
            
        except FloodWaitError as e:
            logger.error(f"Flood wait error. Need to wait {e.seconds} seconds")
            return False
        except Exception as e:
            logger.error(f"Error sending message to {identifier}: {e}")
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
    
    async def check_user_exists(self, username) -> bool:
        if not self.client:
            logger.error("Client not connected")
            return False
        
        identifier = self.parse_telegram_identifier(username)
        
        try:
            await self.client.get_entity(identifier)
            return True
        except Exception as e:
            logger.error(f"User {identifier} not found: {e}")
            return False
    
    async def get_chat_messages(self, username, limit: int = 10) -> List[Dict]:
        if not self.client:
            logger.error("Client not connected")
            return []
        
        identifier = self.parse_telegram_identifier(username)
        
        try:
            entity = await self.client.get_entity(identifier)
            messages = await self.client.get_messages(entity, limit=limit)
            
            result = []
            for msg in messages:
                result.append({
                    'id': msg.id,
                    'text': msg.text,
                    'date': msg.date,
                    'out': msg.out,
                    'from_id': msg.from_id
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting messages from {identifier}: {e}")
            return []
    
    async def get_last_outgoing_message_time(self, username):
        if not self.client:
            logger.error("Client not connected")
            return None
        
        identifier = self.parse_telegram_identifier(username)
        
        try:
            entity = await self.client.get_entity(identifier)
            messages = await self.client.get_messages(entity, limit=50)
            
            for msg in messages:
                if msg.out:
                    return msg.date
            
            return None
        except Exception as e:
            logger.error(f"Error getting last message time from {identifier}: {e}")
            return None


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
    
    @staticmethod
    async def send_single_message_async(user_id, message: str) -> bool:
        messenger = TelegramMessenger()
        
        try:
            connected = await messenger.connect()
            if not connected:
                logger.error("Failed to connect to Telegram")
                return False
            
            success = await messenger.send_message(user_id, message)
            return success
            
        finally:
            await messenger.disconnect()
    
    @staticmethod
    def send_single_message(user_id, message: str) -> bool:
        return asyncio.run(TelegramService.send_single_message_async(user_id, message))
    
    @staticmethod
    async def get_chat_messages_async(user_id, limit: int = 10) -> List[Dict]:
        messenger = TelegramMessenger()
        
        try:
            connected = await messenger.connect()
            if not connected:
                logger.error("Failed to connect to Telegram")
                return []
            
            messages = await messenger.get_chat_messages(user_id, limit)
            return messages
            
        finally:
            await messenger.disconnect()
    
    @staticmethod
    def get_chat_messages(user_id, limit: int = 10) -> List[Dict]:
        return asyncio.run(TelegramService.get_chat_messages_async(user_id, limit))
    
    @staticmethod
    async def send_message_with_time_check_async(
        user_id,
        message: str,
        min_seconds: int = 60
    ) -> Dict[str, any]:
        messenger = TelegramMessenger()
        
        try:
            connected = await messenger.connect()
            if not connected:
                logger.error("Failed to connect to Telegram")
                return {'sent': False, 'reason': 'connection_failed'}
            
            last_msg_time = await messenger.get_last_outgoing_message_time(user_id)
            
            if last_msg_time:
                now = datetime.now(timezone.utc)
                time_diff = (now - last_msg_time).total_seconds()
                
                if time_diff < min_seconds:
                    logger.info(f"Skipping message to {user_id}. Last message sent {time_diff:.0f} seconds ago")
                    return {
                        'sent': False,
                        'reason': 'too_soon',
                        'seconds_since_last': time_diff,
                        'min_required': min_seconds,
                        'last_msg_time': last_msg_time
                    }
            
            success = await messenger.send_message(user_id, message)
            
            return {
                'sent': success,
                'reason': 'sent' if success else 'send_failed',
                'last_msg_time': datetime.now(timezone.utc) if success else None
            }
            
        finally:
            await messenger.disconnect()
    
    @staticmethod
    def send_message_with_time_check(
        user_id,
        message: str,
        min_seconds: int = 60
    ) -> Dict[str, any]:
        return asyncio.run(TelegramService.send_message_with_time_check_async(user_id, message, min_seconds))


