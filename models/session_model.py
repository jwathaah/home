from services.google_sheets import get_data, add_row, delete_row
from core.constants import TABLE_SESSIONS
from utils.id_generator import generate_uuid
from datetime import datetime, timedelta

class SessionModel:
    # الأعمدة: session_id, user_id, token, created_at, last_activity, expires_at
    
    @staticmethod
    def create_session(user_id):
        """إنشاء جلسة ببيانات كاملة"""
        session_id = generate_uuid()
        token = generate_uuid() # توكن خاص للكوكيز (أكثر أماناً)
        
        now = datetime.now()
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        last_activity = created_at
        # تحديد تاريخ انتهاء الصلاحية (بعد 30 يوم)
        expires_at = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        
        # ترتيب البيانات حسب ملف الإكسل بالضبط
        row = [session_id, user_id, token, created_at, last_activity, expires_at]
        
        add_row(TABLE_SESSIONS, row)
        return token # نرجع التوكن لنخزنه في المتصفح

    @staticmethod
    def get_user_id_by_token(token):
        """البحث عن المستخدم باستخدام التوكن"""
        df = get_data(TABLE_SESSIONS)
        if not df.empty:
            # البحث عن الصف الذي يحتوي على هذا التوكن
            row = df[df['token'] == str(token)]
            if not row.empty:
                # تحقق إضافي: هل انتهت صلاحية الجلسة؟
                expires_str = row.iloc[0]['expires_at']
                try:
                    expires_date = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() > expires_date:
                        return None # انتهت الصلاحية
                except:
                    pass # تجاهل خطأ التاريخ للمرونة

                return row.iloc[0]['user_id']
        return None

    @staticmethod
    def delete_session(token):
        """حذف الجلسة (تسجيل خروج) باستخدام التوكن"""
        # نفترض أن العمود الثالث هو token، لكن دالة الحذف تبحث باسم العمود
        # تأكد أن اسم العمود في الشيت هو 'token'
        return delete_row(TABLE_SESSIONS, "token", token)
