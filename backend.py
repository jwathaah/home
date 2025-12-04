import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
import pandas as pd
import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from gspread.exceptions import APIError

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

TABLE_USERS = "users"
TABLE_ROLES = "roles"
TABLE_SECTIONS = "sections"
TABLE_TABS = "tabs"
TABLE_CATEGORIES = "categories"
TABLE_CONTENT = "content"
TABLE_PERMISSIONS = "permissions"
TABLE_ACTIVITY_LOG = "activity_log"
TABLE_SESSIONS = "sessions"
TABLE_MEDIA = "media_library"
TABLE_FORMS = "forms"
TABLE_FORM_ANSWERS = "form_answers"
TABLE_COMMENTS = "comments"
TABLE_NOTIFICATIONS = "notifications"
TABLE_SETTINGS = "settings"
TABLE_CHECKLISTS = "checklists"

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# ==========================================
# 2. أدوات مساعدة (Helpers)
# ==========================================
def generate_uuid():
    return str(uuid.uuid4())

# ==========================================
# 3. خدمات جوجل (Google Services)
# ==========================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=600)
def get_connection():
    try:
        if "google" not in st.secrets: return None
        creds_data = st.secrets["google"].get("service_account_json") or st.secrets["google"].get("service_account")
        if not creds_data: return None

        if isinstance(creds_data, str):
            creds_dict = json.loads(creds_data)
        else:
            creds_dict = dict(creds_data)

        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error connecting to Sheets: {e}")
        return None

def get_storage_client():
    try:
        if "google" in st.secrets:
            creds_data = st.secrets["google"].get("service_account_json") or st.secrets["google"].get("service_account")
            if isinstance(creds_data, str): creds_dict = json.loads(creds_data)
            else: creds_dict = dict(creds_data)
            
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                
            credentials = Credentials.from_service_account_info(creds_dict)
            return storage.Client(credentials=credentials, project=creds_dict.get("project_id"))
        return None
    except: return None

def _execute_with_retry(func, *args, **kwargs):
    for i in range(3):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429:
                time.sleep((i + 1) * 2)
                continue
            else: return None
        except: return None
    return None

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
    return result is True

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
    return result is True

def update_field(sheet_name, id_column, id_value, target_column, new_value):
    client = get_connection()
    if not client: return False
    def _update():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if not cell: return False
        headers = ws.row_values(1)
        try: col_index = headers.index(target_column) + 1
        except: return False
        ws.update_cell(cell.row, col_index, new_value)
        return True
    result = _execute_with_retry(_update)
    return result is True

def upload_file_to_cloud(file_obj, filename, mime_type):
    client = get_storage_client()
    if not client: return None, None
    try:
        bucket_name = st.secrets["google"].get("bucket_name")
        bucket = client.bucket(bucket_name)
        safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        blob = bucket.blob(safe_filename)
        file_obj.seek(0)
        blob.upload_from_file(file_obj, content_type=mime_type)
        return safe_filename, f"https://storage.googleapis.com/{bucket_name}/{safe_filename}"
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None, None

# ==========================================
# 4. الموديلات (Models)
# ==========================================

class UserModel:
    def __init__(self, user_id, name, email, role_id, status, created_at):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role_id = int(role_id)
        self.status = status
        self.created_at = created_at
        self.role_name = ROLE_NAMES.get(self.role_id, "Unknown")

    @property
    def is_super_admin(self): return self.role_id == ROLE_SUPER_ADMIN
    @property
    def is_active(self): return self.status == STATUS_ACTIVE

    @st.cache_data(ttl=300)
    @staticmethod
    def get_all_users():
        df = get_data(TABLE_USERS)
        users = []
        if not df.empty:
            for _, row in df.iterrows():
                users.append(UserModel(row['user_id'], row['name'], row['email'], row['role_id'], row['status'], row['created_at']))
        return users

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
        existing, _ = UserModel.get_user_by_email(email)
        if existing: return False, "موجود مسبقاً"
        uid = generate_uuid()
        phash = hashlib.sha256(str.encode(password)).hexdigest()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if add_row(TABLE_USERS, [uid, name, email, phash, role_id, STATUS_ACTIVE, now]):
            return True, "تم الإنشاء"
        return False, "فشل الحفظ"

    @staticmethod
    def update_user_status(uid, status): return update_field(TABLE_USERS, "user_id", uid, "status", status)
    @staticmethod
    def delete_user(uid): return delete_row(TABLE_USERS, "user_id", uid)

