import streamlit as st
import gspread
import pandas as pd
import json
import time
import uuid
import hashlib
import io
import os  # ضروري جداً لتحديد المسارات
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from gspread.exceptions import APIError, WorksheetNotFound
from streamlit_option_menu import option_menu

# ==========================================
# 0. تحديد المسار الأساسي (FIX)
# ==========================================
# هذا السطر يضمن أننا نعرف مكان هذا الملف (backend.py)
# وبالتالي نستطيع العثور على ملف المفاتيح حتى لو تم استدعاؤنا من داخل مجلد pages
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. الثوابت (Constants)
# ==========================================
ROLE_SUPER_ADMIN = 1
ROLE_ADMIN = 2
ROLE_SUPERVISOR = 3
ROLE_MEMBER = 4
ROLE_GUEST = 5

ROLE_NAMES = {
    ROLE_SUPER_ADMIN: "المدير العام",
    ROLE_ADMIN: "مدير",
    ROLE_SUPERVISOR: "مشرف",
    ROLE_MEMBER: "عضو",
    ROLE_GUEST: "زائر"
}

# أسماء الجداول في قوقل شيت
TABLE_USERS = "users"
TABLE_ROLES = "roles"
TABLE_SECTIONS = "sections"
TABLE_TABS = "tabs"
TABLE_CATEGORIES = "categories"
TABLE_CONTENT = "content"
TABLE_PERMISSIONS = "permissions"
TABLE_MEDIA = "media_library"
TABLE_CHECKLISTS = "checklists"
TABLE_SETTINGS = "settings"
TABLE_COMMENTS = "comments"

STATUS_ACTIVE = "active"

# ==========================================
# 2. إعدادات جوجل والاتصال (Google Config)
# ==========================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _get_creds_object():
    """تجهيز بيانات الاعتماد - تم تحسينها لتعمل محلياً وعلى السيرفر"""
    
    # 1. المحاولة الأولى: عن طريق st.secrets (للاستخدام في Streamlit Cloud)
    if "google" in st.secrets:
        try:
            if "service_account_json" in st.secrets["google"]:
                creds_data = st.secrets["google"]["service_account_json"]
                creds_dict = json.loads(creds_data) if isinstance(creds_data, str) else creds_data
            elif "service_account" in st.secrets["google"]:
                creds_dict = dict(st.secrets["google"]["service_account"])
            else:
                creds_dict = None

            if creds_dict:
                if "private_key" in creds_dict:
                    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        except Exception as e:
            print(f"Error loading from secrets: {e}")

    # 2. المحاولة الثانية: عن طريق ملف JSON محلي (للاستخدام المحلي Localhost)
    # يبحث عن الملف بجانب backend.py مباشرة
    json_path = os.path.join(BASE_DIR, 'service_account.json')
    if os.path.exists(json_path):
        try:
            return Credentials.from_service_account_file(json_path, scopes=SCOPES)
        except Exception as e:
            st.error(f"خطأ في قراءة ملف المفاتيح المحلي: {e}")
            return None

    # إذا فشل كل شيء
    st.error("⚠️ لم يتم العثور على إعدادات الاتصال (secrets or service_account.json)")
    return None

@st.cache_resource(ttl=600)
def get_connection():
    """إنشاء اتصال مع Google Sheets"""
    c = _get_creds_object()
    return gspread.authorize(c) if c else None

def _execute_with_retry(func, *args, **kwargs):
    """دالة مساعدة لإعادة المحاولة بذكاء عند حدوث أخطاء API"""
    for i in range(5): # زيادة المحاولات إلى 5
        try: return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429: 
                # انتظار تصاعدي: 2, 3, 5, 9, 17 ثانية
                wait_time = (2 ** i) + 1
                time.sleep(wait_time)
                continue
            else: return None
        except: return None
    return None

# --- دوال التعامل مع البيانات (Data Operations) ---

