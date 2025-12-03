from services.google_sheets import get_data, add_row
from core.constants import TABLE_ACTIVITY_LOG
from utils.id_generator import generate_uuid
from datetime import datetime
import streamlit as st

class ActivityLogModel:
    def __init__(self, log_id, user_id, action, target_id, target_type, details, time):
        self.log_id = log_id
        self.user_id = user_id
        self.action = action
        self.target_id = target_id
        self.target_type = target_type
        self.details = details
        self.time = time

    @staticmethod
    def log_action(user_id, action, target_id="", target_type="", details=""):
        """
        تسجيل حدث جديد في النظام
        مثال: log_action(user.id, "delete", "section_123", "section", "قام بحذف القسم العام")
        """
        try:
            log_id = generate_uuid()
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # الترتيب حسب ملف CSV: log_id, user_id, action, target_id, target_type, details, time
            new_row = [log_id, user_id, action, target_id, target_type, details, time_now]
            
            # عملية التسجيل يجب ألا توقف النظام إذا فشلت (Fire and Forget)
            add_row(TABLE_ACTIVITY_LOG, new_row)
        except Exception as e:
            print(f"Failed to log action: {e}")

    @staticmethod
    def get_all_logs():
        """جلب جميع السجلات للعرض"""
        df = get_data(TABLE_ACTIVITY_LOG)
        logs = []
        if not df.empty:
            # ترتيب عكسي (الأحدث أولاً)
            # df = df.sort_values(by='time', ascending=False)
            
            for _, row in df.iterrows():
                logs.append(ActivityLogModel(
                    log_id=row['log_id'],
                    user_id=row['user_id'],
                    action=row['action'],
                    target_id=row['target_id'],
                    target_type=row['target_type'],
                    details=row['details'],
                    time=row['time']
                ))
        return logs
