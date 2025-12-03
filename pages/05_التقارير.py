import streamlit as st
import pandas as pd
from models.activity_log_model import ActivityLogModel
from models.user_model import UserModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# 1. إعداد الصفحة
st.set_page_config(page_title="التقارير وسجل النشاط", page_icon="📊", layout="wide")


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
# التحقق من الصلاحيات (للمدراء فقط)
if not user or user.role_id not in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
    st.warning("⛔ هذه الصفحة مخصصة للمسؤولين فقط.")
    st.stop()

from ui.layout import render_sidebar
render_sidebar()

st.title("📊 سجل النشاطات والتقارير")
st.markdown("مراقبة حركات النظام وتصرفات المستخدمين.")
st.divider()

# 2. عرض سجل النشاط (Activity Log)
st.subheader("🕵️ سجل العمليات الأخيرة")

logs = ActivityLogModel.get_all_logs()

if not logs:
    st.info("سجل النشاط فارغ حالياً.")
else:
    # تحويل البيانات إلى DataFrame للعرض
    # نحتاج أولاً جلب أسماء المستخدمين لأن السجل يحفظ الـ ID فقط
    all_users = UserModel.get_all_users()
    user_map = {u.user_id: u.name for u in all_users}

    data = []
    for log in logs:
        # استبدال ID بالاسم إذا وجد
        user_name = user_map.get(log.user_id, log.user_id)
        
        data.append({
            "الوقت": log.time,
            "المستخدم": user_name,
            "الحدث": log.action,
            "التفاصيل": log.details,
            "نوع الهدف": log.target_type
        })
    
    df = pd.DataFrame(data)
    
    # أدوات تصفية (Filters)
    with st.expander("🔍 أدوات التصفية", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            filter_user = st.multiselect("تصفية حسب المستخدم", options=df["المستخدم"].unique())
        with col2:
            filter_action = st.multiselect("تصفية حسب نوع الحدث", options=df["الحدث"].unique())
    
    # تطبيق التصفية
    if filter_user:
        df = df[df["المستخدم"].isin(filter_user)]
    if filter_action:
        df = df[df["الحدث"].isin(filter_action)]

    # عرض الجدول
    st.dataframe(df, use_container_width=True, height=400)
    
    # زر تحميل التقرير
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 تصدير السجل (Excel/CSV)",
        data=csv,
        file_name="activity_log.csv",
        mime="text/csv",
        type="primary"
    )

# 3. إحصائيات عامة
st.divider()
st.subheader("📈 إحصائيات سريعة")
c1, c2, c3 = st.columns(3)
c1.metric("إجمالي العمليات المسجلة", len(logs))
c2.metric("عدد المستخدمين النشطين في السجل", len(df["المستخدم"].unique()))
# c3.metric("آخر نشاط", logs[0].time if logs else "-")