# [تعديل هام]: إضافة الكاش هنا لتقليل الطلبات من قوقل
@st.cache_data(ttl=300) # يحفظ البيانات لمدة 5 دقائق
def get_data(sheet_name):
    client = get_connection()
    if not client: return pd.DataFrame()
    def _fetch():
        try:
            # محاولة جلب الآيدي من الأسرار، أو وضعه مباشرة هنا إذا كنت تعمل محلياً فقط
            sheet_id = st.secrets["google"].get("spreadsheet_id")
            if not sheet_id:
                pass 
            
            if not sheet_id:
                 return pd.DataFrame()

            sh = client.open_by_key(sheet_id)
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except WorksheetNotFound: return pd.DataFrame()
        except gspread.exceptions.GSpreadException: return pd.DataFrame() 
        except Exception as e: 
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    res = _execute_with_retry(_fetch)
    return res if res is not None else pd.DataFrame()

def add_row(sheet_name, row_data_list, new_sheet_headers=None):
    """إضافة صف ومسح الكاش لتحديث البيانات"""
    client = get_connection()
    if not client: return False
    def _add():
        sheet_id = st.secrets["google"].get("spreadsheet_id")
        if not sheet_id: return False

        sh = client.open_by_key(sheet_id)
        try: 
            ws = sh.worksheet(sheet_name)
        except WorksheetNotFound: 
            ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
            if new_sheet_headers:
                ws.append_row(new_sheet_headers)
        
        ws.append_row(row_data_list)
        return True
    
    # تنفيذ العملية
    result = _execute_with_retry(_add)
    
    # [تعديل هام]: مسح الكاش إذا تمت العملية بنجاح
    if result is True:
        st.cache_data.clear()
        return True
    return False

def delete_row(sheet_name, id_column, id_value):
    """حذف صف ومسح الكاش لتحديث البيانات"""
    client = get_connection()
    if not client: return False
    def _del():
        sheet_id = st.secrets["google"].get("spreadsheet_id")
        sh = client.open_by_key(sheet_id)
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if cell: ws.delete_rows(cell.row); return True
        return False
        
    result = _execute_with_retry(_del)
    
    # [تعديل هام]: مسح الكاش إذا تمت العملية بنجاح
    if result is True:
        st.cache_data.clear()
        return True
    return False

def update_field(sheet_name, id_column, id_value, target_column, new_value):
    """تحديث حقل ومسح الكاش لتحديث البيانات"""
    client = get_connection()
    if not client: return False
    def _upd():
        sheet_id = st.secrets["google"].get("spreadsheet_id")
        sh = client.open_by_key(sheet_id)
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if not cell: return False
        headers = ws.row_values(1)
        try: 
            col_index = headers.index(target_column) + 1
            ws.update_cell(cell.row, col_index, new_value)
            return True
        except: return False
        
    result = _execute_with_retry(_upd)
    
    # [تعديل هام]: مسح الكاش إذا تمت العملية بنجاح
    if result is True:
        st.cache_data.clear()
        return True
    return False

# --- دوال التعامل مع Google Drive (رفع وعرض) ---

def upload_file_to_cloud(file_obj, filename, mime_type):
    creds = _get_creds_object()
    if not creds: return None, None
    try:
        fid = st.secrets["google"].get("drive_folder_id")
        if not fid:
            st.error("لم يتم تحديد drive_folder_id في secrets")
            return None, None

        service = build('drive', 'v3', credentials=creds)
        
        safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        meta = {'name': safe_name, 'parents': [fid]}
        
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
        
        f = service.files().create(
            body=meta, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True,
            supportsTeamDrives=True
        ).execute()
        
        return f.get('id'), f.get('webViewLink')
        
    except Exception as e:
        error_msg = str(e)
        if "storageQuotaExceeded" in error_msg:
             st.error("❌ خطأ: مساحة التخزين ممتلئة.")
        else:
             st.error(f"Upload Error: {error_msg}")
        return None, None

