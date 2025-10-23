from config import PARTNERS_TABLE


class PartnerQueries:
    @staticmethod
    def get_all_partners():
        return f"""
            SELECT id, name, priopity, 
                   COALESCE("lastFollowUp", "createdAt"::date) as "lastFollowUp",
                   "createdAt",
                   status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_by_tag():
        return f"""
            SELECT id, name, priopity,
                   COALESCE("lastFollowUp", "createdAt"::date) as "lastFollowUp",
                   "createdAt",
                   status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE "telegramLinkPrimaryLinkUrl" = %s
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_with_telegram():
        return f"""
            SELECT id, name, priopity,
                   COALESCE("lastFollowUp", "createdAt"::date) as "lastFollowUp",
                   "createdAt",
                   status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE "telegramLinkPrimaryLinkUrl" IS NOT NULL AND "telegramLinkPrimaryLinkUrl" != ''
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_needing_followup():
        return f"""
            SELECT id, name, priopity, "lastFollowUp", status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE "lastFollowUp" < CURRENT_DATE - INTERVAL '30 days'
            ORDER BY "lastFollowUp" ASC
        """
    
    @staticmethod
    def get_partners_by_status():
        return f"""
            SELECT id, name, priopity, "lastFollowUp", status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE status = %s
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_by_priority():
        return f"""
            SELECT id, name, priopity, "lastFollowUp", status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE priopity = %s
            ORDER BY name
        """
    
    @staticmethod
    def get_partners_filtered(status=None, priority=None, days_since_followup=30):
        conditions = []
        
        if status:
            conditions.append("status = %(status)s")
        
        if priority:
            conditions.append("priopity = %(priority)s")
        
        if days_since_followup:
            conditions.append('"lastFollowUp" < CURRENT_DATE - INTERVAL \'%(days)s days\'')
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        return f"""
            SELECT id, name, priopity, "lastFollowUp", status, "telegramLinkPrimaryLinkUrl", "upworkLinkPrimaryLinkUrl"
            FROM {PARTNERS_TABLE}
            WHERE {where_clause}
            ORDER BY "lastFollowUp" ASC
        """
    
    @staticmethod
    def update_last_followup():
        return f"""
            UPDATE {PARTNERS_TABLE}
            SET "lastFollowUp" = CURRENT_DATE
            WHERE id = %s
        """
    
    @staticmethod
    def update_last_followup_with_date():
        return f"""
            UPDATE {PARTNERS_TABLE}
            SET "lastFollowUp" = %s
            WHERE id = %s
        """
