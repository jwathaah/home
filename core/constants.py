# تعريف أرقام الأدوار
ROLE_SUPER_ADMIN = 1
ROLE_ADMIN = 2
ROLE_SUPERVISOR = 3
ROLE_MEMBER = 4
ROLE_GUEST = 5

# قاموس لترجمة الأدوار
ROLE_NAMES = {
    ROLE_SUPER_ADMIN: "المدير العام",
    ROLE_ADMIN: "مدير",
    ROLE_SUPERVISOR: "مشرف",
    ROLE_MEMBER: "عضو",
    ROLE_GUEST: "زائر"
}

# أسماء الجداول في Google Sheets
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

# أنواع المحتوى
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_IMAGE = "image"
CONTENT_TYPE_VIDEO = "video"
CONTENT_TYPE_FILE = "file"
CONTENT_TYPE_FORM = "form"
CONTENT_TYPE_LINK = "link"

# حالات النظام
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_PENDING = "pending"