@st.cache_data(ttl=3600)
def get_file_content(file_id):
    creds = _get_creds_object()
    if not creds: return None

    try:
        service = build('drive', 'v3', credentials=creds)
        request = service.files().get_media(fileId=file_id)
        
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        return file.getvalue()
    except Exception:
        return None

def generate_uuid(): return str(uuid.uuid4())

# ==========================================
# 3. الموديلات (Models)
# ==========================================

class UserModel:
    def __init__(self, uid, name, email, rid, status, created):
        self.user_id, self.name, self.email = uid, name, email
        self.role_id, self.status, self.created_at = int(rid), status, created
        self.role_name = ROLE_NAMES.get(self.role_id, "Unknown")
    @staticmethod
    def get_all_users():
        df = get_data(TABLE_USERS)
        return [UserModel(r['user_id'], r['name'], r['email'], r['role_id'], r['status'], r['created_at']) for _, r in df.iterrows()] if not df.empty else []
    @staticmethod
    def get_user_by_email(email):
        df = get_data(TABLE_USERS)
        if df.empty: return None, None
        row = df[df['email'] == email]
        if not row.empty:
            r = row.iloc[0]
            return UserModel(r['user_id'], r['name'], r['email'], r['role_id'], r['status'], r['created_at']), r['password_hash']
        return None, None
    @staticmethod
    def create_user(name, email, password, role_id):
        if UserModel.get_user_by_email(email)[0]: return False, "موجود مسبقاً"
        phash = hashlib.sha256(str.encode(password)).hexdigest()
        headers = ['user_id', 'name', 'email', 'password_hash', 'role_id', 'status', 'created_at']
        if add_row(TABLE_USERS, [generate_uuid(), name, email, phash, role_id, STATUS_ACTIVE, datetime.now().strftime("%Y-%m-%d")], new_sheet_headers=headers):
            return True, "تم"
        return False, "فشل"
    @staticmethod
    def update_user_status(uid, st): return update_field(TABLE_USERS, "user_id", uid, "status", st)
    @staticmethod
    def delete_user(uid): return delete_row(TABLE_USERS, "user_id", uid)

class SectionModel:
    def __init__(self, sid, name, public): self.section_id, self.name, self.is_public = sid, name, str(public).lower()=='true'
    @staticmethod
    def get_all_sections():
        df = get_data(TABLE_SECTIONS)
        return [SectionModel(r['section_id'], r['name'], r['is_public']) for _, r in df.sort_values('sort_order').iterrows()] if not df.empty else []
    @staticmethod
    def create_section(name, by, pub): 
        headers = ['section_id', 'name', 'created_by', 'created_at', 'sort_order', 'is_public']
        add_row(TABLE_SECTIONS, [generate_uuid(), name, by, datetime.now().strftime("%Y-%m-%d"), 99, str(pub)], new_sheet_headers=headers)

class TabModel:
    def __init__(self, tid, sid, name): self.tab_id, self.section_id, self.name = tid, sid, name
    @staticmethod
    def get_tabs_by_section(sid):
        df = get_data(TABLE_TABS)
        return [TabModel(r['tab_id'], r['section_id'], r['name']) for _, r in df[df['section_id']==str(sid)].iterrows()] if not df.empty else []
    @staticmethod
    def create_tab(sid, name, by): 
        headers = ['tab_id', 'section_id', 'name', 'created_by', 'created_at', 'sort_order']
        add_row(TABLE_TABS, [generate_uuid(), sid, name, by, datetime.now().strftime("%Y-%m-%d"), 99], new_sheet_headers=headers)

class CategoryModel:
    def __init__(self, cid, tid, name): self.category_id, self.tab_id, self.name = cid, tid, name
    @staticmethod
    def get_categories_by_tab(tid):
        df = get_data(TABLE_CATEGORIES)
        return [CategoryModel(r['category_id'], r['tab_id'], r['name']) for _, r in df[df['tab_id']==str(tid)].iterrows()] if not df.empty else []
    @staticmethod
    def create_category(tid, name, by): 
        headers = ['category_id', 'tab_id', 'name', 'created_by', 'created_at', 'sort_order']
        add_row(TABLE_CATEGORIES, [generate_uuid(), tid, name, by, datetime.now().strftime("%Y-%m-%d"), 99], new_sheet_headers=headers)

