import streamlit as st
import pandas as pd
import plotly.express as px
import time
from services.google_sheets import get_data
from core.constants import (
    TABLE_USERS, TABLE_CONTENT, TABLE_ACTIVITY_LOG, 
    ROLE_SUPER_ADMIN, ROLE_ADMIN, TABLE_SECTIONS
)
from core.auth import get_current_user
from utils.formatting import apply_custom_style

# 1. إعداد الصفحة
st.set_page_config(page_title="التقارير والإحصائيات", page_icon="📊", layout="wide")

user = get_current_user()

# 2. التحقق من الصلاحيات (للمدراء فقط)
ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN]
if not user or user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ عذراً، هذه الصفحة للمدراء فقط!", icon="🚫")
    time.sleep(1.5)
    st.switch_page("app.py")

apply_custom_style()

st.title("📊 التقارير والإحصائيات العامة")
st.markdown("---")

# ==========================================
# 1. جلب البيانات (Data Fetching)
# ==========================================
with st.spinner("جاري جلب أحدث البيانات..."):
    # جلب الجداول الرئيسية
    df_users = get_data(TABLE_USERS)
    df_content = get_data(TABLE_CONTENT)
    df_sections = get_data(TABLE_SECTIONS)
    df_activity = get_data(TABLE_ACTIVITY_LOG) # هذا هو الجدول المفقود سابقاً

# ==========================================
# 2. بطاقات الأرقام القياسية (Metrics)
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_users = len(df_users) if not df_users.empty else 0
    st.metric("👥 إجمالي المستخدمين", total_users)

with col2:
    total_content = len(df_content) if not df_content.empty else 0
    st.metric("📝 إجمالي المحتوى", total_content)

with col3:
    total_sections = len(df_sections) if not df_sections.empty else 0
    st.metric("📂 عدد الأقسام", total_sections)

with col4:
    total_activities = len(df_activity) if not df_activity.empty else 0
    st.metric("⚡ حركات السجل", total_activities)

st.markdown("---")

# ==========================================
# 3. الرسوم البيانية (Charts)
# ==========================================

c1, c2 = st.columns(2)

# الرسم البياني 1: توزيع المستخدمين حسب الصلاحية
with c1:
    st.subheader("توزيع المستخدمين")
    if not df_users.empty and 'role_id' in df_users.columns:
        # تحويل أرقام الصلاحيات إلى أسماء للعرض
        from core.constants import ROLE_NAMES
        # إنشاء نسخة لتعديلها للعرض
        chart_users = df_users.copy()
        chart_users['role_name'] = chart_users['role_id'].map(lambda x: ROLE_NAMES.get(int(x), "غير معروف"))
        
        role_counts = chart_users['role_name'].value_counts().reset_index()
        role_counts.columns = ['الصلاحية', 'العدد']
        
        fig_roles = px.pie(role_counts, values='العدد', names='الصلاحية', hole=0.4)
        st.plotly_chart(fig_roles, use_container_width=True)
    else:
        st.info("لا توجد بيانات مستخدمين كافية.")

# الرسم البياني 2: المحتوى حسب النوع
with c2:
    st.subheader("المحتوى حسب النوع")
    if not df_content.empty and 'content_type' in df_content.columns:
        type_counts = df_content['content_type'].value_counts().reset_index()
        type_counts.columns = ['النوع', 'العدد']
        
        fig_content = px.bar(type_counts, x='النوع', y='العدد', color='العدد')
        st.plotly_chart(fig_content, use_container_width=True)
    else:
        st.info("لا يوجد محتوى لعرضه.")

st.markdown("---")

# ==========================================
# 4. سجل النشاطات (Activity Log) - مكان الخطأ السابق
# ==========================================
st.subheader("📋 آخر النشاطات في النظام")

if df_activity.empty:
    st.info("سجل النشاطات فارغ حالياً.")
else:
    # 1. تعريف df لتصحيح الخطأ (NameError)
    df = df_activity.copy()
    
    # 2. التأكد من وجود الأعمدة المتوقعة (لتجنب KeyError)
    # نفترض أن الأعمدة في قوقل شيت هي: activity_id, user_name, action, details, timestamp
    # سنقوم بإعادة تسميتها للعربية للعرض الجميل
    
    # خريطة تغيير الأسماء (عدلها حسب أسماء الأعمدة الإنجليزية في ملفك)
    rename_map = {
        "user_name": "المستخدم",
        "action": "الحدث",
        "details": "التفاصيل",
        "timestamp": "التوقيت"
    }
    
    # إعادة التسمية للعرض فقط
    df_display = df.rename(columns=rename_map)
    
    # التأكد من وجود عمود "المستخدم" قبل الحساب
    if "المستخدم" in df_display.columns:
        active_users_count = len(df_display["المستخدم"].unique())
    elif "user_name" in df.columns: # محاولة بديلة
        active_users_count = len(df["user_name"].unique())
    else:
        active_users_count = 0

    # عرض إحصائية سريعة للسجل
    k1, k2 = st.columns(2)
    k1.metric("عدد المستخدمين النشطين في السجل", active_users_count)
    
    # عرض الجدول
    # نختار الأعمدة المهمة فقط للعرض إذا كانت موجودة
    cols_to_show = [c for c in ["المستخدم", "الحدث", "التفاصيل", "التوقيت"] if c in df_display.columns]
    
    if cols_to_show:
        st.dataframe(
            df_display[cols_to_show].sort_values(by="التوقيت", ascending=False), # ترتيب من الأحدث للأقدم
            use_container_width=True,
            hide_index=True
        )
    else:
        # عرض الجدول الخام إذا لم تتطابق الأسماء
        st.dataframe(df, use_container_width=True)
