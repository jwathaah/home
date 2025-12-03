import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# الصلاحيات المطلوبة للوصول للدرايف
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """إنشاء اتصال مع Google Drive API"""
    try:
        if "google" in st.secrets and "service_account_json" in st.secrets["google"]:
            # التعامل مع التنسيق (سواء كان TOML object أو String)
            creds_data = st.secrets["google"]["service_account_json"]
            import json
            if isinstance(creds_data, str):
                creds_dict = json.loads(creds_data)
            else:
                creds_dict = creds_data

            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            return service
        return None
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Drive: {e}")
        return None

def upload_file_to_drive(file_obj, filename, mime_type):
    """
    رفع ملف إلى مجلد محدد في Google Drive
    """
    service = get_drive_service()
    if not service:
        return None, None

    try:
        folder_id = st.secrets["google"]["drive_folder_id"]
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
        
        # --- التعديل الهام هنا ---
        # نضيف supportsAllDrives=True للسماح بالرفع للمجلدات المشتركة
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink',
            supportsAllDrives=True  # <--- هذا هو الحل السحري
        ).execute()
        
        # جعل الملف "عام" (Public)
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            service.permissions().create(
                fileId=file.get('id'),
                body=permission,
                supportsAllDrives=True # <--- ومهمة هنا أيضاً
            ).execute()
        except Exception as p_err:
            print(f"Warning setting permissions: {p_err}")

        # إرجاع المعرف والرابط
        # webContentLink للتحميل المباشر، webViewLink للمعاينة
        # الصور تحتاج أحياناً معالجة خاصة في Streamlit، سنرجع رابط المعاينة
        return file.get('id'), file.get('webViewLink')

    except Exception as e:
        # طباعة الخطأ بتفصيل أكبر
        st.error(f"❌ فشل رفع الملف: {e}")
        return None, None