class ContentModel:
    def __init__(self, cid, catid, title, body, link, ctype, by, at):
        self.content_id, self.category_id, self.title = cid, catid, title
        self.body, self.social_link, self.content_type = body, link, ctype
        self.created_by, self.created_at = by, at
    @staticmethod
    def get_content_by_category(catid):
        df = get_data(TABLE_CONTENT)
        return [ContentModel(r['content_id'], r['category_id'], r['title'], r['body'], r['social_link'], r['content_type'], r['created_by'], r['created_at']) for _, r in df[df['category_id']==str(catid)].iterrows()] if not df.empty else []
    @staticmethod
    def create_content(cat_id, ctype, title, body, social_link, created_by):
        headers = ['content_id', 'category_id', 'content_type', 'title', 'body', 'file_url', 'social_link', 'thumbnail', 'created_by', 'created_at']
        add_row(TABLE_CONTENT, [generate_uuid(), cat_id, ctype, title, body, "", social_link, "", created_by, datetime.now().strftime("%Y-%m-%d")], new_sheet_headers=headers)
    @staticmethod
    def delete_content(cid): return delete_row(TABLE_CONTENT, "content_id", cid)

class PermissionModel:
    def __init__(self, pid, uid, sid, tid, view, edit, hidden):
        self.permission_id, self.user_id, self.section_id, self.tab_id = pid, uid, str(sid), str(tid)
        self.view, self.edit, self.hidden = str(view).lower()=='true', str(edit).lower()=='true', str(hidden).lower()=='true'
    @staticmethod
    def get_permissions_by_user(uid):
        df = get_data(TABLE_PERMISSIONS)
        return [PermissionModel(r['permission_id'], r['user_id'], r['section_id'], r['tab_id'], r['view'], r['edit'], r['hidden']) for _, r in df[df['user_id']==str(uid)].iterrows()] if not df.empty else []
    @staticmethod
    def grant_permission(uid, sid="", tid="", cid="", view=True, edit=False, hidden=False):
        headers = ['permission_id', 'user_id', 'section_id', 'tab_id', 'content_id', 'view', 'edit', 'hidden']
        add_row(TABLE_PERMISSIONS, [generate_uuid(), uid, str(sid), str(tid), str(cid), str(view), str(edit), str(hidden)], new_sheet_headers=headers)
    @staticmethod
    def check_access(uid, section_id=None):
        perms = PermissionModel.get_permissions_by_user(uid)
        for p in perms:
            if p.section_id == str(section_id) and not p.tab_id:
                if p.hidden: return False, False
                if p.view or p.edit: return True, p.edit
        return False, False

class ChecklistModel:
    def __init__(self, iid, main, sub, name, checked, by):
        self.item_id, self.main_title, self.sub_title, self.item_name = iid, main, sub, name
        self.is_checked, self.created_by = str(checked).upper()=='TRUE', by
    @staticmethod
    def get_all_items():
        df = get_data(TABLE_CHECKLISTS)
        return [ChecklistModel(r['item_id'], r['main_title'], r['sub_title'], r['item_name'], r['is_checked'], r['created_by']) for _, r in df.iterrows()] if not df.empty else []
    @staticmethod
    def add_item(main, sub, name, by): 
        headers = ['item_id', 'main_title', 'sub_title', 'item_name', 'is_checked', 'created_by']
        add_row(TABLE_CHECKLISTS, [generate_uuid(), main, sub, name, "FALSE", by], new_sheet_headers=headers)
    @staticmethod
    def toggle_status(iid, curr): update_field(TABLE_CHECKLISTS, "item_id", iid, "is_checked", "FALSE" if curr else "TRUE")
    @staticmethod
    def delete_item(iid): delete_row(TABLE_CHECKLISTS, "item_id", iid)

