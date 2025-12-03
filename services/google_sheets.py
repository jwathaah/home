import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. إعداد الاتصال
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_connection():
    """إنشاء اتصال آمن مع Google Sheets"""
    try:
        if "google" in st.secrets and "service_account_json" in st.secrets["google"]:
            creds_dict = st.secrets["google"]["service_account_json"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client
        return None
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        return None

# 2. دالة جلب البيانات (للعرض)
def get_data(sheet_name):
    """جلب البيانات كـ DataFrame"""
    client = get_connection()
    if not client: return pd.DataFrame()
    try:
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        # st.error(f"خطأ في قراءة {sheet_name}: {e}")
        return pd.DataFrame()

# 3. دالة الإضافة (Create)
def add_row(sheet_name, row_data_list):
    """إضافة صف جديد (يجب أن تكون البيانات قائمة List)"""
    client = get_connection()
    if not client: return False
    try:
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        ws.append_row(row_data_list)
        return True
    except Exception as e:
        st.error(f"❌ فشل الإضافة: {e}")
        return False

# 4. دالة الحذف (Delete)
def delete_row(sheet_name, id_column, id_value):
    """حذف صف بناءً على قيمة المعرف (ID)"""
    client = get_connection()
    if not client: return False
    try:
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        
        # البحث عن الخلية التي تحتوي على الـ ID
        cell = ws.find(str(id_value))
        if cell:
            ws.delete_rows(cell.row)
            return True
        st.warning("⚠️ لم يتم العثور على العنصر لحذفه")
        return False
    except Exception as e:
        st.error(f"❌ فشل الحذف: {e}")
        return False

# 5. دالة التعديل (Update)
def update_field(sheet_name, id_column, id_value, target_column, new_value):
    """تحديث قيمة خلية واحدة محددة"""
    client = get_connection()
    if not client: return False
    try:
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        
        # البحث عن الصف
        cell = ws.find(str(id_value))
        if not cell:
            return False
            
        # البحث عن رقم العمود المستهدف
        headers = ws.row_values(1) # الصف الأول هو العناوين
        try:
            col_index = headers.index(target_column) + 1 # +1 لأن gspread يبدأ من 1
        except ValueError:
            st.error(f"العمود {target_column} غير موجود")
            return False
            
        # تحديث الخلية
        ws.update_cell(cell.row, col_index, new_value)
        return True
    except Exception as e:
        st.error(f"❌ فشل التحديث: {e}")
        return False
