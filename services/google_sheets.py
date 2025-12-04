import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import time
from gspread.exceptions import APIError

# 1. إعدادات النطاق (Permissions)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 2. دالة الاتصال (محسنة لقراءة الأسرار بدقة)
@st.cache_resource(ttl=600)
def get_connection():
    """إنشاء اتصال آمن مع Google Sheets"""
    try:
        # أ. التأكد من وجود قسم google في الأسرار
        if "google" not in st.secrets:
            st.error("❌ ملف secrets.toml لا يحتوي على القسم [google]")
            return None

        # ب. جلب بيانات المفتاح (service_account_json)
        # نستخدم .get لتجنب توقف البرنامج إذا لم يوجد المفتاح
        creds_data = st.secrets["google"].get("service_account_json")
        
        if not creds_data:
             st.error("❌ لم يتم العثور على 'service_account_json' داخل الأسرار. تأكد من إضافته.")
             return None

        # ج. معالجة البيانات (تحويل النص إلى قاموس JSON)
        # هذا الجزء يحل مشكلة "No key could be detected"
        if isinstance(creds_data, str):
            try:
                creds_dict = json.loads(creds_data)
            except json.JSONDecodeError as e:
                st.error(f"❌ خطأ في تنسيق JSON في ملف الأسرار (تأكد من الأقواس والفواصل): {e}")
                return None
        else:
            # في حال كان Streamlit قد حوله تلقائياً
            creds_dict = creds_data

        # د. التأكد من أن المفتاح يحتوي على البيانات المطلوبة
        if "private_key" not in creds_dict or "client_email" not in creds_dict:
            st.error("❌ بيانات الاعتماد ناقصة! تأكد أن service_account_json يحتوي على private_key و client_email.")
            return None

        # هـ. إنشاء الاتصال الفعلي
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client

    except Exception as e:
        st.error(f"❌ حدث خطأ غير متوقع أثناء الاتصال بجوجل: {e}")
        return None

# 3. دالة ذكية لإعادة المحاولة (Retry Logic) لتجنب انقطاع الاتصال
def _execute_with_retry(func, *args, **kwargs):
    max_retries = 3
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429: # خطأ تجاوز الحد المسموح (Quota)
                time.sleep((i + 1) * 2)
                continue
            else:
                st.error(f"❌ Google API Error: {e}")
                return None
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None
    return None

# ==========================================
# دوال التعامل مع البيانات (CRUD Operations)
# ==========================================

def get_data(sheet_name):
    """جلب البيانات من ورقة محددة"""
    client = get_connection()
    if not client: return pd.DataFrame()
    
    def _fetch():
        # التأكد من وجود spreadsheet_id
        if "spreadsheet_id" not in st.secrets["google"]:
            st.error("❌ لم يتم العثور على spreadsheet_id في الأسرار")
            return []
            
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())

    result = _execute_with_retry(_fetch)
    return result if result is not None else pd.DataFrame()

def add_row(sheet_name, row_data_list):
    """إضافة صف جديد"""
    client = get_connection()
    if not client: return False
    
    def _add():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        ws.append_row(row_data_list)
        return True

    result = _execute_with_retry(_add)
    return result if result is True else False

def delete_row(sheet_name, id_column, id_value):
    """حذف صف بناءً على قيمة عمود محدد"""
    client = get_connection()
    if not client: return False
    
    def _delete():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if cell:
            ws.delete_rows(cell.row)
            return True
        return False

    result = _execute_with_retry(_delete)
    return result if result is True else False

def update_field(sheet_name, id_column, id_value, target_column, new_value):
    """تحديث خلية محددة"""
    client = get_connection()
    if not client: return False
    
    def _update():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if not cell: return False
        
        headers = ws.row_values(1)
        try:
            col_index = headers.index(target_column) + 1
        except ValueError:
            return False
            
        ws.update_cell(cell.row, col_index, new_value)
        return True

    result = _execute_with_retry(_update)
    return result if result is True else False
