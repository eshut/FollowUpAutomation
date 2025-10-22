from config import PARTNERS_TABLE


class PartnerQueries:
    @staticmethod
    def get_all_partners():
        return f"""
            SELECT id, name, link, telegram_tag, last_contacted, notes
            FROM {PARTNERS_TABLE}
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_by_tag():
        return f"""
            SELECT id, name, link, telegram_tag, last_contacted, notes
            FROM {PARTNERS_TABLE}
            WHERE telegram_tag = %s
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_with_telegram():
        return f"""
            SELECT id, name, link, telegram_tag, last_contacted, notes
            FROM {PARTNERS_TABLE}
            WHERE telegram_tag IS NOT NULL AND telegram_tag != ''
            ORDER BY name
        """
    
    @staticmethod
    def update_last_contacted():
        return f"""
            UPDATE {PARTNERS_TABLE}
            SET last_contacted = NOW()
            WHERE id = %s
        """

