from services.google_sheets import get_data, update_field, add_row
from core.constants import TABLE_SETTINGS
from datetime import datetime

class SettingModel:
    def __init__(self, key, value, description, updated_by, updated_at):
        self.key = key
        self.value = value
        self.description = description
        self.updated_by = updated_by
        self.updated_at = updated_at

    @staticmethod
    def get_all_settings():
        """جلب جميع الإعدادات كقاموس لسهولة الاستخدام"""
        df = get_data(TABLE_SETTINGS)
        settings = {}
        if not df.empty:
            for _, row in df.iterrows():
                settings[row['setting_key']] = SettingModel(
                    key=row['setting_key'],
                    value=row['setting_value'],
                    description=row['description'],
                    updated_by=row['updated_by'],
                    updated_at=row['updated_at']
                )
        return settings

    @staticmethod
    def get_setting_value(key, default_value=""):
        """جلب قيمة إعداد معين مباشرة"""
        all_settings = SettingModel.get_all_settings()
        if key in all_settings:
            return all_settings[key].value
        return default_value

    @staticmethod
    def update_setting(key, new_value, user_name):
        """تحديث قيمة إعداد"""
        try:
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # تحديث القيمة
            # ملاحظة: نفترض أن المفتاح هو العمود الأول 'setting_key' في ملف settings.csv
            success = update_field(TABLE_SETTINGS, "setting_key", key, "setting_value", str(new_value))
            
            if success:
                # تحديث التوقيع (من عدّل ومتى)
                update_field(TABLE_SETTINGS, "setting_key", key, "updated_by", user_name)
                update_field(TABLE_SETTINGS, "setting_key", key, "updated_at", time_now)
                return True
            return False
        except Exception as e:
            print(f"Error updating setting {key}: {e}")
            return False

    @staticmethod
    def initialize_defaults(user_name="System"):
        """دالة لإنشاء الإعدادات الافتراضية إذا كان الجدول فارغاً"""
        current = SettingModel.get_all_settings()
        
        defaults = [
            # key, value, description
            ["site_title", "المنصة المركزية", "عنوان الموقع الذي يظهر في الأعلى"],
            ["system_status", "active", "حالة النظام (active/maintenance)"],
            ["allow_guest_view", "false", "السماح للضيوف بالمشاهدة"],
            ["announcement_bar", "", "شريط إعلانات يظهر في أعلى الصفحات"]
        ]
        
        for item in defaults:
            key, val, desc = item
            if key not in current:
                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                add_row(TABLE_SETTINGS, [key, val, desc, user_name, time_now])
