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
        if "google" not in st.secrets:
            st.error("❌ ملف secrets.toml لا يحتوي على القسم [google]")
            return None

        # 1. محاولة قراءة البيانات بالتنسيق الجديد (Table)
        if "service_account" in st.secrets["google"]:
            # نحول كائن Streamlit Secrets إلى قاموس بايثون عادي لتعديله
            creds_dict = dict(st.secrets["google"]["service_account"])
        
        # 2. دعم التنسيق القديم (JSON String) كاحتياط
        elif "service_account_json" in st.secrets["google"]:
            creds_data = st.secrets["google"]["service_account_json"]
            if isinstance(creds_data, str):
                try:
                    creds_dict = json.loads(creds_data)
                except json.JSONDecodeError as e:
                    st.error(f"❌ خطأ JSON: {e}")
                    return None
            else:
                creds_dict = creds_data
        else:
             st.error("❌ لم يتم العثور على بيانات الاعتماد (service_account) في الأسرار")
             return None

        # 3. إصلاح مفتاح التشفير (الحل السحري لمشكلة No key detected)
        # بعض الأحيان يتم قراءة \n كنص عادي بدلاً من سطر جديد، هنا نقوم بإصلاحه
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        # إنشاء الاتصال
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client

    except Exception as e:
        st.error(f"❌ خطأ غير متوقع في الاتصال: {e}")
        return None

# --- دوال المساعدة (Retry Logic) ---
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

# --- دوال التعامل مع البيانات ---

def get_data(sheet_name):
    client = get_connection()
    if not client: return pd.DataFrame()
    
    def _fetch():
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
