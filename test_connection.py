import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🕵️ فحص الاتصال بقاعدة البيانات")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

try:
    # جلب الأسرار
    creds_dict = st.secrets["google"]["service_account_json"]
    sheet_id = st.secrets["google"]["spreadsheet_id"]
    
    # محاولة الاتصال
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    st.info("⏳ جاري الاتصال بجوجل...")
    sh = client.open_by_key(sheet_id)
    
    st.success(f"✅ تم الاتصال بنجاح! اسم الملف: {sh.title}")
    
    # قراءة جدول roles
    worksheet = sh.worksheet("roles")
    data = worksheet.get_all_records()
    
    st.write("---")
    st.subheader("📊 البيانات الموجودة في جدول الأدوار (Roles):")
    st.dataframe(data)

except Exception as e:
    st.error("❌ حدث خطأ في الاتصال!")
    st.error(e)
