from services.google_sheets import get_data, add_row, delete_row
from core.constants import TABLE_SESSIONS
from utils.id_generator import generate_uuid
from datetime import datetime, timedelta

class SessionModel:
    def __init__(self, session_id, user_id, created_at):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at

    @staticmethod
    def create_session(user_id):
        """إنشاء جلسة جديدة وحفظها"""
        session_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # الترتيب: session_id, user_id, created_at
        add_row(TABLE_SESSIONS, [session_id, user_id, created_at])
        return session_id

    @staticmethod
    def get_user_id_by_session(session_id):
        """البحث عن المستخدم من خلال رمز الجلسة"""
        df = get_data(TABLE_SESSIONS)
        if not df.empty:
            # البحث عن السطر الذي يحتوي على session_id
            row = df[df['session_id'] == str(session_id)]
            if not row.empty:
                return row.iloc[0]['user_id']
        return None

    @staticmethod
    def delete_session(session_id):
        """حذف الجلسة عند تسجيل الخروج"""
        return delete_row(TABLE_SESSIONS, "session_id", session_id)
