import streamlit as st
import time
from models.checklist_model import ChecklistModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from utils.formatting import apply_custom_style

# 1. إعداد الصفحة
st.set_page_config(page_title="القوائم والنماذج", page_icon="☑️", layout="wide")


import streamlit as st
import time # <--- مهم جداً للتأخير البسيط قبل الطرد
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR

# ... (بعد set_page_config) ...

user = get_current_user()

# قائمة الأدوار المسموح لها بدخول هذه الصفحة (عدلها حسب كل صفحة)
# مثلاً صفحة المستخدمين والإعدادات: [ROLE_SUPER_ADMIN, ROLE_ADMIN]
# صفحة رفع الوسائط: [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR]
ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN] 

if not user or user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ عذراً، ليس لديك صلاحية لدخول هذه الصفحة! جارِ تحويلك...", icon="🚫")
    time.sleep(1.5) # انتظار ثانية ونصف ليقرأ الرسالة
    st.switch_page("app.py") # الطرد إلى الصفحة الرئيسية



user = get_current_user()
if not user:
    st.toast("🔒 سجل دخولك أولاً")
    time.sleep(1)
    st.switch_page("app.py")

apply_custom_style()

# الصلاحيات
is_admin = user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# --- دوال مساعدة ---
def toggle_item(item_id, current_status):
    """دالة يتم استدعاؤها عند ضغط التشيك بوكس"""
    ChecklistModel.toggle_status(item_id, current_status)
    # مسح الكاش لإعادة تحميل البيانات الجديدة فوراً
    st.cache_resource.clear()
    st.rerun()

# ==========================================
# 1. واجهة الإدارة (إضافة بنود جديدة)
# ==========================================
if is_admin:
    with st.sidebar:
        st.header("⚙️ إدارة القوائم")
        with st.expander("➕ إضافة بند جديد", expanded=False):
            with st.form("add_checklist_item"):
                main_t = st.text_input("العنوان الرئيسي (مثال: بقالة)")
                sub_t = st.text_input("العنوان الفرعي (مثال: حلى)")
                i_name = st.text_input("اسم البند (مثال: كيك)")
                
                if st.form_submit_button("إضافة"):
                    if main_t and sub_t and i_name:
                        ChecklistModel.add_item(main_t, sub_t, i_name, user.name)
                        st.cache_resource.clear() # تحديث البيانات
                        st.success("تمت الإضافة!")
                        st.rerun()
                    else:
                        st.error("جميع الحقول مطلوبة")
        st.divider()

# ==========================================
# 2. عرض القوائم (الفرز الذكي)
# ==========================================

# جلب كل البيانات
all_items = ChecklistModel.get_all_items()

if not all_items:
    st.info("القائمة فارغة، أضف بنوداً جديدة من القائمة الجانبية.")
    st.stop()

# استخراج العناوين الرئيسية الفريدة لعمل التبويبات
# نستخدم set لمنع التكرار ثم list للترتيب
main_titles = sorted(list(set([item.main_title for item in all_items])))

# إنشاء التبويبات الرئيسية (Tabs)
tabs = st.tabs(main_titles)

for i, main_title in enumerate(main_titles):
    with tabs[i]:
        # نفلتر البنود الخاصة بهذا التبويب فقط
        section_items = [x for x in all_items if x.main_title == main_title]
        
        # استخراج العناوين الفرعية داخل هذا القسم
        sub_titles = sorted(list(set([item.sub_title for item in section_items])))
        
        # عرض العناوين الفرعية
        for sub_title in sub_titles:
            # تصميم العنوان الفرعي
            st.markdown(f"### 🔸 {sub_title}")
            
            # فلترة البنود لهذا العنوان الفرعي
            my_items = [x for x in section_items if x.sub_title == sub_title]
            
            # --- الفرز السحري (Magic Sorting) ---
            # نفصل البنود إلى مجموعتين: غير مكتملة (فوق) ومكتملة (تحت)
            unchecked_items = [x for x in my_items if not x.is_checked]
            checked_items = [x for x in my_items if x.is_checked]
            
            # 1. عرض غير المكتمل (يظهر في الأعلى)
            for item in unchecked_items:
                c1, c2 = st.columns([0.5, 11])
                with c1:
                    # التشيك بوكس: عند تغييره يتم تحديث القاعدة فوراً
                    is_done = st.checkbox(
                        "done", 
                        value=False, 
                        key=f"check_{item.item_id}", 
                        label_visibility="collapsed",
                        on_change=toggle_item,
                        args=(item.item_id, False)
                    )
                with c2:
                    st.write(f"**{item.item_name}**")
                    # زر حذف صغير للمدير
                    if is_admin:
                         if st.button("🗑", key=f"del_{item.item_id}"):
                             ChecklistModel.delete_item(item.item_id)
                             st.cache_resource.clear()
                             st.rerun()

            # 2. عرض المكتمل (يظهر في الأسفل بلون باهت)
            if checked_items:
                if unchecked_items:
                    st.divider() # فاصل بين المجموعتين
                
                for item in checked_items:
                    c1, c2 = st.columns([0.5, 11])
                    with c1:
                        # هذا المربع معلم عليه صح مسبقاً
                        is_undone = st.checkbox(
                            "undone", 
                            value=True, 
                            key=f"check_{item.item_id}", 
                            label_visibility="collapsed",
                            on_change=toggle_item,
                            args=(item.item_id, True)
                        )
                    with c2:
                        # عرض النص مشطوباً للإشارة للانتهاء
                        st.markdown(f"~~{item.item_name}~~", help="تم الانتهاء منه")
                        if is_admin:
                             if st.button("🗑", key=f"del_{item.item_id}"):
                                 ChecklistModel.delete_item(item.item_id)
                                 st.cache_resource.clear()
                                 st.rerun()
            
            # مسافة بين كل قسم فرعي وآخر
            st.write("") 
            st.write("")
