from services.google_sheets import get_data, add_row, update_field, delete_row
from core.constants import TABLE_PERMISSIONS
from utils.id_generator import generate_uuid

class PermissionModel:
    def __init__(self, permission_id, user_id, section_id, tab_id, category_id, view, edit, hidden):
        self.permission_id = permission_id
        self.user_id = user_id
        self.section_id = str(section_id) if section_id else ""
        self.tab_id = str(tab_id) if tab_id else ""
        self.category_id = str(category_id) if category_id else ""
        
        # تحويل القيم النصية إلى Boolean
        self.view = str(view).lower() == 'true'
        self.edit = str(edit).lower() == 'true'
        self.hidden = str(hidden).lower() == 'true'

    @staticmethod
    def get_permissions_by_user(user_id):
        """جلب كافة صلاحيات مستخدم معين"""
        df = get_data(TABLE_PERMISSIONS)
        perms = []
        if not df.empty:
            user_perms = df[df['user_id'] == str(user_id)]
            for _, row in user_perms.iterrows():
                perms.append(PermissionModel(
                    permission_id=row['permission_id'],
                    user_id=row['user_id'],
                    section_id=row['section_id'],
                    tab_id=row['tab_id'],
                    category_id=row['category_id'],
                    view=row['view'],
                    edit=row['edit'],
                    hidden=row['hidden']
                ))
        return perms

    @staticmethod
    def grant_permission(user_id, section_id="", tab_id="", category_id="", view=True, edit=False, hidden=False):
        """منح صلاحية جديدة"""
        # أولاً: التحقق مما إذا كانت الصلاحية موجودة مسبقاً لتحديثها بدلاً من تكرارها
        existing_perms = PermissionModel.get_permissions_by_user(user_id)
        
        target_perm = None
        for p in existing_perms:
            # التحقق من تطابق الهدف (نفس القسم أو نفس التبويب...)
            if p.section_id == str(section_id) and p.tab_id == str(tab_id) and p.category_id == str(category_id):
                target_perm = p
                break
        
        if target_perm:
            # تحديث الموجود
            # ملاحظة: في النسخة البسيطة سنحذف القديم ونضيف الجديد، أو نحدث الحقول
            # للأمان والسرعة هنا سنقوم بالتحديث المباشر
            # لكن gspread لا يدعم تحديث صف كامل بسهولة، لذا سنحذف القديم ونضيف الجديد
            delete_row(TABLE_PERMISSIONS, "permission_id", target_perm.permission_id)

        # إضافة الجديد
        perm_id = generate_uuid()
        new_row = [
            perm_id, user_id, 
            str(section_id), str(tab_id), str(category_id), 
            str(view), str(edit), str(hidden)
        ]
        return add_row(TABLE_PERMISSIONS, new_row)

    @staticmethod
    def check_access(user_id, section_id=None, tab_id=None, category_id=None):
        """
        دالة ذكية لفحص هل يمتلك المستخدم صلاحية العرض؟
        تعيد (can_view, can_edit)
        """
        perms = PermissionModel.get_permissions_by_user(user_id)
        
        can_view = False
        can_edit = False
        
        for p in perms:
            # فحص مستوى القسم
            if section_id and p.section_id == str(section_id) and not p.tab_id and not p.category_id:
                if p.hidden: return False, False # محجوب صراحة
                if p.view: can_view = True
                if p.edit: can_edit = True
            
            # فحص مستوى التبويب (إذا كنا نفحص تبويب)
            if tab_id and p.tab_id == str(tab_id):
                if p.hidden: return False, False
                if p.view: can_view = True
                if p.edit: can_edit = True

             # فحص مستوى التصنيف (إذا كنا نفحص تصنيف)
            if category_id and p.category_id == str(category_id):
                if p.hidden: return False, False
                if p.view: can_view = True
                if p.edit: can_edit = True
                
        return can_view, can_edit