class MediaModel:
    def __init__(self, mid, name, mtype, did, by, at):
        self.media_id, self.file_name, self.file_type = mid, name, mtype
        self.google_drive_id, self.uploaded_by, self.uploaded_at = did, by, at
    @staticmethod
    def get_all_media():
        df = get_data(TABLE_MEDIA)
        return [MediaModel(r['media_id'], r['file_name'], r['file_type'], r['google_drive_id'], r['uploaded_by'], r['uploaded_at']) for _, r in df.iterrows()] if not df.empty else []
    @staticmethod
    def add_media(name, mtype, drive_id, by):
        headers = ['media_id', 'file_name', 'file_type', 'google_drive_id', 'uploaded_by', 'uploaded_at']
        add_row(TABLE_MEDIA, [generate_uuid(), name, mtype, drive_id, by, datetime.now().strftime("%Y-%m-%d")], new_sheet_headers=headers)

class SettingModel:
    def __init__(self, key, val): self.key, self.value = key, val
    @staticmethod
    def get_all_settings():
        df = get_data(TABLE_SETTINGS)
        return {r['setting_key']: SettingModel(r['setting_key'], r['setting_value']) for _, r in df.iterrows()} if not df.empty else {}
    @staticmethod
    def update_setting(key, val, user):
        update_field(TABLE_SETTINGS, "setting_key", key, "setting_value", str(val))
    @staticmethod
    def initialize_defaults(user):
        curr = SettingModel.get_all_settings()
        if "site_title" not in curr: 
            add_row(TABLE_SETTINGS, ["site_title", "المنصة", "", user, ""], new_sheet_headers=['setting_key', 'setting_value', 'description', 'updated_by', 'updated_at'])

# ==========================================
# 4. موديل التعليقات
# ==========================================
class CommentModel:
    @staticmethod
    def create_comment(content_id, user_name, comment_text):
        headers = ['comment_id', 'content_id', 'user_name', 'comment_text', 'created_at']
        return add_row(TABLE_COMMENTS, [
            generate_uuid(), 
            str(content_id), 
            user_name, 
            comment_text, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ], new_sheet_headers=headers)

    @staticmethod
    def get_comments_by_content(content_id):
        df = get_data(TABLE_COMMENTS)
        if df.empty: return []
        
        required_cols = ['content_id', 'user_name', 'comment_text', 'created_at']
        if not all(col in df.columns for col in required_cols):
            return []

        filtered_df = df[df['content_id'].astype(str) == str(content_id)]
        
        if not filtered_df.empty and 'created_at' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('created_at')
            
        return filtered_df.to_dict('records')

    @staticmethod
    def delete_comment(comment_id):
        return delete_row(TABLE_COMMENTS, "comment_id", comment_id)

# ==========================================
# 5. أدوات النظام
# ==========================================

def get_current_user():
    if 'user' in st.session_state and st.session_state.get('logged_in'):
        return st.session_state['user']
    return None

def login_procedure(email, password):
    hashed = hashlib.sha256(str.encode(password)).hexdigest()
    user, stored_hash = UserModel.get_user_by_email(email)
    if user and stored_hash == hashed:
        if user.status != 'active': return False, "الحساب موقوف"
        st.session_state['logged_in'] = True
        st.session_state['user'] = user
        return True, "تم الدخول"
    return False, "بيانات خاطئة"

def logout_procedure():
    st.session_state.clear()
    st.rerun()

def apply_custom_style():
    st.markdown("""
    <style>
        .stApp { direction: rtl; }
        .stMarkdown, .stText, .stHeader, .stSubheader, p, div, label, .stButton { text-align: right; }
        .stSidebar { text-align: right; direction: rtl; }
        div[data-testid="stMetricValue"] { direction: ltr; }
    </style>
    """, unsafe_allow_html=True)


