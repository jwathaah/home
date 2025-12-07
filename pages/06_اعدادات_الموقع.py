import streamlit as st
import pandas as pd
import time
from backend import (
    UserModel, SectionModel, TabModel, PermissionModel, SettingModel,
    ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_NAMES
)
from frontend import get_current_user, render_navbar, apply_custom_style

# 1. إعداد الصفحة
st.set_page_config(page_title="إدارة النظام", page_icon="⚙️", layout="wide")

user = get_current_user()
# التحقق من الصلاحية (للمدراء فقط)
if not user or user.role_id not in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
    st.toast("⛔ منطقة محظورة", icon="🚫")
    time.sleep(1)
    st.switch_page("app.py")

render_navbar("pages/02_ادارة_النظام.py")
apply_custom_style()

st.title("🛠️ لوحة التحكم وإدارة النظام")

# تقسيم الصفحة لـ 3 تبويبات رئيسية
main_tabs = st.tabs(["👥 المستخدمين", "🔐 الصلاحيات", "⚙️ الإعدادات"])

# ==================================================
# TAB 1: إدارة المستخدمين
# ==================================================
with main_tabs[0]:
    st.header("إدارة المستخدمين")
    
    all_users = UserModel.get_all_users()
    active_count = len([u for u in all_users if u.status == 'active'])
    
    # إحصائيات سريعة
    c1, c2, c3 = st.columns(3)
    c1.metric("العدد الكلي", len(all_users))
    c2.metric("النشطين", active_count)
    c3.metric("الموقوفين", len(all_users) - active_count)
    
    st.divider()
    
    # تبويبات داخلية (قائمة / إضافة)
    u_tabs = st.tabs(["📋 القائمة والتعديل", "➕ إضافة عضو جديد"])
    
    with u_tabs[0]:
        # جدول العرض
        data = [{"الاسم": u.name, "البريد": u.email, "الدور": u.role_name, "الحالة": u.status} for u in all_users]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        
        st.subheader("تعديل بيانات مستخدم")
        user_opts = {f"{u.name} ({u.email})": u for u in all_users}
        if user_opts:
            sel_lbl = st.selectbox("اختر للتعديل:", list(user_opts.keys()), key="u_sel")
            sel_u = user_opts[sel_lbl]
            
            # حماية المدير العام
            if sel_u.role_id == ROLE_SUPER_ADMIN and user.user_id != sel_u.user_id:
                st.warning("لا يمكن تعديل المدير العام.")
            else:
                with st.expander(f"تعديل: {sel_u.name}", expanded=True):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        ns = st.selectbox("الحالة", ["active", "inactive"], index=0 if sel_u.status=="active" else 1, key="u_st")
                        if st.button("تحديث الحالة", key="btn_upd"):
                            UserModel.update_user_status(sel_u.user_id, ns)
                            st.success("تم التحديث")
                            time.sleep(0.5)
                            st.rerun()
                    with ec2:
                        st.write("⚠️ منطقة الخطر")
                        if st.button("حذف نهائي", type="primary", key="btn_del"):
                            UserModel.delete_user(sel_u.user_id)
                            st.warning("تم الحذف")
                            time.sleep(1)
                            st.rerun()

    with u_tabs[1]:
        st.subheader("إضافة عضو")
        with st.form("new_u"):
            n1, n2 = st.columns(2)
            nm = n1.text_input("الاسم")
            em = n1.text_input("البريد")
            pw = n2.text_input("كلمة المرور", type="password")
            rl = n2.selectbox("الدور", list(ROLE_NAMES.values()))
            if st.form_submit_button("إضافة"):
                rid = {v: k for k, v in ROLE_NAMES.items()}[rl]
                ok, msg = UserModel.create_user(nm, em, pw, rid)
                if ok: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)

