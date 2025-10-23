import os
import uuid

from framework_inject.logger.logger import Logger


class DataUtil(Logger):
    def __init__(self, logger=__file__):
        super().__init__(logger)

    def generate_uuid(self):
        """
        Generates a dynamic session ID with the required format.

        Returns:
            str: Formatted session ID string.
        """
        session = str(uuid.uuid4())
        return session

    @staticmethod
    def count_words(string):
        if string is None:
            return 0
        words = string.split()  # Splits string by whitespace
        return len(words)

    @staticmethod
    def get_first_n_words(text, n=15):
        if text is None:
            return None
        words = text.split()
        return ' '.join(words[:n])

    def check_for_required_fields(self, required_fields):
        missing_fields = []
        for field in required_fields:
            if not os.getenv(field):
                missing_fields.append(field)

        if missing_fields:
            self.logger.error("PLEASE COPY VARIABLES FROM .env.example TO .env FILE")
            self.logger.error("The following required fields are missing or empty in the .env file:")
            for field in missing_fields:
                self.logger.error(f"- {field}")
            exit(1)  # Exit with error code
        else:
            self.logger.info("All required fields are provided.")

    @staticmethod
    def parse_number(s: str) -> float:
        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000,
            'T': 1_000_000_000_000,
        }
        if s[-1].upper() in multipliers:
            return float(s[:-1]) * multipliers[s[-1].upper()]
        return float(s)
