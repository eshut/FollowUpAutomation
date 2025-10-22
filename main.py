import argparse
import sys
import logging

from commands import CommandFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self):
        parser = argparse.ArgumentParser(
            description='Follow Up Automation - Manage partners and automate Telegram messaging'
        )
        
        parser.add_argument(
            'action',
            choices=['list', 'list-telegram', 'send'],
            help='Action to perform: list (all partners), list-telegram (partners with Telegram), send (send messages)'
        )
        
        parser.add_argument(
            '--message',
            type=str,
            help='Custom message to send (use {name} as placeholder for partner name)'
        )
        
        parser.add_argument(
            '--tag',
            type=str,
            help='Filter by specific Telegram tag'
        )
        
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='Delay between messages in seconds (default: 2)'
        )
        
        return parser
    
    def run(self):
        args = self.parser.parse_args()
        
        logger.info(f"Executing action: {args.action}")
        
        command = CommandFactory.create(
            args.action,
            message=args.message,
            tag=args.tag,
            delay=args.delay
        )
        
        if command:
            command.execute()
        else:
            logger.error(f"Unknown action: {args.action}")
            sys.exit(1)


def main():
    try:
        app = Application()
        app.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
