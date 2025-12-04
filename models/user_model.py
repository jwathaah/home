from services.google_sheets import get_data, add_row, update_field, delete_row
from core.constants import TABLE_USERS, STATUS_ACTIVE, ROLE_SUPER_ADMIN
from utils.id_generator import generate_uuid
from datetime import datetime
import hashlib

class UserModel:
    def __init__(self, user_id, name, username, role_id, status, created_at):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.role_id = int(role_id)
        self.status = status
        self.created_at = created_at

    @property
    def is_super_admin(self):
        return self.role_id == ROLE_SUPER_ADMIN

    @property
    def is_active(self):
        return self.status == STATUS_ACTIVE

    @staticmethod
    def get_all_users():
        df = get_data(TABLE_USERS)
        users = []
        if not df.empty:
            # تطبيع عمود username
            if 'username' in df.columns:
                df['username'] = df['username'].astype(str).str.strip().str.lower()
            for _, row in df.iterrows():
                users.append(UserModel(
                    user_id=row['user_id'],
                    name=row['name'],
                    username=row.get('username', ""),
                    role_id=row['role_id'],
                    status=row['status'],
                    created_at=row['created_at']
                ))
        return users

    @staticmethod
    def get_user_by_username(username):
        df = get_data(TABLE_USERS)
        if df.empty:
            return None, None

        # تطبيع اسم المستخدم والعمود
        if 'username' not in df.columns:
            return None, None

        df['username'] = df['username'].astype(str).str.strip().str.lower()
        username = str(username).strip().lower()

        user_row = df[df['username'] == username]
        if not user_row.empty:
            row = user_row.iloc[0]
            return UserModel(
                user_id=row['user_id'],
                name=row['name'],
                username=row['username'],
                role_id=row['role_id'],
                status=row['status'],
                created_at=row['created_at']
            ), row.get('password_hash', None)
        return None, None

    @staticmethod
    def create_user(name, username, password, role_id):
        username = str(username).strip().lower()
        existing_user, _ = UserModel.get_user_by_username(username)
        if existing_user:
            return False, "اسم المستخدم مسجل مسبقًا"

        user_id = generate_uuid()
        password_hash = hashlib.sha256(str(password).encode()).hexdigest()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_user = [
            user_id,
            name,
            username,
            password_hash,
            role_id,
            STATUS_ACTIVE,
            created_at
        ]

        success = add_row(TABLE_USERS, new_user)
        if success:
            return True, "تم إنشاء المستخدم بنجاح"
        return False, "حدث خطأ أثناء الاتصال بقاعدة البيانات"

    @staticmethod
    def update_user_status(user_id, new_status):
        return update_field(TABLE_USERS, "user_id", user_id, "status", new_status)

    @staticmethod
    def delete_user(user_id):
        return delete_row(TABLE_USERS, "user_id", user_id)
