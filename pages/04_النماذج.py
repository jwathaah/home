import streamlit as st
import time
from models.checklist_model import ChecklistModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from utils.formatting import apply_custom_style

# 1. إعداد الصفحة
st.set_page_config(page_title="القوائم والنماذج", page_icon="☑️", layout="wide")

user = get_current_user()
if not user:
    st.toast("🔒 سجل دخولك أولاً")
    time.sleep(1)
    st.switch_page("app.py")

apply_custom_style()
is_admin = user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# ==========================================
# 🧠 إدارة البيانات الذكية (Smart Data Management)
# ==========================================

# 1. تحميل البيانات مرة واحدة فقط عند دخول الصفحة
if 'checklist_data' not in st.session_state:
    with st.spinner("جاري جلب القوائم..."):
        st.session_state.checklist_data = ChecklistModel.get_all_items()

# زر تحديث يدوي (لجلب التغييرات التي قام بها أشخاص آخرون)
col_ref1, col_ref2 = st.columns([10, 1])
with col_ref2:
    if st.button("🔄 تحديث"):
        st.session_state.checklist_data = ChecklistModel.get_all_items()
        st.rerun()

# 2. دالة التغيير الذكية (تحدث الذاكرة + جوجل)
def smart_toggle(item_id, current_status):
    # أ. التحديث في جوجل شيت (يكتب فقط ولا يقرأ)
    ChecklistModel.toggle_status(item_id, current_status)
    
    # ب. التحديث في الذاكرة المحلية فوراً (بدون اتصال بالنت)
    # نبحث عن العنصر في القائمة ونعكس حالته
    for item in st.session_state.checklist_data:
        if item.item_id == item_id:
            item.is_checked = not current_status
            break
    
    # ج. إعادة رسم الصفحة من الذاكرة (سريع جداً)
    st.rerun()

# 3. دالة الحذف الذكية
def smart_delete(item_id):
    ChecklistModel.delete_item(item_id)
    # حذف من الذاكرة المحلية
    st.session_state.checklist_data = [i for i in st.session_state.checklist_data if i.item_id != item_id]
    st.rerun()

# 4. دالة الإضافة الذكية
def smart_add(main, sub, name):
    ChecklistModel.add_item(main, sub, name, user.name)
    # هنا نضطر لجلب البيانات مرة أخرى لضمان الحصول على ID صحيح وجديد
    # لكن بما أن الإضافة لا تحدث بكثرة التفاعل، فلا بأس بذلك
    st.session_state.checklist_data = ChecklistModel.get_all_items()
    st.success("تمت الإضافة")
    st.rerun()


# استخدم البيانات من الذاكرة بدلاً من جلبها كل مرة
all_items = st.session_state.checklist_data
existing_main_titles = sorted(list(set([i.main_title for i in all_items])))

# ==========================================
# 1. القائمة الجانبية (الإضافة)
# ==========================================
if is_admin:
    with st.sidebar:
        st.header("⚙️ إدارة القوائم")
        with st.expander("➕ إنشاء / إضافة بند", expanded=True):
            with st.form("smart_add_form"):
                # العنوان الرئيسي
                main_options = ["✨ قسم جديد..."] + existing_main_titles
                selected_main = st.selectbox("العنوان الرئيسي", main_options)
                
                final_main = ""
                if selected_main == "✨ قسم جديد...":
                    final_main = st.text_input("اكتب اسم القسم الجديد", placeholder="مثال: بقالة")
                else:
                    final_main = selected_main
                
                # العنوان الفرعي
                sub_options = ["✨ فرعي جديد..."]
                if final_main and final_main != "✨ قسم جديد...":
                    relevant_subs = sorted(list(set([i.sub_title for i in all_items if i.main_title == final_main])))
                    sub_options += relevant_subs
                
                selected_sub = st.selectbox("العنوان الفرعي", sub_options)
                
                final_sub = ""
                if selected_sub == "✨ فرعي جديد...":
                    final_sub = st.text_input("اكتب العنوان الفرعي", placeholder="مثال: خضار")
                else:
                    final_sub = selected_sub

                new_item_name = st.text_input("اسم البند", placeholder="مثال: طماطم")
                
                if st.form_submit_button("حفظ البند"):
                    if final_main and final_sub and new_item_name:
                        smart_add(final_main, final_sub, new_item_name)
                    else:
                        st.warning("البيانات ناقصة")

# ==========================================
# 2. عرض القوائم (التصميم المظلل + الأداء السريع)
# ==========================================

if not all_items:
    st.info("القائمة فارغة، ابدأ بإضافة بنود.")
    st.stop()

main_titles = sorted(list(set([item.main_title for item in all_items])))
tabs = st.tabs(main_titles)

for i, main_title in enumerate(main_titles):
    with tabs[i]:
        section_items = [x for x in all_items if x.main_title == main_title]
        sub_titles = sorted(list(set([item.sub_title for item in section_items])))
        
        for sub_title in sub_titles:
            # العنوان الفرعي + زر الإضافة السريع
            col_head, col_add = st.columns([5, 1])
            col_head.markdown(f"### 🔸 {sub_title}")
            
            if is_admin:
                with col_add:
                    with st.popover("➕ بند"):
                        with st.form(f"quick_add_{main_title}_{sub_title}"):
                            st.write(f"إضافة إلى: {sub_title}")
                            quick_name = st.text_input("اسم البند", key=f"q_in_{main_title}_{sub_title}")
                            if st.form_submit_button("أضف"):
                                smart_add(main_title, sub_title, quick_name)
            
            # الفلترة والفرز
            my_items = [x for x in section_items if x.sub_title == sub_title]
            unchecked_items = [x for x in my_items if not x.is_checked]
            checked_items = [x for x in my_items if x.is_checked]
            
            # 1. غير المنجز
            if not unchecked_items and not checked_items:
                st.caption("لا توجد بنود.")
            
            for item in unchecked_items:
                c1, c2 = st.columns([0.5, 11])
                with c1:
                    # نستخدم smart_toggle هنا
                    st.checkbox("done", False, key=f"c_{item.item_id}", label_visibility="collapsed", on_change=smart_toggle, args=(item.item_id, False))
                with c2:
                    st.markdown(f"""<div style="padding: 5px; font-weight: 500;">{item.item_name}</div>""", unsafe_allow_html=True)
                    if is_admin:
                         if st.button("🗑", key=f"d_{item.item_id}"):
                             smart_delete(item.item_id)

            # 2. المنجز (مظلل)
            if checked_items:
                if unchecked_items: st.divider()
                for item in checked_items:
                    c1, c2 = st.columns([0.5, 11])
                    with c1:
                        st.checkbox("undone", True, key=f"c_{item.item_id}", label_visibility="collapsed", on_change=smart_toggle, args=(item.item_id, True))
                    with c2:
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #f0f2f6; 
                                color: #666; 
                                padding: 8px 12px; 
                                border-radius: 8px; 
                                border: 1px solid #e0e0e0;
                            ">
                                ✅ {item.item_name}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if is_admin:
                             if st.button("🗑", key=f"d_{item.item_id}"):
                                 smart_delete(item.item_id)
            
            st.write("")
