import streamlit as st
import gspread
import pandas as pd
import json
import time
import uuid
import hashlib
import io  # ضروري للصور
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload # ضروري للرفع والعرض
from gspread.exceptions import APIError, WorksheetNotFound
from streamlit_option_menu import option_menu

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

STATUS_ACTIVE = "active"

# ==========================================
# 2. إعدادات جوجل والاتصال (Google Config)
# ==========================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _get_creds_object():
    """تجهيز بيانات الاعتماد"""
    try:
        if "google" not in st.secrets: return None
        
        # دعم قراءة JSON كـ String أو Dict
        if "service_account_json" in st.secrets["google"]:
            creds_data = st.secrets["google"]["service_account_json"]
            creds_dict = json.loads(creds_data) if isinstance(creds_data, str) else creds_data
        elif "service_account" in st.secrets["google"]:
            creds_dict = dict(st.secrets["google"]["service_account"])
        else:
            return None
        
        # إصلاح مشاكل التشفير في private_key
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except: return None

@st.cache_resource(ttl=600)
def get_connection():
    """إنشاء اتصال مع Google Sheets"""
    c = _get_creds_object()
    return gspread.authorize(c) if c else None

def _execute_with_retry(func, *args, **kwargs):
    """دالة مساعدة لإعادة المحاولة عند حدوث أخطاء API"""
    for i in range(3):
        try: return func(*args, **kwargs)
        except APIError as e:
            if e.response.status_code == 429: time.sleep((i+1)*2); continue
            else: return None
        except: return None
    return None

# --- دوال التعامل مع البيانات (Data Operations) ---

def get_data(sheet_name):
    client = get_connection()
    if not client: return pd.DataFrame()
    def _fetch():
        try:
            sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
            ws = sh.worksheet(sheet_name)
            return pd.DataFrame(ws.get_all_records())
        except WorksheetNotFound: return pd.DataFrame()
    res = _execute_with_retry(_fetch)
    return res if res is not None else pd.DataFrame()

def add_row(sheet_name, row_data_list):
    client = get_connection()
    if not client: return False
    def _add():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        try: ws = sh.worksheet(sheet_name)
        except WorksheetNotFound: ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
        ws.append_row(row_data_list)
        return True
    return _execute_with_retry(_add) is True

def delete_row(sheet_name, id_column, id_value):
    client = get_connection()
    if not client: return False
    def _del():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if cell: ws.delete_rows(cell.row); return True
        return False
    return _execute_with_retry(_del) is True

def update_field(sheet_name, id_column, id_value, target_column, new_value):
    client = get_connection()
    if not client: return False
    def _upd():
        sh = client.open_by_key(st.secrets["google"]["spreadsheet_id"])
        ws = sh.worksheet(sheet_name)
        cell = ws.find(str(id_value))
        if not cell: return False
        headers = ws.row_values(1)
        try: 
            col_index = headers.index(target_column) + 1
            ws.update_cell(cell.row, col_index, new_value)
            return True
        except: return False
    return _execute_with_retry(_upd) is True

# --- دوال التعامل مع Google Drive (رفع وعرض) ---

def upload_file_to_cloud(file_obj, filename, mime_type):
    """رفع ملف إلى Google Drive (يدعم Shared Drives لتجنب مشكلة المساحة)"""
    creds = _get_creds_object()
    if not creds: return None, None
    try:
        fid = st.secrets["google"].get("drive_folder_id")
        service = build('drive', 'v3', credentials=creds)
        
        safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        meta = {'name': safe_name, 'parents': [fid]}
        
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
        
        # supportsAllDrives=True ضروري للمجلدات المشتركة
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
             st.error("❌ خطأ: مساحة التخزين ممتلئة. تأكد من أنك رفعت الملف إلى مجلد مشترك (Shared Drive) وأضفت إيميل البوت كـ Content Manager.")
        else:
             st.error(f"Upload Error: {error_msg}")
        return None, None

@st.cache_data(ttl=3600)
def get_file_content(file_id):
    """جلب محتوى الملف كـ Bytes لعرض الصور مباشرة"""
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
    except Exception as e:
        # يمكن طباعة الخطأ للتتبع: print(e)
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
        if add_row(TABLE_USERS, [generate_uuid(), name, email, phash, role_id, STATUS_ACTIVE, datetime.now().strftime("%Y-%m-%d")]):
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
    def create_section(name, by, pub): add_row(TABLE_SECTIONS, [generate_uuid(), name, by, datetime.now().strftime("%Y-%m-%d"), 99, str(pub)])

class TabModel:
    def __init__(self, tid, sid, name): self.tab_id, self.section_id, self.name = tid, sid, name
    @staticmethod
    def get_tabs_by_section(sid):
        df = get_data(TABLE_TABS)
        return [TabModel(r['tab_id'], r['section_id'], r['name']) for _, r in df[df['section_id']==str(sid)].iterrows()] if not df.empty else []
    @staticmethod
    def create_tab(sid, name, by): add_row(TABLE_TABS, [generate_uuid(), sid, name, by, datetime.now().strftime("%Y-%m-%d"), 99])