# ==================================================
# TAB 2: الصلاحيات
# ==================================================
with main_tabs[1]:
    st.header("توزيع الصلاحيات")
    
    # استثناء المدير العام من القائمة
    targets = [u for u in all_users if u.role_id != ROLE_SUPER_ADMIN]
    
    if not targets:
        st.info("لا يوجد مستخدمين لتعديل صلاحياتهم.")
    else:
        p_opts = {f"{u.name} ({u.email})": u for u in targets}
        p_lbl = st.selectbox("👤 اختر المستخدم:", list(p_opts.keys()), key="p_sel")
        p_user = p_opts[p_lbl]
        
        st.info(f"جاري تعديل صلاحيات: **{p_user.name}**")
        
        # جلب الصلاحيات الحالية
        curr_perms = PermissionModel.get_permissions_by_user(p_user.user_id)
        def find_p(sid, tid=""):
            for p in curr_perms:
                if p.section_id == str(sid) and p.tab_id == str(tid): return p
            return None
            
        all_secs = SectionModel.get_all_sections()
        
        with st.form("perm_form"):
            h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
            h1.write("**الهيكل**"); h2.write("**عرض**"); h3.write("**تعديل**"); h4.write("**حجب**")
            st.markdown("---")
            
            for sec in all_secs:
                ps = find_p(sec.section_id)
                sc1, sc2, sc3, sc4 = st.columns([3, 1, 1, 1])
                sc1.markdown(f"### {sec.name}")
                # نستخدم مفاتيح فريدة لكل مربع اختيار
                st.session_state[f"sv_{sec.section_id}"] = sc2.checkbox("", value=ps.view if ps else False, key=f"k_sv_{sec.section_id}")
                st.session_state[f"se_{sec.section_id}"] = sc3.checkbox("", value=ps.edit if ps else False, key=f"k_se_{sec.section_id}")
                st.session_state[f"sh_{sec.section_id}"] = sc4.checkbox("", value=ps.hidden if ps else False, key=f"k_sh_{sec.section_id}")
                
                tabs = TabModel.get_tabs_by_section(sec.section_id)
                if tabs:
                    st.caption(f"└ تبويبات {sec.name}")
                    for tab in tabs:
                        pt = find_p(sec.section_id, tab.tab_id)
                        tc1, tc2, tc3, tc4 = st.columns([3, 1, 1, 1])
                        tc1.text(f"  📄 {tab.name}")
                        st.session_state[f"tv_{tab.tab_id}"] = tc2.checkbox("", value=pt.view if pt else False, key=f"k_tv_{tab.tab_id}")
                        st.session_state[f"te_{tab.tab_id}"] = tc3.checkbox("", value=pt.edit if pt else False, key=f"k_te_{tab.tab_id}")
                        st.session_state[f"th_{tab.tab_id}"] = tc4.checkbox("", value=pt.hidden if pt else False, key=f"k_th_{tab.tab_id}")
                st.divider()
            
            if st.form_submit_button("💾 حفظ وتحديث الصلاحيات"):
                for sec in all_secs:
                    PermissionModel.grant_permission(
                        p_user.user_id, sid=sec.section_id, 
                        view=st.session_state[f"sv_{sec.section_id}"], 
                        edit=st.session_state[f"se_{sec.section_id}"], 
                        hidden=st.session_state[f"sh_{sec.section_id}"]
                    )
                    for tab in TabModel.get_tabs_by_section(sec.section_id):
                        PermissionModel.grant_permission(
                            p_user.user_id, sid=sec.section_id, tid=tab.tab_id,
                            view=st.session_state[f"tv_{tab.tab_id}"], 
                            edit=st.session_state[f"te_{tab.tab_id}"], 
                            hidden=st.session_state[f"th_{tab.tab_id}"]
                        )
                st.success("✅ تم تحديث الصلاحيات بنجاح!")
                time.sleep(1)
                st.rerun()

# ==================================================
# TAB 3: الإعدادات
# ==================================================
with main_tabs[2]:
    st.header("إعدادات الموقع")
    
    SettingModel.initialize_defaults(user.name)
    sett = SettingModel.get_all_settings()
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
            SettingModel.update_setting("site_title", tit, user.name)
            SettingModel.update_setting("announcement_bar", ann, user.name)
            SettingModel.update_setting("system_status", sta, user.name)
            SettingModel.update_setting("allow_guest_view", str(gst), user.name)
            st.success("تم التحديث")
            time.sleep(1)
            st.rerun()
