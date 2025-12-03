import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import time
from gspread.exceptions import APIError

# 1. إعداد الاتصال
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- التحسين الأول: تخزين الاتصال في الذاكرة (Cache) ---
# هذا يمنع تسجيل الدخول المتكرر مع كل ضغطة زر
@st.cache_resource(ttl=600)
def get_connection():
    """إنشاء اتصال آمن مع Google Sheets مع التخزين المؤقت"""
    try:
        if "google" in st.secrets and "service_account_json" in st.secrets["google"]:
            creds_data = st.secrets["google"]["service_account_json"]
            
            if isinstance(creds_data, str):
                try:
                    creds_dict = json.loads(creds_data)
                except json.JSONDecodeError:
                    creds_dict = creds_data
            else:
                creds_dict = creds_data

            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client
        return None
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        return None

# --- التحسين الثاني: دالة ذكية لإعادة المحاولة عند الفشل ---
def _execute_with_retry(func, *args, **kwargs):
    """دالة مساعدة تعيد المحاولة عند حدوث خطأ 429 (Quota exceeded)"""
    max_retries = 3
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429:
                # إذا كان الخطأ بسبب الضغط الزائد، انتظر قليلاً وتزايد الوقت
                wait_time = (i + 1) * 2  # 2s, 4s, 6s
                time.sleep(wait_time)
                continue
            else:
                # إذا كان خطأ آخر، أوقفه
                st.error(f"❌ Google API Error: {e}")
                return None
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None
    st.error("❌ فشل الاتصال بعد عدة محاولات (تجاوزت الحد المسموح). حاول بعد دقيقة.")
    return None

# 2. دالة جلب البيانات (للعرض)
def get_data(sheet_name):
    """جلب البيانات كـ DataFrame"""
    client = get_connection()
    if not client: return pd.DataFrame()
    
    def _fetch():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        return pd.DataFrame(ws.get_all_records())

    result = _execute_with_retry(_fetch)
    return result if result is not None else pd.DataFrame()

# 3. دالة الإضافة (Create)
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

# 4. دالة الحذف (Delete)
def delete_row(sheet_name, id_column, id_value):
    """حذف صف بناءً على قيمة المعرف"""
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
    if result is None: return False
    if result is False: st.warning("⚠️ العنصر غير موجود.")
    return result

# 5. دالة التعديل (Update)
def update_field(sheet_name, id_column, id_value, target_column, new_value):
    """تحديث قيمة خلية واحدة"""
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
