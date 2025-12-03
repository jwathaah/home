from services.google_sheets import get_data, add_row, delete_row, update_field
from core.constants import TABLE_CHECKLISTS
from utils.id_generator import generate_uuid
from datetime import datetime
import streamlit as st

class ChecklistModel:
    def __init__(self, item_id, main_title, sub_title, item_name, is_checked, created_by):
        self.item_id = item_id
        self.main_title = main_title
        self.sub_title = sub_title
        self.item_name = item_name
        # تحويل النص "TRUE"/"FALSE" إلى بوليان
        self.is_checked = str(is_checked).upper() == "TRUE"
        self.created_by = created_by

    @staticmethod
    def get_all_items():
        """جلب كافة البنود"""
        df = get_data(TABLE_CHECKLISTS)
        items = []
        if not df.empty:
            for _, row in df.iterrows():
                items.append(ChecklistModel(
                    item_id=row['item_id'],
                    main_title=row['main_title'],
                    sub_title=row['sub_title'],
                    item_name=row['item_name'],
                    is_checked=row['is_checked'],
                    created_by=row['created_by']
                ))
        return items

    @staticmethod
    def add_item(main_title, sub_title, item_name, created_by):
        """إضافة بند جديد"""
        item_id = generate_uuid()
        # الترتيب: item_id, main_title, sub_title, item_name, is_checked, created_by
        row = [item_id, main_title, sub_title, item_name, "FALSE", created_by]
        return add_row(TABLE_CHECKLISTS, row)

    @staticmethod
    def toggle_status(item_id, current_status):
        """عكس الحالة: إذا كانت صح تصبح خطأ والعكس"""
        new_status = "FALSE" if current_status else "TRUE"
        # تحديث العمود "is_checked"
        return update_field(TABLE_CHECKLISTS, "item_id", item_id, "is_checked", new_status)

    @staticmethod
    def delete_item(item_id):
        return delete_row(TABLE_CHECKLISTS, "item_id", item_id)
