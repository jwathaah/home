from services.google_sheets import get_data, add_row, update_field, delete_row
from core.constants import TABLE_SECTIONS, TABLE_TABS, TABLE_CATEGORIES
from utils.id_generator import generate_uuid
from datetime import datetime

# --- 1. نموذج القسم (Section) ---
class SectionModel:
    def __init__(self, section_id, name, created_by, created_at, sort_order, is_public):
        self.section_id = section_id
        self.name = name
        self.created_by = created_by
        self.created_at = created_at
        self.sort_order = sort_order
        self.is_public = str(is_public).lower() == 'true'

    @staticmethod
    def get_all_sections():
        df = get_data(TABLE_SECTIONS)
        sections = []
        if not df.empty:
            # ترتيب الأقسام حسب sort_order
            df = df.sort_values(by='sort_order', ascending=True)
            for _, row in df.iterrows():
                sections.append(SectionModel(
                    section_id=row['section_id'],
                    name=row['name'],
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    sort_order=row['sort_order'],
                    is_public=row['is_public']
                ))
        return sections

    @staticmethod
    def create_section(name, created_by, is_public=False):
        section_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # حساب الترتيب الجديد (آخر واحد + 1)
        sections = SectionModel.get_all_sections()
        sort_order = len(sections) + 1
        
        new_row = [section_id, name, created_by, created_at, sort_order, str(is_public)]
        return add_row(TABLE_SECTIONS, new_row)

    @staticmethod
    def delete_section(section_id):
        # ⚠️ ملاحظة: المفترض هنا حذف التبويبات التابعة له أيضاً (سنضيفها لاحقاً)
        return delete_row(TABLE_SECTIONS, "section_id", section_id)

# --- 2. نموذج التبويب (Tab) ---
class TabModel:
    def __init__(self, tab_id, section_id, name, created_by, created_at, sort_order):
        self.tab_id = tab_id
        self.section_id = section_id
        self.name = name
        self.created_by = created_by
        self.created_at = created_at
        self.sort_order = sort_order

    @staticmethod
    def get_tabs_by_section(section_id):
        df = get_data(TABLE_TABS)
        tabs = []
        if not df.empty:
            filtered_df = df[df['section_id'] == str(section_id)]
            filtered_df = filtered_df.sort_values(by='sort_order', ascending=True)
            for _, row in filtered_df.iterrows():
                tabs.append(TabModel(
                    tab_id=row['tab_id'],
                    section_id=row['section_id'],
                    name=row['name'],
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    sort_order=row['sort_order']
                ))
        return tabs

    @staticmethod
    def create_tab(section_id, name, created_by):
        tab_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        current_tabs = TabModel.get_tabs_by_section(section_id)
        sort_order = len(current_tabs) + 1
        
        new_row = [tab_id, section_id, name, created_by, created_at, sort_order]
        return add_row(TABLE_TABS, new_row)

# --- 3. نموذج الصنف (Category) ---
class CategoryModel:
    def __init__(self, category_id, tab_id, name, created_by, created_at, sort_order):
        self.category_id = category_id
        self.tab_id = tab_id
        self.name = name
        self.created_by = created_by
        self.created_at = created_at
        self.sort_order = sort_order

    @staticmethod
    def get_categories_by_tab(tab_id):
        df = get_data(TABLE_CATEGORIES)
        categories = []
        if not df.empty:
            filtered_df = df[df['tab_id'] == str(tab_id)]
            filtered_df = filtered_df.sort_values(by='sort_order', ascending=True)
            for _, row in filtered_df.iterrows():
                categories.append(CategoryModel(
                    category_id=row['category_id'],
                    tab_id=row['tab_id'],
                    name=row['name'],
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    sort_order=row['sort_order']
                ))
        return categories

    @staticmethod
    def create_category(tab_id, name, created_by):
        category_id = generate_uuid()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        current_cats = CategoryModel.get_categories_by_tab(tab_id)
        sort_order = len(current_cats) + 1
        
        new_row = [category_id, tab_id, name, created_by, created_at, sort_order]
        return add_row(TABLE_CATEGORIES, new_row)
