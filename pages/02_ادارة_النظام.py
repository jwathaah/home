import streamlit as st
import pandas as pd
import time
import sys
import os

# ==========================================
# 1. إعداد المسارات والاستيراد
# ==========================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # استيراد الباك إند الموحد (الجوكر)
    import backend as bk
except ImportError as e:
    st.error(f"⚠️ خطأ في استيراد backend.py: {e}")
    st.stop()

# ==========================================
# 2. إعداد الصفحة والتحقق من الصلاحيات
# ==========================================
st.set_page_config(page_title="إدارة النظام", page_icon="⚙️", layout="wide")

# تطبيق التنسيق العام
bk.apply_custom_style()

# التحقق من المستخدم
user = bk.get_current_user()

if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# التحقق من الصلاحية (للمدراء فقط)
ALLOWED_ROLES = [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]
if user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ منطقة محظورة", icon="🚫")
    time.sleep(1)
    st.switch_page("app.py")

# عرض القائمة الجانبية الموحدة
bk.render_sidebar()

st.title("🛠️ لوحة التحكم وإدارة النظام")

# ==========================================
# 3. واجهة التحكم (Tabs)
# ==========================================
main_tabs = st.tabs(["👥 المستخدمين", "🔐 الصلاحيات", "⚙️ الإعدادات"])

# ==================================================
# TAB 1: إدارة المستخدمين
# ==================================================
with main_tabs[0]:
    st.header("إدارة المستخدمين")
    
    all_users = bk.UserModel.get_all_users()
    active_count = len([u for u in all_users if u.status == 'active'])
    
    # إحصائيات سريعة
    c1, c2, c3 = st.columns(3)
    c1.metric("العدد الكلي", len(all_users))
    c2.metric("النشطين", active_count)
    c3.metric("الموقوفين", len(all_users) - active_count)
    
    st.divider()
    
    # تبويبات داخلية
    u_tabs = st.tabs(["📋 القائمة والتعديل", "➕ إضافة عضو جديد"])
    
    with u_tabs[0]:
        # جدول العرض
        if all_users:
            data = [{"الاسم": u.name, "البريد": u.email, "الدور": u.role_name, "الحالة": u.status} for u in all_users]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            
            st.subheader("تعديل بيانات مستخدم")
            user_opts = {f"{u.name} ({u.email})": u for u in all_users}
            
            sel_lbl = st.selectbox("اختر للتعديل:", list(user_opts.keys()), key="u_sel")
            sel_u = user_opts[sel_lbl]
            
            # حماية المدير العام
            if sel_u.role_id == bk.ROLE_SUPER_ADMIN and (user.user_id != sel_u.user_id):
                st.warning("لا يمكن تعديل المدير العام.")
            else:
                with st.expander(f"تعديل: {sel_u.name}", expanded=True):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        ns = st.selectbox("الحالة", ["active", "inactive"], index=0 if sel_u.status=="active" else 1, key="u_st")
                        if st.button("تحديث الحالة", key="btn_upd"):
                            bk.UserModel.update_user_status(sel_u.user_id, ns)
                            st.success("تم التحديث")
                            time.sleep(0.5)
                            st.rerun()
                    with ec2:
                        st.write("⚠️ منطقة الخطر")
                        if st.button("حذف نهائي", type="primary", key="btn_del"):
                            bk.UserModel.delete_user(sel_u.user_id)
                            st.warning("تم الحذف")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("لا يوجد مستخدمين حالياً.")

    with u_tabs[1]:
        st.subheader("إضافة عضو")
        with st.form("new_u"):
            n1, n2 = st.columns(2)
            nm = n1.text_input("الاسم")
            em = n1.text_input("البريد")
            pw = n2.text_input("كلمة المرور", type="password")
            
            role_options = list(bk.ROLE_NAMES.values())
            rl = n2.selectbox("الدور", role_options)
            
            if st.form_submit_button("إضافة"):
                if nm and em and pw:
                    rid = {v: k for k, v in bk.ROLE_NAMES.items()}[rl]
                    ok, msg = bk.UserModel.create_user(nm, em, pw, rid)
                    if ok: 
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else: 
                        st.error(msg)
                else:
                    st.warning("يرجى تعبئة جميع الحقول.")