class CategoryModel:
    def __init__(self, cid, tid, name): self.category_id, self.tab_id, self.name = cid, tid, name
    @staticmethod
    def get_categories_by_tab(tid):
        df = get_data(TABLE_CATEGORIES)
        return [CategoryModel(r['category_id'], r['tab_id'], r['name']) for _, r in df[df['tab_id']==str(tid)].iterrows()] if not df.empty else []
    @staticmethod
    def create_category(tid, name, by): add_row(TABLE_CATEGORIES, [generate_uuid(), tid, name, by, datetime.now().strftime("%Y-%m-%d"), 99])

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
        add_row(TABLE_CONTENT, [generate_uuid(), cat_id, ctype, title, body, "", social_link, "", created_by, datetime.now().strftime("%Y-%m-%d")])
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
        add_row(TABLE_PERMISSIONS, [generate_uuid(), uid, str(sid), str(tid), str(cid), str(view), str(edit), str(hidden)])
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
    def add_item(main, sub, name, by): add_row(TABLE_CHECKLISTS, [generate_uuid(), main, sub, name, "FALSE", by])
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
        add_row(TABLE_MEDIA, [generate_uuid(), name, mtype, drive_id, by, datetime.now().strftime("%Y-%m-%d")])

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
        if "site_title" not in curr: add_row(TABLE_SETTINGS, ["site_title", "المنصة", "", user, ""])

# ==========================================
# 4. أدوات النظام (UI & Auth Helpers)
# ==========================================

def get_current_user():
    """إرجاع المستخدم من الجلسة"""
    if 'user' in st.session_state and st.session_state.get('logged_in'):
        return st.session_state['user']
    return None

def login_procedure(email, password):
    """منطق تسجيل الدخول"""
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
    """تطبيق CSS العام"""
    st.markdown("""
    <style>
        .stApp { direction: rtl; }
        .stMarkdown, .stText, .stHeader, .stSubheader, p, div, label, .stButton { text-align: right; }
        .stSidebar { text-align: right; direction: rtl; }
        div[data-testid="stMetricValue"] { direction: ltr; }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """رسم القائمة الجانبية"""
    user = get_current_user()
    with st.sidebar:
        if user:
            st.info(f"👤 {user.name}\n\n🏷️ {user.role_name}")
        
        selected = option_menu(
            menu_title=None,
            options=["الرئيسية", "الأقسام", "المكتبة", "النماذج", "التقارير", "الإدارة"],
            icons=["house", "collection", "images", "clipboard-check", "graph-up", "gear"],
            default_index=0,
            styles={"nav-link": {"font-size": "14px", "text-align": "right"}}
        )
        
        if selected == "الرئيسية":
            if st.button("🏠 الذهاب للرئيسية", use_container_width=True): st.switch_page("app.py")
        elif selected == "الأقسام": st.switch_page("pages/01_الاقسام.py")
        elif selected == "المكتبة": st.switch_page("pages/03_Media_Upload.py")
        elif selected == "النماذج": st.switch_page("pages/04_النماذج.py")
        elif selected == "التقارير":
            if user and user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: st.switch_page("pages/05_التقارير.py")
            else: st.warning("للمدراء فقط")
        elif selected == "الإدارة":
            if user and user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: st.switch_page("pages/02_ادارة_النظام.py")
            else: st.warning("للمدراء فقط")

        st.divider()
        if st.button("تسجيل خروج", type="primary"):
            logout_procedure()

def render_social_media(link):
    if "youtube" in link: st.video(link)
    else: st.markdown(f"🔗 [رابط]({link})")






# ==========================================
# أضف هذا الكود داخل ملف backend.py
# ==========================================

# 1. أولاً: تأكد من إنشاء جدول التعليقات في دالة init_db أو نفذ هذا الأمر في قاعدة البيانات
# CREATE TABLE IF NOT EXISTS comments (
#     comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     content_id INTEGER,
#     user_name TEXT,
#     comment_text TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY(content_id) REFERENCES contents(content_id)
# );

# 2. ثانياً: أضف كلاس التعامل مع التعليقات
class CommentModel:
    @staticmethod
    def create_comment(content_id, user_name, comment_text):
        with get_db_connection() as conn: # تأكد أن دالة الاتصال لديك اسمها هكذا
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comments (content_id, user_name, comment_text) VALUES (?, ?, ?)",
                (content_id, user_name, comment_text)
            )
            conn.commit()

    @staticmethod
    def get_comments_by_content(content_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT comment_id, user_name, comment_text, created_at FROM comments WHERE content_id = ? ORDER BY created_at ASC",
                (content_id,)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def delete_comment(comment_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comments WHERE comment_id = ?", (comment_id,))
            conn.commit()
