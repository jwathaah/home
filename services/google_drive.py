import streamlit as st
from google.cloud import storage
from google.oauth2 import service_account
import json
import datetime

# إعداد الاتصال بـ Cloud Storage
def get_storage_client():
    try:
        if "google" in st.secrets and "service_account" in st.secrets["google"]:
            creds_dict = dict(st.secrets["google"]["service_account"])
            
            # إصلاح مفتاح التشفير (مشكلة المسافات)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            client = storage.Client(credentials=credentials, project=creds_dict.get("project_id"))
            return client
        return None
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Cloud Storage: {e}")
        return None

def upload_file_to_drive(file_obj, filename, mime_type):
    """
    رفع ملف إلى Google Cloud Storage وإرجاع رابط عام.
    """
    client = get_storage_client()
    if not client:
        return None, None

    try:
        bucket_name = st.secrets["google"].get("bucket_name")
        if not bucket_name:
            st.error("⚠️ لم يتم تحديد اسم Bucket في الأسرار!")
            return None, None

        bucket = client.bucket(bucket_name)
        
        # إضافة طابع زمن لاسم الملف لمنع التكرار
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        
        blob = bucket.blob(safe_filename)
        
        # رفع الملف
        file_obj.seek(0)
        blob.upload_from_file(file_obj, content_type=mime_type)
        
        # الرابط العام
        # https://storage.googleapis.com/BUCKET_NAME/FILENAME
        public_url = f"https://storage.googleapis.com/{bucket_name}/{safe_filename}"
        
        return safe_filename, public_url

    except Exception as e:
        st.error(f"❌ فشل الرفع: {e}")
        return None, None
