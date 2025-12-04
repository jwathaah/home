import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import time
from gspread.exceptions import APIError

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=600)
def get_connection():
    """إنشاء اتصال آمن مع Google Sheets"""
    try:
        # التأكد من وجود القسم الرئيسي
        if "google" not in st.secrets:
            st.error("❌ ملف secrets.toml لا يحتوي على القسم [google]")
            return None

        # جلب البيانات
        creds_data = st.secrets["google"].get("service_account_json")
        
        if not creds_data:
             st.error("❌ لم يتم العثور على 'service_account_json' داخل الأسرار")
             return None

        # معالجة البيانات (تحويل النص إلى JSON إذا لزم الأمر)
        if isinstance(creds_data, str):
            try:
                creds_dict = json.loads(creds_data)
            except json.JSONDecodeError as e:
                st.error(f"❌ خطأ في تنسيق JSON في ملف الأسرار: {e}")
                return None
        else:
            creds_dict = creds_data

        # التأكد من وجود المفتاح الخاص قبل الاتصال
        if "private_key" not in creds_dict:
            st.error("❌ البيانات موجودة لكن حقل 'private_key' مفقود!")
            return None

        # إنشاء الاتصال
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client

    except Exception as e:
        st.error(f"❌ خطأ غير متوقع في الاتصال: {e}")
        return None

# دالة إعادة المحاولة (مهمة لتجنب الحظر المؤقت من جوجل)
def _execute_with_retry(func, *args, **kwargs):
    max_retries = 3
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429:
                time.sleep((i + 1) * 2)
                continue
            else:
                st.error(f"❌ Google API Error: {e}")
                return None
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None
    return None

def get_data(sheet_name):
    client = get_connection()
    if not client: return pd.DataFrame()
    
    def _fetch():
        # استخدام المعرف من الأسرار مباشرة
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())

    result = _execute_with_retry(_fetch)
    return result if result is not None else pd.DataFrame()

def add_row(sheet_name, row_data_list):
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
