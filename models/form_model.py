from services.google_sheets import get_data, add_row, delete_row
from core.constants import TABLE_FORMS, TABLE_FORM_ANSWERS
from utils.id_generator import generate_uuid
from datetime import datetime
import json
import streamlit as st

class FormModel:
    def __init__(self, form_id, category_id, title, description, config_json, created_by, created_at):
        self.form_id = form_id
        self.category_id = category_id
        self.title = title
        self.description = description
        self.config_json = config_json # يخزن الأسئلة كـ نص JSON
        self.created_by = created_by
        self.created_at = created_at

    @staticmethod
    def create_form(category_id, title, description, fields_list, created_by):
        """
        إنشاء نموذج جديد
        fields_list: قائمة تحتوي على إعدادات الحقول (نوع الحقل، السؤال، الخيارات)
        """
        form_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # تحويل القائمة إلى نص JSON للتخزين في خلية واحدة
        config_json = json.dumps(fields_list, ensure_ascii=False)
        
        # الترتيب حسب ملف CSV: form_id, category_id, title, description, config_json, created_by, created_at
        row = [form_id, category_id, title, description, config_json, created_by, created_at]
        return add_row(TABLE_FORMS, row)

    @staticmethod
    def get_all_forms():
        """جلب جميع النماذج"""
        df = get_data(TABLE_FORMS)
        forms = []
        if not df.empty:
            for _, row in df.iterrows():
                forms.append(FormModel(
                    form_id=row['form_id'],
                    category_id=row['category_id'],
                    title=row['title'],
                    description=row['description'],
                    config_json=row['config_json'],
                    created_by=row['created_by'],
                    created_at=row['created_at']
                ))
        return forms
    
    @staticmethod
    def delete_form(form_id):
        return delete_row(TABLE_FORMS, "form_id", form_id)

    def get_fields(self):
        """تحويل النص JSON المخزن إلى قائمة بايثون لاستخدامها"""
        try:
            return json.loads(self.config_json)
        except:
            return []

class FormAnswerModel:
    def __init__(self, answer_id, form_id, user_id, answer_json, created_at):
        self.answer_id = answer_id
        self.form_id = form_id
        self.user_id = user_id
        self.answer_json = answer_json
        self.created_at = created_at

    @staticmethod
    def submit_answer(form_id, user_id, answers_dict):
        """حفظ إجابات المستخدم"""
        answer_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # تحويل الإجابات إلى نص JSON
        answer_json_str = json.dumps(answers_dict, ensure_ascii=False)
        
        # الترتيب حسب ملف CSV: answer_id, form_id, user_id, answer_json, created_at
        row = [answer_id, form_id, user_id, answer_json_str, created_at]
        return add_row(TABLE_FORM_ANSWERS, row)

    @staticmethod
    def get_answers_by_form(form_id):
        """جلب جميع الإجابات لنموذج معين"""
        df = get_data(TABLE_FORM_ANSWERS)
        answers = []
        if not df.empty:
            filtered = df[df['form_id'] == str(form_id)]
            # ترتيب حسب الأحدث
            # filtered = filtered.sort_values(by='created_at', ascending=False)
            
            for _, row in filtered.iterrows():
                answers.append(FormAnswerModel(
                    answer_id=row['answer_id'],
                    form_id=row['form_id'],
                    user_id=row['user_id'],
                    answer_json=row['answer_json'],
                    created_at=row['created_at']
                ))
        return answers
        
    def get_parsed_answers(self):
        """تحويل نص الإجابة إلى قاموس"""
        try:
            return json.loads(self.answer_json)
        except:
            return {}
