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

# --- دوال مساعدة ---
def toggle_item(item_id, current_status):
    ChecklistModel.toggle_status(item_id, current_status)
    st.cache_resource.clear()
    st.rerun()

# جلب البيانات
all_items = ChecklistModel.get_all_items()
existing_main_titles = sorted(list(set([i.main_title for i in all_items])))

# ==========================================
# 1. القائمة الجانبية (ذكية)
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

                # اسم البند
                new_item_name = st.text_input("اسم البند", placeholder="مثال: طماطم")
                
                if st.form_submit_button("حفظ البند"):
                    if final_main and final_sub and new_item_name:
                        ChecklistModel.add_item(final_main, final_sub, new_item_name, user.name)
                        st.cache_resource.clear()
                        st.success("تم!")
                        st.rerun()
                    else:
                        st.warning("البيانات ناقصة")

# ==========================================
# 2. عرض القوائم (التصميم الجديد المظلل)
# ==========================================

if not all_items:
    st.info("ابدأ بإضافة أول قسم من القائمة الجانبية.")
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
                                ChecklistModel.add_item(main_title, sub_title, quick_name, user.name)
                                st.cache_resource.clear()
                                st.rerun()
            
            # الفلترة
            my_items = [x for x in section_items if x.sub_title == sub_title]
            unchecked_items = [x for x in my_items if not x.is_checked]
            checked_items = [x for x in my_items if x.is_checked]
            
            # 1. غير المنجز (يظهر كنص عادي نظيف)
            if not unchecked_items and not checked_items:
                st.caption("لا توجد بنود.")
            
            for item in unchecked_items:
                c1, c2 = st.columns([0.5, 11])
                with c1:
                    st.checkbox("done", False, key=f"c_{item.item_id}", label_visibility="collapsed", on_change=toggle_item, args=(item.item_id, False))
                with c2:
                    # تصميم بسيط ونظيف لغير المنجز
                    st.markdown(
                        f"""<div style="padding: 5px; font-weight: 500;">{item.item_name}</div>""", 
                        unsafe_allow_html=True
                    )
                    
                    if is_admin:
                         if st.button("🗑", key=f"d_{item.item_id}"):
                             ChecklistModel.delete_item(item.item_id)
                             st.cache_resource.clear()
                             st.rerun()

            # 2. المنجز (يظهر مظللاً بخلفية رمادية خفيفة بدلاً من الشطب)
            if checked_items:
                if unchecked_items: st.divider()
                for item in checked_items:
                    c1, c2 = st.columns([0.5, 11])
                    with c1:
                        st.checkbox("undone", True, key=f"c_{item.item_id}", label_visibility="collapsed", on_change=toggle_item, args=(item.item_id, True))
                    with c2:
                        # 🔥 التعديل هنا: ستايل مظلل (Shaded Style)
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
                                 ChecklistModel.delete_item(item.item_id)
                                 st.cache_resource.clear()
                                 st.rerun()
            
            st.write("") # مسافة
