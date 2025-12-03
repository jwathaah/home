import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# تحديد الصلاحيات المطلوبة (Scopes)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_connection():
    """
    دالة لإنشاء اتصال آمن مع Google Sheets باستخدام الأسرار المخزنة
    """
    try:
        # قراءة بيانات الاعتماد من ملف secrets.toml
        # st.secrets converts the TOML section to a dictionary
        credentials_info = st.secrets["google"]["service_account_json"]
        
        creds = Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Cloud: {e}")
        return None

def get_sheet_data(sheet_name):
    """
    قراءة البيانات من ورقة محددة وإرجاعها كـ DataFrame
    """
    client = get_connection()
    if not client:
        return pd.DataFrame()
    
    try:
        spreadsheet_id = st.secrets["google"]["spreadsheet_id"]
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        # جلب كل البيانات
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"⚠️ الورقة '{sheet_name}' غير موجودة.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة {sheet_name}: {e}")
        return pd.DataFrame()

def add_row(sheet_name, row_data):
    """
    إضافة صف جديد إلى ورقة محددة
    row_data: يجب أن يكون قائمة (List) بالقيم، مثال: ['user1', 'login', 'success']
    """
    client = get_connection()
    if not client:
        return False
        
    try:
        spreadsheet_id = st.secrets["google"]["spreadsheet_id"]
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        # إضافة وقت الإنشاء تلقائيًا إذا لم يكن موجودًا (اختياري)
        # worksheet.append_row(row_data) 
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ فشل في إضافة البيانات لـ {sheet_name}: {e}")
        return False
