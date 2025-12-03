from services.google_sheets import get_data, add_row, delete_row
from core.constants import TABLE_MEDIA
from utils.id_generator import generate_uuid
from datetime import datetime

class MediaModel:
    def __init__(self, media_id, file_name, file_type, google_drive_id, uploaded_by, uploaded_at):
        self.media_id = media_id
        self.file_name = file_name
        self.file_type = file_type
        self.google_drive_id = google_drive_id
        self.uploaded_by = uploaded_by
        self.uploaded_at = uploaded_at

    @staticmethod
    def get_all_media():
        """جلب جميع الملفات الموجودة في مكتبة الوسائط"""
        df = get_data(TABLE_MEDIA)
        media_list = []
        if not df.empty:
            # ترتيب عكسي (الأحدث أولاً)
            # df = df.sort_values(by='uploaded_at', ascending=False)
            
            for _, row in df.iterrows():
                media_list.append(MediaModel(
                    media_id=row['media_id'],
                    file_name=row['file_name'],
                    file_type=row['file_type'],
                    google_drive_id=row['google_drive_id'],
                    uploaded_by=row['uploaded_by'],
                    uploaded_at=row['uploaded_at']
                ))
        return media_list

    @staticmethod
    def add_media(file_name, file_type, google_drive_id, uploaded_by):
        """تسجيل ملف جديد في قاعدة البيانات"""
        media_id = generate_uuid()
        uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # الترتيب حسب ملف CSV:
        # media_id, file_name, file_type, google_drive_id, uploaded_by, uploaded_at
        new_row = [
            media_id,
            file_name,
            file_type,
            google_drive_id,
            uploaded_by,
            uploaded_at
        ]
        
        return add_row(TABLE_MEDIA, new_row)

    @staticmethod
    def delete_media(media_id):
        """حذف سجل الملف من قاعدة البيانات"""
        # ملاحظة: هذا يحذف السجل فقط، لحذف الملف من Drive نحتاج صلاحيات إضافية معقدة
        return delete_row(TABLE_MEDIA, "media_id", media_id)
