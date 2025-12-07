import streamlit as st
import time
import pandas as pd

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
try:
    # استدعاء النماذج من الباك إند الموحد
    # ملاحظة: تأكد أن كلاس ChecklistModel موجود في backend.py
    # إذا لم يكن موجوداً، يجب نقله من models/checklist_model.py إلى backend.py
    from backend import (
        ChecklistModel, 
        ROLE_SUPER_ADMIN, ROLE_ADMIN
    )
    from core.auth import get_current_user
    from utils.formatting import apply_custom_style
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد: {e}\nتأكد من تحديث backend.py ليشمل ChecklistModel.")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="القوائم والنماذج", page_icon="☑️", layout="wide")

# ==========================================
# 3. التحقق من الصلاحيات
# ==========================================
user = get_current_user()
if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# تطبيق التنسيق العام
try:
    apply_custom_style()
except:
    pass

# تحديد ما إذا كان المستخدم أدمن (للإضافة والحذف)
is_admin = user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# ==========================================
# 4. دوال معالجة البيانات (Logic & Caching)
# ==========================================

@st.cache_data(ttl=60)
def get_cached_checklists():
    """جلب جميع عناصر القوائم وتخزينها مؤقتاً"""
    return ChecklistModel.get_all_items()

def clear_checklist_cache():
    """مسح الكاش لإجبار النظام على جلب بيانات جديدة"""
    st.cache_data.clear()

def toggle_item_status(item_id, current_status):
    """تغيير حالة العنصر (منجز/غير منجز)"""
    ChecklistModel.toggle_status(item_id, current_status)
    clear_checklist_cache()
    # لا نحتاج st.rerun() هنا لأن Streamlit سيعيد التشغيل تلقائياً عند تغيير الـ checkbox
    # ولكن للتأكيد على تحديث الواجهة سنتركها في مكان الاستدعاء

# ==========================================
# 5. واجهة المستخدم (UI)
# ==========================================

# جلب البيانات
all_items = get_cached_checklists()

# استخراج العناوين الرئيسية الموجودة لترتيبها في القائمة
if all_items:
    existing_main_titles = sorted(list(set([i.main_title for i in all_items if i.main_title])))
else:
    existing_main_titles = []

# --- القائمة الجانبية (للإدارة والإضافة) ---
if is_admin:
    with st.sidebar:
        st.header("⚙️ إدارة القوائم")
        st.info("يمكنك إضافة مهام جديدة أو أقسام جديدة من هنا.")
        
        with st.expander("➕ إضافة بند جديد", expanded=True):
            with st.form("smart_add_form", clear_on_submit=True):
                # خيار ذكي: إما اختيار قسم موجود أو إنشاء جديد
                select_options = ["✨ قسم جديد..."] + existing_main_titles
                selected_main = st.selectbox("القسم الرئيسي:", select_options)
                
                new_main_title = None
                if selected_main == "✨ قسم جديد...":
                    new_main_title = st.text_input("اكتب اسم القسم الجديد:")
                
                # العنوان الفرعي (اختياري)
                sub_title = st.text_input("العنوان الفرعي (اختياري):")
                
                # اسم المهمة
                item_name = st.text_input("نص المهمة / البند:", placeholder="مثال: مراجعة التقرير الشهري")
                
                submitted = st.form_submit_button("إضافة", use_container_width=True)
                
                if submitted:
                    final_main = new_main_title if (selected_main == "✨ قسم جديد...") else selected_main
                    
                    if not final_main or not item_name:
                        st.error("يرجى تحديد القسم واسم المهمة!")
                    else:
                        ChecklistModel.add_item(
                            main_title=final_main,
                            sub_title=sub_title if sub_title else "",
                            item_name=item_name,
                            created_by=user.name
                        )
                        st.toast("✅ تمت الإضافة بنجاح!")
                        clear_checklist_cache()
                        time.sleep(1)
                        st.rerun()

# --- العرض الرئيسي ---
st.title("📋 قوائم المهام والنماذج")
st.markdown("---")

if not all_items:
    st.info("📭 لا توجد قوائم مهام حالياً. يمكن للمسؤولين إضافة بنود جديدة من القائمة الجانبية.")
else:
    # تجميع البيانات حسب العنوان الرئيسي
    grouped_data = {}
    for item in all_items:
        if item.main_title not in grouped_data:
            grouped_data[item.main_title] = []
        grouped_data[item.main_title].append(item)
    
    # عرض البيانات
    for main_title, items in grouped_data.items():
        with st.expander(f"📌 {main_title}", expanded=True):
            
            # فصل العناصر المنجزة عن غير المنجزة
            unchecked_items = [i for i in items if not i.is_checked]
            checked_items = [i for i in items if i.is_checked]
            
            # 1. عرض العناصر غير المنجزة (To-Do)
            for item in unchecked_items:
                c1, c2 = st.columns([0.5, 11])
                with c1:
                    # Checkbox عادي
                    is_done = st.checkbox(
                        "done", 
                        value=False, 
                        key=f"check_{item.item_id}", 
                        label_visibility="collapsed"
                    )
                    
                    if is_done: # إذا ضغط المستخدم عليه
                        toggle_item_status(item.item_id, False) # False تعني الحالة الحالية كانت False
                        st.rerun()
                        
                with c2:
                    # عرض النص بشكل عادي
                    if item.sub_title:
                        st.markdown(f"**{item.sub_title}:** {item.item_name}")
                    else:
                        st.write(item.item_name)

            # 2. عرض العناصر المنجزة (Done) بستايل خاص
            if checked_items:
                if unchecked_items: 
                    st.divider() # فاصل جمالي إذا كان هناك عناصر مختلطة
                
                for item in checked_items:
                    c1, c2, c3 = st.columns([0.5, 10.5, 1])
                    with c1:
                        # Checkbox للتراجع (Undo)
                        undo = st.checkbox(
                            "undone", 
                            value=True, 
                            key=f"check_{item.item_id}", 
                            label_visibility="collapsed"
                        )
                        if not undo: # إذا أزال الصح
                            toggle_item_status(item.item_id, True)
                            st.rerun()
                            
                    with c2:
                        # 🔥 الستايل المظلل (كما طلبته)
                        # تم تحسين الـ CSS قليلاً ليكون متجاوباً
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #f0f2f6; 
                                color: #888; 
                                padding: 8px 12px; 
                                border-radius: 8px; 
                                border: 1px solid #e0e0e0;
                                text-decoration: line-through;
                                display: flex;
                                align-items: center;
                            ">
                                ✅ {item.item_name}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    # زر الحذف (للأدمن فقط)
                    with c3:
                        if is_admin:
                            if st.button("🗑", key=f"del_{item.item_id}", help="حذف هذا البند"):
                                ChecklistModel.delete_item(item.item_id)
                                st.toast("تم الحذف")
                                clear_checklist_cache()
                                time.sleep(0.5)
                                st.rerun()
