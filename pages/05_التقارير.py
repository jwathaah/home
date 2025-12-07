import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import sys
import os

# ==========================================
# 1. إعداد المسارات والاستيراد
# ==========================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from backend import (
        UserModel, SectionModel, ContentModel, ChecklistModel,
        ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_NAMES,
        get_data, TABLE_CONTENT  # استيراد دالة جلب البيانات المباشرة
    )
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد من backend: {e}")
    st.stop()

# --- دوال احتياطية (Fallback) ---
try:
    from core.auth import get_current_user
except ImportError:
    def get_current_user():
        if 'user' in st.session_state:
            return st.session_state['user']
        return None

try:
    from utils.formatting import apply_custom_style
except ImportError:
    def apply_custom_style():
        # تنسيق بسيط
        st.markdown("""
        <style>
            .stApp { direction: rtl; }
            .stMarkdown, .stText, .stHeader, .stSubheader, p, div { text-align: right; }
            .stMetric { text-align: right; }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="التقارير والإحصائيات", page_icon="📊", layout="wide")

# ==========================================
# 3. التحقق من الصلاحيات
# ==========================================
user = get_current_user()
ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# التحقق (يمكن تفعيله بإلغاء التعليق)
# if not user:
#    st.warning("🔒 يجب تسجيل الدخول أولاً!")
#    st.stop()

if user and user.role_id not in ALLOWED_ROLES:
    st.warning("⛔ هذه الصفحة مخصصة للمدراء فقط.")
    time.sleep(2)
    st.switch_page("app.py")

# تطبيق التنسيق
apply_custom_style()

# ==========================================
# 4. معالجة البيانات (Data Processing)
# ==========================================

@st.cache_data(ttl=300) # كاش لمدة 5 دقائق
def get_analytics_data():
    """جلب وتجهيز جميع البيانات للتحليل"""
    
    # 1. بيانات المستخدمين
    # ملاحظة: نستخدم try-except لضمان عدم توقف الصفحة إذا كان الجدول فارغاً
    try:
        users = UserModel.get_all_users()
        df_users = pd.DataFrame([vars(u) for u in users])
    except Exception as e:
        st.error(f"خطأ في جلب المستخدمين: {e}")
        df_users = pd.DataFrame()
    
    # 2. بيانات المحتوى
    # نستخدم get_data مباشرة لجلب الجدول كاملاً لأن ContentModel قد لا يملك دالة get_all
    try:
        df_content = get_data(TABLE_CONTENT)
    except Exception:
        df_content = pd.DataFrame(columns=["title", "category_id", "created_by", "created_at"])

    # 3. بيانات القوائم (Checklists)
    try:
        checklists = ChecklistModel.get_all_items()
        df_checklists = pd.DataFrame([vars(i) for i in checklists])
    except Exception:
        df_checklists = pd.DataFrame()

    return df_users, df_content, df_checklists

def convert_df_to_csv(df):
    """دالة مساعدة لتحميل البيانات"""
    return df.to_csv(index=False).encode('utf-8')

# ==========================================
# 5. واجهة المستخدم (UI)
# ==========================================

st.title("📊 التقارير وتحليل البيانات")
st.markdown("---")

# زر تحديث البيانات
if st.button("🔄 تحديث البيانات الآن"):
    st.cache_data.clear()
    st.rerun()

# جلب البيانات
df_users, df_content, df_checklists = get_analytics_data()

# --- نظرة عامة (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👥 إجمالي المستخدمين", len(df_users))
with col2:
    if not df_users.empty and 'status' in df_users.columns:
        active_users = len(df_users[df_users['status'] == 'active'])
    else:
        active_users = 0
    st.metric("🟢 المستخدمين النشطين", active_users)
with col3:
    st.metric("📝 إجمالي المقالات/المحتوى", len(df_content))
with col4:
    if not df_checklists.empty and 'is_checked' in df_checklists.columns:
        # التأكد من تحويل القيم إلى Boolean للمقارنة الصحيحة
        completed_tasks = len(df_checklists[df_checklists['is_checked'].astype(str).str.upper() == 'TRUE'])
        total_tasks = len(df_checklists)
        percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    else:
        percent = 0
    st.metric("✅ نسبة إنجاز المهام", f"{percent}%")

st.markdown("---")

# --- التبويبات التفصيلية ---
tabs = st.tabs(["👥 تحليل المستخدمين", "📝 تحليل المحتوى", "✅ متابعة المهام"])

# ----------------------------------------
# TAB 1: تحليل المستخدمين
# ----------------------------------------
with tabs[0]:
    st.header("توزيع المستخدمين")
    
    if not df_users.empty:
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # خريطة توزيع الأدوار (Pie Chart)
            if 'role_id' in df_users.columns:
                df_users['role_name'] = df_users['role_id'].map(ROLE_NAMES)
                fig_roles = px.pie(df_users, names='role_name', title='توزيع المستخدمين حسب الصلاحيات')
                st.plotly_chart(fig_roles, use_container_width=True)
            
        with c2:
            st.subheader("تحميل بيانات المستخدمين")
            st.write("يمكنك تحميل قائمة المستخدمين الكاملة بصيغة CSV.")
            csv_users = convert_df_to_csv(df_users)
            st.download_button(
                "📥 تحميل القائمة (CSV)",
                csv_users,
                "users_report.csv",
                "text/csv",
                key='download-users'
            )
            
            st.subheader("📋 آخر المسجلين")
            if 'created_at' in df_users.columns:
                cols_to_show = ['name', 'email', 'role_name', 'status', 'created_at']
                # تصفية الأعمدة الموجودة فقط لتجنب الأخطاء
                valid_cols = [c for c in cols_to_show if c in df_users.columns]
                st.dataframe(
                    df_users[valid_cols].tail(5),
                    use_container_width=True
                )
    else:
        st.info("لا توجد بيانات مستخدمين للعرض.")

# ----------------------------------------
# TAB 2: تحليل المحتوى
# ----------------------------------------
with tabs[1]:
    st.header("أداء المحتوى")
    
    if not df_content.empty:
        # الرسم البياني: عدد المشاركات لكل كاتب
        if 'created_by' in df_content.columns:
            st.subheader("📊 أكثر الأعضاء نشاطاً (نشراً للمحتوى)")
            author_counts = df_content['created_by'].value_counts().reset_index()
            author_counts.columns = ['الكاتب', 'عدد المشاركات']
            
            fig_content = px.bar(author_counts, x='الكاتب', y='عدد المشاركات', color='عدد المشاركات')
            st.plotly_chart(fig_content, use_container_width=True)
        
        # جدول البيانات
        with st.expander("عرض سجل المحتوى كاملاً"):
            st.dataframe(df_content, use_container_width=True)
    else:
        st.info("لا يوجد محتوى مضاف حتى الآن.")

# ----------------------------------------
# TAB 3: متابعة المهام (Checklists)
# ----------------------------------------
with tabs[2]:
    st.header("تقدم العمل في القوائم")
    
    if not df_checklists.empty and 'is_checked' in df_checklists.columns:
        # توحيد نوع البيانات في العمود لضمان العد الصحيح
        # نفترض أن البيانات في الشيت قد تكون TRUE/FALSE (نص) أو 1/0 (رقم)
        df_checklists['status_bool'] = df_checklists['is_checked'].astype(str).str.upper() == 'TRUE'
        
        status_counts = df_checklists['status_bool'].value_counts().reset_index()
        status_counts.columns = ['الحالة', 'العدد']
        status_counts['الحالة'] = status_counts['الحالة'].map({True: 'منجز ✅', False: 'قيد الانتظار ⏳'})
        
        c1, c2 = st.columns(2)
        
        with c1:
            fig_tasks = px.pie(status_counts, names='الحالة', values='العدد', title='حالة المهام الكلية', hole=0.4)
            st.plotly_chart(fig_tasks, use_container_width=True)
            
        with c2:
            st.write("#### تفاصيل المهام غير المنجزة")
            pending = df_checklists[df_checklists['status_bool'] == False]
            if not pending.empty:
                cols_show = ['main_title', 'item_name', 'created_by']
                valid_cols = [c for c in cols_show if c in pending.columns]
                st.dataframe(pending[valid_cols], use_container_width=True)
            else:
                st.success("🎉 ممتاز! جميع المهام منجزة.")
    else:
        st.info("لا توجد قوائم مهام.")