class SessionModel:
    @staticmethod
    def create_session(user_id):
        sid, token = generate_uuid(), generate_uuid()
        now = datetime.now()
        exp = (now + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        add_row(TABLE_SESSIONS, [sid, user_id, token, now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S"), exp])
        return token

    @staticmethod
    def get_user_id_by_token(token):
        df = get_data(TABLE_SESSIONS)
        if not df.empty:
            row = df[df['token'] == str(token)]
            if not row.empty: return row.iloc[0]['user_id']
        return None

    @staticmethod
    def delete_session(token): return delete_row(TABLE_SESSIONS, "token", token)

class SectionModel:
    def __init__(self, section_id, name, is_public):
        self.section_id = section_id
        self.name = name
        self.is_public = str(is_public).lower() == 'true'

    @staticmethod
    def get_all_sections():
        df = get_data(TABLE_SECTIONS)
        return [SectionModel(r['section_id'], r['name'], r['is_public']) for _, r in df.sort_values('sort_order').iterrows()] if not df.empty else []

    @staticmethod
    def create_section(name, by, public=False):
        sid = generate_uuid()
        order = len(SectionModel.get_all_sections()) + 1
        add_row(TABLE_SECTIONS, [sid, name, by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order, str(public)])

    @staticmethod
    def delete_section(sid): return delete_row(TABLE_SECTIONS, "section_id", sid)

class TabModel:
    def __init__(self, tab_id, section_id, name):
        self.tab_id, self.section_id, self.name = tab_id, section_id, name
    @staticmethod
    def get_tabs_by_section(sid):
        df = get_data(TABLE_TABS)
        return [TabModel(r['tab_id'], r['section_id'], r['name']) for _, r in df[df['section_id']==str(sid)].sort_values('sort_order').iterrows()] if not df.empty else []
    @staticmethod
    def create_tab(sid, name, by):
        tid = generate_uuid()
        order = len(TabModel.get_tabs_by_section(sid)) + 1
        add_row(TABLE_TABS, [tid, sid, name, by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order])

class CategoryModel:
    def __init__(self, cid, tid, name):
        self.category_id, self.tab_id, self.name = cid, tid, name
    @staticmethod
    def get_categories_by_tab(tid):
        df = get_data(TABLE_CATEGORIES)
        return [CategoryModel(r['category_id'], r['tab_id'], r['name']) for _, r in df[df['tab_id']==str(tid)].sort_values('sort_order').iterrows()] if not df.empty else []
    @staticmethod
    def create_category(tid, name, by):
        cid = generate_uuid()
        order = len(CategoryModel.get_categories_by_tab(tid)) + 1
        add_row(TABLE_CATEGORIES, [cid, tid, name, by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order])

class ContentModel:
    def __init__(self, cid, cat_id, title, body, social, ctype, by, at):
        self.content_id, self.category_id, self.title, self.body = cid, cat_id, title, body
        self.social_link, self.content_type, self.created_by, self.created_at = social, ctype, by, at
    
    @staticmethod
    def get_content_by_category(cat_id):
        df = get_data(TABLE_CONTENT)
        return [ContentModel(r['content_id'], r['category_id'], r['title'], r['body'], r['social_link'], r['content_type'], r['created_by'], r['created_at']) for _, r in df[df['category_id']==str(cat_id)].iterrows()] if not df.empty else []

    @staticmethod
    def create_content(cat_id, ctype, title, body="", media_id="", social_link="", created_by=""):
        cid = generate_uuid()
        add_row(TABLE_CONTENT, [cid, cat_id, ctype, title, body, media_id, social_link, "", created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    @staticmethod
    def delete_content(cid): return delete_row(TABLE_CONTENT, "content_id", cid)

class PermissionModel:
    def __init__(self, pid, uid, sid, tid, cid, view, edit, hidden):
        self.permission_id, self.user_id = pid, uid
        self.section_id, self.tab_id, self.category_id = str(sid), str(tid), str(cid)
        self.view, self.edit, self.hidden = str(view).lower()=='true', str(edit).lower()=='true', str(hidden).lower()=='true'

    @staticmethod
    def get_permissions_by_user(uid):
        df = get_data(TABLE_PERMISSIONS)
        return [PermissionModel(r['permission_id'], r['user_id'], r['section_id'], r['tab_id'], r['category_id'], r['view'], r['edit'], r['hidden']) for _, r in df[df['user_id']==str(uid)].iterrows()] if not df.empty else []

    @staticmethod
    def grant_permission(uid, sid="", tid="", cid="", view=True, edit=False, hidden=False):
        existing = PermissionModel.get_permissions_by_user(uid)
        for p in existing:
            if p.section_id == str(sid) and p.tab_id == str(tid):
                delete_row(TABLE_PERMISSIONS, "permission_id", p.permission_id)
        add_row(TABLE_PERMISSIONS, [generate_uuid(), uid, str(sid), str(tid), str(cid), str(view), str(edit), str(hidden)])

    @staticmethod
    def check_access(uid, section_id=None, tab_id=None):
        perms = PermissionModel.get_permissions_by_user(uid)
        for p in perms:
            if section_id and p.section_id == str(section_id) and not p.tab_id:
                if p.hidden: return False, False
                if p.view or p.edit: return True, p.edit
        return False, False

class ChecklistModel:
    def __init__(self, item_id, main, sub, name, checked, by):
        self.item_id, self.main_title, self.sub_title, self.item_name = item_id, main, sub, name
        self.is_checked, self.created_by = str(checked).upper() == "TRUE", by
    @staticmethod
    def get_all_items():
        df = get_data(TABLE_CHECKLISTS)
        return [ChecklistModel(r['item_id'], r['main_title'], r['sub_title'], r['item_name'], r['is_checked'], r['created_by']) for _, r in df.iterrows()] if not df.empty else []
    @staticmethod
    def add_item(main, sub, name, by):
        add_row(TABLE_CHECKLISTS, [generate_uuid(), main, sub, name, "FALSE", by])
    @staticmethod
    def toggle_status(iid, current):
        update_field(TABLE_CHECKLISTS, "item_id", iid, "is_checked", "FALSE" if current else "TRUE")
    @staticmethod
    def delete_item(iid): delete_row(TABLE_CHECKLISTS, "item_id", iid)

class MediaModel:
    def __init__(self, mid, name, mtype, drive_id, by, at):
        self.media_id, self.file_name, self.file_type = mid, name, mtype
        self.google_drive_id, self.uploaded_by, self.uploaded_at = drive_id, by, at
    @staticmethod
    def get_all_media():
        df = get_data(TABLE_MEDIA)
        return [MediaModel(r['media_id'], r['file_name'], r['file_type'], r['google_drive_id'], r['uploaded_by'], r['uploaded_at']) for _, r in df.iterrows()] if not df.empty else []
    @staticmethod
    def add_media(name, mtype, drive_id, by):
        add_row(TABLE_MEDIA, [generate_uuid(), name, mtype, drive_id, by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

class SettingModel:
    def __init__(self, key, value, desc, by, at):
        self.key, self.value = key, value
        self.updated_by, self.updated_at = by, at
    @staticmethod
    def get_all_settings():
        df = get_data(TABLE_SETTINGS)
        return {r['setting_key']: SettingModel(r['setting_key'], r['setting_value'], r['description'], r['updated_by'], r['updated_at']) for _, r in df.iterrows()} if not df.empty else {}
    @staticmethod
    def update_setting(key, val, user):
        if update_field(TABLE_SETTINGS, "setting_key", key, "setting_value", str(val)):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_field(TABLE_SETTINGS, "setting_key", key, "updated_by", user)
            update_field(TABLE_SETTINGS, "setting_key", key, "updated_at", now)
    @staticmethod
    def initialize_defaults(user):
        curr = SettingModel.get_all_settings()
        defaults = [["site_title", "المنصة", "العنوان"], ["system_status", "active", "الحالة"], ["allow_guest_view", "false", "الزوار"], ["announcement_bar", "", "إعلان"]]
        for k, v, d in defaults:
            if k not in curr: add_row(TABLE_SETTINGS, [k, v, d, user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
