from services.google_sheets import get_data, add_row, delete_row, update_field
from core.constants import TABLE_CONTENT
from utils.id_generator import generate_uuid
from datetime import datetime

class ContentModel:
    def __init__(self, content_id, category_id, content_type, title, body, media_id, social_link, form_id, created_by, created_at):
        self.content_id = content_id
        self.category_id = category_id
        self.content_type = content_type
        self.title = title
        self.body = body
        self.media_id = media_id
        self.social_link = social_link
        self.form_id = form_id
        self.created_by = created_by
        self.created_at = created_at

    @staticmethod
    def get_content_by_category(category_id):
        """جلب جميع المحتويات التابعة لصنف معين"""
        df = get_data(TABLE_CONTENT)
        content_list = []
        if not df.empty:
            # تصفية البيانات حسب الصنف
            filtered_df = df[df['category_id'] == str(category_id)]
            
            # (اختياري) يمكن إضافة ترتيب حسب التاريخ هنا
            # filtered_df = filtered_df.sort_values(by='created_at', ascending=False)
            
            for _, row in filtered_df.iterrows():
                content_list.append(ContentModel(
                    content_id=row['content_id'],
                    category_id=row['category_id'],
                    content_type=row['content_type'],
                    title=row['title'],
                    body=row['body'],
                    media_id=row['media_id'],
                    social_link=row['social_link'],
                    form_id=row['form_id'],
                    created_by=row['created_by'],
                    created_at=row['created_at']
                ))
        return content_list

    @staticmethod
    def create_content(category_id, content_type, title, body="", media_id="", social_link="", form_id="", created_by="System"):
        """إضافة محتوى جديد"""
        content_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # الترتيب في ملف CSV:
        # content_id, category_id, content_type, title, body, media_id, social_link, form_id, created_by, created_at
        new_row = [
            content_id,
            category_id,
            content_type,
            title,
            body,
            media_id,
            social_link,
            form_id,
            created_by,
            created_at
        ]
        
        return add_row(TABLE_CONTENT, new_row)

    @staticmethod
    def delete_content(content_id):
        """حذف محتوى"""
        return delete_row(TABLE_CONTENT, "content_id", content_id)

    @staticmethod
    def update_content_text(content_id, new_body):
        """تحديث نص المحتوى"""
        return update_field(TABLE_CONTENT, "content_id", content_id, "body", new_body)