# ==================================================
# TAB 2: الصلاحيات
# ==================================================
with main_tabs[1]:
    st.header("توزيع الصلاحيات")
    
    targets = [u for u in all_users if u.role_id != bk.ROLE_SUPER_ADMIN]
    
    if not targets:
        st.info("لا يوجد مستخدمين لتعديل صلاحياتهم.")
    else:
        p_opts = {f"{u.name} ({u.email})": u for u in targets}
        p_lbl = st.selectbox("👤 اختر المستخدم:", list(p_opts.keys()), key="p_sel")
        p_user = p_opts[p_lbl]
        
        st.info(f"جاري تعديل صلاحيات: **{p_user.name}**")
        
        curr_perms = bk.PermissionModel.get_permissions_by_user(p_user.user_id)
        
        def find_p(sid, tid=""):
            for p in curr_perms:
                if str(p.section_id) == str(sid) and str(p.tab_id) == str(tid): return p
            return None
            
        all_secs = bk.SectionModel.get_all_sections()
        
        if not all_secs:
            st.warning("يجب إضافة أقسام أولاً لتوزيع الصلاحيات.")
        else:
            with st.form("perm_form"):
                h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
                h1.write("**الهيكل**"); h2.write("**عرض**"); h3.write("**تعديل**"); h4.write("**حجب**")
                st.markdown("---")
                
                for sec in all_secs:
                    ps = find_p(sec.section_id)
                    sc1, sc2, sc3, sc4 = st.columns([3, 1, 1, 1])
                    sc1.markdown(f"### {sec.name}")
                    
                    # استخدام المفاتيح لحفظ الحالة وقراءتها لاحقاً
                    sc2.checkbox("", value=ps.view if ps else False, key=f"k_sv_{sec.section_id}")
                    sc3.checkbox("", value=ps.edit if ps else False, key=f"k_se_{sec.section_id}")
                    sc4.checkbox("", value=ps.hidden if ps else False, key=f"k_sh_{sec.section_id}")
                    
                    tabs = bk.TabModel.get_tabs_by_section(sec.section_id)
                    if tabs:
                        st.caption(f"└ تبويبات {sec.name}")
                        for tab in tabs:
                            pt = find_p(sec.section_id, tab.tab_id)
                            tc1, tc2, tc3, tc4 = st.columns([3, 1, 1, 1])
                            tc1.text(f"  📄 {tab.name}")
                            tc2.checkbox("", value=pt.view if pt else False, key=f"k_tv_{tab.tab_id}")
                            tc3.checkbox("", value=pt.edit if pt else False, key=f"k_te_{tab.tab_id}")
                            tc4.checkbox("", value=pt.hidden if pt else False, key=f"k_th_{tab.tab_id}")
                    st.divider()
            
                if st.form_submit_button("💾 حفظ وتحديث الصلاحيات"):
                    for sec in all_secs:
                        # قراءة القيم مباشرة من st.session_state باستخدام المفاتيح
                        bk.PermissionModel.grant_permission(
                            p_user.user_id, sid=sec.section_id, 
                            view=st.session_state.get(f"k_sv_{sec.section_id}", False), 
                            edit=st.session_state.get(f"k_se_{sec.section_id}", False), 
                            hidden=st.session_state.get(f"k_sh_{sec.section_id}", False)
                        )
                        for tab in bk.TabModel.get_tabs_by_section(sec.section_id):
                            bk.PermissionModel.grant_permission(
                                p_user.user_id, sid=sec.section_id, tid=tab.tab_id,
                                view=st.session_state.get(f"k_tv_{tab.tab_id}", False), 
                                edit=st.session_state.get(f"k_te_{tab.tab_id}", False), 
                                hidden=st.session_state.get(f"k_th_{tab.tab_id}", False)
                            )
                    st.success("✅ تم تحديث الصلاحيات بنجاح!")
                    time.sleep(1)
                    st.rerun()

# ==================================================
# TAB 3: الإعدادات
# ==================================================
with main_tabs[2]:
    st.header("إعدادات الموقع")
    
    current_user_name = user.name
    bk.SettingModel.initialize_defaults(current_user_name)
    sett = bk.SettingModel.get_all_settings()
    
    def gv(k): return sett[k].value if k in sett else ""
    
    with st.form("set_form"):
        sc1, sc2 = st.columns(2)
        with sc1:
            tit = st.text_input("اسم الموقع", gv("site_title"))
            ann = st.text_area("شريط إعلانات", gv("announcement_bar"))
        with sc2:
            sta = st.radio("حالة النظام", ["active", "maintenance"], index=0 if gv("system_status")=="active" else 1)
            gst = st.checkbox("السماح للزوار بالتصفح", value=gv("allow_guest_view")=="True")
        
        st.write("")
        if st.form_submit_button("حفظ الإعدادات"):
            bk.SettingModel.update_setting("site_title", tit, current_user_name)
            bk.SettingModel.update_setting("announcement_bar", ann, current_user_name)
            bk.SettingModel.update_setting("system_status", sta, current_user_name)
            bk.SettingModel.update_setting("allow_guest_view", str(gst), current_user_name)
            st.success("تم التحديث")
            time.sleep(1)
            st.rerun()
