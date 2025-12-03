import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# إعداد الاتصال
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    creds_dict = st.secrets["google"]["service_account_json"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet_id = st.secrets["google"]["spreadsheet_id"]
    
    print("⏳ جاري محاولة الاتصال...")
    sh = client.open_by_key(sheet_id)
    print(f"✅ تم الاتصال بنجاح بملف: {sh.title}")
    
    # محاولة قراءة أول صف من جدول الأدوار roles
    worksheet = sh.worksheet("roles")
    data = worksheet.get_all_records()
    print(f"📊 نجحنا في قراءة جدول الأدوار، عدد الأدوار الموجودة: {len(data)}")
    if len(data) > 0:
        print(f"   مثال: {data[0]}")
    else:
        print("⚠️ الجدول فارغ، لكن الاتصال سليم.")

except Exception as e:
    print(f"❌ حدث خطأ في الاتصال: {e}")
