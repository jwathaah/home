from services.google_sheets import get_data, add_row, update_field, delete_row
from core.constants import TABLE_USERS, STATUS_ACTIVE, ROLE_SUPER_ADMIN
from utils.id_generator import generate_uuid
from datetime import datetime
import hashlib

class UserModel:
    def __init__(self, user_id, name, email, role_id, status, created_at):
        self.user_id = user_id
        self.name = name
        self.email = email
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
        """جلب جميع المستخدمين من قاعدة البيانات"""
        df = get_data(TABLE_USERS)
        users = []
        if not df.empty:
            for _, row in df.iterrows():
                users.append(UserModel(
                    user_id=row['user_id'],
                    name=row['name'],
                    email=row['email'],
                    role_id=row['role_id'],
                    status=row['status'],
                    created_at=row['created_at']
                ))
        return users

    @staticmethod
    def get_user_by_email(email):
        """البحث عن مستخدم بالبريد الإلكتروني"""
        df = get_data(TABLE_USERS)
        if df.empty:
            return None
        
        # البحث في الـ DataFrame
        user_row = df[df['email'] == email]
        if not user_row.empty:
            row = user_row.iloc[0]
            # نحتاج الباسورد هنا للتحقق، لذا سنرجع الصف الخام مؤقتًا أو نعدل الـ init
            # للأمان، سنرجع الكائن، والتحقق من الباسورد يتم في دالة منفصلة
            return UserModel(
                user_id=row['user_id'],
                name=row['name'],
                email=row['email'],
                role_id=row['role_id'],
                status=row['status'],
                created_at=row['created_at']
            ), row['password_hash'] # نرجع الهاش للتحقق
        return None, None

    @staticmethod
    def create_user(name, email, password, role_id):
        """إنشاء مستخدم جديد"""
        # التحقق من عدم وجود الايميل مسبقًا
        existing_user, _ = UserModel.get_user_by_email(email)
        if existing_user:
            return False, "البريد الإلكتروني مسجل مسبقًا"

        user_id = generate_uuid()
        password_hash = hashlib.sha256(str.encode(password)).hexdigest()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_user = [
            user_id, 
            name, 
            email, 
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
        """تغيير حالة المستخدم (تجميد/تفعيل)"""
        return update_field(TABLE_USERS, "user_id", user_id, "status", new_status)
        
    @staticmethod
    def delete_user(user_id):
        """حذف مستخدم نهائيًا"""
        return delete_row(TABLE_USERS, "user_id", user_id)
