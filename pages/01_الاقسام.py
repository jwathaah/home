import streamlit as st
import streamlit.components.v1 as components
import time
import sys
import os
import re

# محاولة استيراد محرر النصوص
try:
    from streamlit_quill import st_quill
except ImportError:
    st_quill = None

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import backend as bk
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد من backend: {e}")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")
bk.apply_custom_style()

# ==========================================
# 3. التحقق من الصلاحيات
# ==========================================
user = bk.get_current_user()
if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# دوال الصلاحيات
def is_super_admin():
    return user and user.role_id == bk.ROLE_SUPER_ADMIN

def can_edit_structure():
    return user and user.role_id in [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]

def can_edit_content(section_id=None):
    if not user: return False
    if user.role_id in [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]: return True
    if user.role_id == bk.ROLE_SUPERVISOR:
        try:
            can_view, can_edit = bk.PermissionModel.check_access(user.user_id, section_id=section_id)
            return can_edit
        except: return False
    return False

# ==========================================
# دالة معالجة وعرض الروابط (The Fix)
# ==========================================
def smart_embed_link(link):
    if not link: return

    link = link.strip()
    
    # دالة مساعدة لإنشاء إطار بحجم الجوال
    def render_mobile_iframe(embed_url, platform_class="generic"):
        html_code = f"""
        <style>
            .video-container {{
                position: relative;
                width: 100%;
                /* نسبة العرض للارتفاع 9:16 (للجوال) - يمكن تعديلها */
                padding-bottom: 120%; 
                height: 0;
                overflow: hidden;
                border-radius: 12px;
                background-color: #000;
                border: 1px solid #ddd;
            }}
            .video-container iframe {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: 0;
            }}
        </style>
        <div class="video-container {platform_class}">
            <iframe src="{embed_url}" allowfullscreen allow="autoplay; encrypted-media"></iframe>
        </div>
        """
        # نستخدم height ثابت للـ component ليظهر المحتوى كاملاً
        components.html(html_code, height=600, scrolling=False)

    # ---------------------------------------
    # 1. معالجة روابط إنستقرام (Instagram)
    # ---------------------------------------
    if "instagram.com" in link:
        # نحتاج لتحويل الرابط إلى صيغة Embed
        # مثال: .../reel/xyz/ -> .../reel/xyz/embed/
        clean_link = link.split("?")[0] # حذف الباراميترات الزائدة
        if not clean_link.endswith("/"):
            clean_link += "/"
        
        if "/embed" not in clean_link:
            embed_url = clean_link + "embed"
        else:
            embed_url = clean_link
            
        render_mobile_iframe(embed_url, "instagram")

    # ---------------------------------------
    # 2. معالجة روابط يوتيوب (Shorts & Regular)
    # ---------------------------------------
    elif "youtube.com" in link or "youtu.be" in link:
        video_id = ""
        if "youtu.be" in link:
            video_id = link.split("/")[-1].split("?")[0]
        elif "shorts" in link:
            video_id = link.split("shorts/")[-1].split("?")[0]
        elif "v=" in link:
            video_id = link.split("v=")[-1].split("&")[0]
        
        if video_id:
            embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0&playsinline=1"
            # يوتيوب يعمل جيداً مع st.video لكن لتوحيد الشكل الطولي نستخدم iframe إذا كان شورتس
            if "shorts" in link:
                 render_mobile_iframe(embed_url, "youtube-shorts")
            else:
                 st.video(link) # الفيديوهات العرضية تبدو أفضل بالمشغل العادي

    # ---------------------------------------
    # 3. معالجة روابط تيك توك (TikTok)
    # ---------------------------------------
    elif "tiktok.com" in link:
        # تيك توك يحتاج في الغالب إلى معرف الفيديو
        # هذا حل تقريبي لأن تيك توك يمنع أحياناً التضمين البسيط
        # نستخدم مكتبة أو iframe مباشر من تيك توك
        parts = link.split("/video/")
        if len(parts) > 1:
            video_id = parts[1].split("?")[0]
            embed_url = f"https://www.tiktok.com/embed/v2/{video_id}"
            render_mobile_iframe(embed_url, "tiktok")
        else:
            # محاولة عرض الرابط كما هو إذا لم نتمكن من استخراج المعرف
            st.markdown(f"📺 **[فتح فيديو تيك توك في نافذة جديدة]({link})**")

    # ---------------------------------------
    # 4. معالجة روابط تويتر / X
    # ---------------------------------------
    elif "twitter.com" in link or "x.com" in link:
        try:
            components.html(f"""
            <blockquote class="twitter-tweet" data-media-max-width="560">
            <a href="{link}"></a>
            </blockquote> 
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
            """, height=600, scrolling=True)
        except:
            st.info(f"رابط تغريدة: {link}")

    # ---------------------------------------
    # 5. معالجة سناب شات (Snapchat)
    # ---------------------------------------
    elif "snapchat.com" in link:
        # روابط السناب تحتاج عادةً لزر تضمين خاص، لكن نجرب الـ iframe المباشر
        render_mobile_iframe(link, "snapchat")

    # ---------------------------------------
    # 6. روابط مباشرة (ملفات)
    # ---------------------------------------
    elif link.endswith(('.mp4', '.mov', '.avi', '.mp3', '.wav')):
        if link.endswith(('.mp3', '.wav')):
            st.audio(link)
        else:
            st.video(link)
            
    # ---------------------------------------
    # 7. افتراضي
    # ---------------------------------------
    else:
        st.markdown(f"🔗 [زيارة الرابط]({link})")


# ==========================================
# 4. واجهة المستخدم (التصميم الجديد)
# ==========================================

# عرض القائمة الجانبية (للتنقل بين الصفحات فقط)
bk.render_sidebar()

st.title("📂 تصفح الأقسام والمحتوى")

# ---------------------------------------------------------
# المستوى الأول: الأقسام الرئيسية (Tabs في أعلى الصفحة)
# ---------------------------------------------------------
sections = bk.SectionModel.get_all_sections()

if not sections:
    st.warning("لا توجد أقسام متاحة حالياً.")
    if can_edit_structure():
        with st.expander("➕ إضافة قسم جديد"):
            with st.form("add_sec_form"):
                n = st.text_input("اسم القسم")
                if st.form_submit_button("حفظ القسم"):
                    bk.SectionModel.create_section(n, user.name, True)
                    st.rerun()
else:
    # تحويل الأقسام إلى تبويبات علوية
    sec_names = [s.name for s in sections]
    
    # إضافة خيار لإضافة قسم جديد كـ Tab أخير للمشرفين
    if can_edit_structure():
        sec_names.append("➕ إضافة قسم")
        
    sec_tabs = st.tabs(sec_names)

    # التعامل مع كل قسم داخل التبويب الخاص به
    for i, section_name in enumerate(sec_names):
        with sec_tabs[i]:
            
            # --- حالة: إضافة قسم جديد ---
            if section_name == "➕ إضافة قسم":
                st.subheader("إضافة قسم رئيسي جديد")
                with st.form("new_sec_main"):
                    nn = st.text_input("اسم القسم")
                    if st.form_submit_button("إضافة"):
                        bk.SectionModel.create_section(nn, user.name, True)
                        st.success("تمت الإضافة")
                        time.sleep(1)
                        st.rerun()
                continue # نتجاوز باقي الكود لهذا التبويب

            # --- حالة: عرض قسم موجود ---
            current_section = sections[i]
            
            # ---------------------------------------------------------
            # المستوى الثاني: الأقسام الفرعية (التبويبات)
            # ---------------------------------------------------------
            sub_tabs_data = bk.TabModel.get_tabs_by_section(current_section.section_id)
            
            if not sub_tabs_data:
                st.info("لا توجد أقسام فرعية هنا.")
                if can_edit_structure():
                    with st.expander("➕ إضافة قسم فرعي (Tab)"):
                        with st.form(f"add_tab_{current_section.section_id}"):
                            tn = st.text_input("اسم القسم الفرعي")
                            if st.form_submit_button("إضافة"):
                                bk.TabModel.create_tab(current_section.section_id, tn, user.name)
                                st.rerun()
            else:
                sub_tab_names = [t.name for t in sub_tabs_data]
                if can_edit_structure():
                    sub_tab_names.append("➕ إضافة فرعي")
                
                # استخدام tabs داخلية
                inner_tabs = st.tabs(sub_tab_names)
                
                for j, sub_name in enumerate(sub_tab_names):
                    with inner_tabs[j]:
                        
                        # إضافة فرعي
                        if sub_name == "➕ إضافة فرعي":
                            with st.form(f"new_sub_{current_section.section_id}"):
                                tnn = st.text_input("اسم القسم الفرعي")
                                if st.form_submit_button("إضافة"):
                                    bk.TabModel.create_tab(current_section.section_id, tnn, user.name)
                                    st.rerun()
                            continue

                        current_tab = sub_tabs_data[j]
                        
                        # ---------------------------------------------------------
                        # المستوى الثالث: التصنيفات (Categories)
                        # ---------------------------------------------------------
                        categories = bk.CategoryModel.get_categories_by_tab(current_tab.tab_id)
                        
                        if not categories:
                            st.caption("لا توجد تصنيفات.")
                            if can_edit_structure():
                                with st.form(f"add_cat_{current_tab.tab_id}"):
                                    cn = st.text_input("اسم التصنيف الجديد")
                                    if st.form_submit_button("إضافة تصنيف"):
                                        bk.CategoryModel.create_category(current_tab.tab_id, cn, user.name)
                                        st.rerun()
                        else:
                            # عرض التصنيفات كتبويبات (مستوى ثالث)
                            cat_names = [c.name for c in categories]
                            if can_edit_structure():
                                cat_names.append("➕ تصنيف")
                            
                            cat_tabs_ui = st.tabs(cat_names)
                            
                            for k, cat_name in enumerate(cat_names):
                                with cat_tabs_ui[k]:
                                    
                                    # إضافة تصنيف
                                    if cat_name == "➕ تصنيف":
                                        with st.form(f"new_cat_form_{current_tab.tab_id}"):
                                            ncn = st.text_input("اسم التصنيف")
                                            if st.form_submit_button("إضافة"):
                                                bk.CategoryModel.create_category(current_tab.tab_id, ncn, user.name)
                                                st.rerun()
                                        continue

                                    current_cat = categories[k]
                                    
                                    # ---------------------------------------------------------
                                    # المحتوى (إضافة وعرض)
                                    # ---------------------------------------------------------
                                    
                                    # منطقة الإضافة
                                    if can_edit_content(current_section.section_id):
                                        with st.expander("✍️ نشر محتوى جديد", expanded=False):
                                            with st.form(f"add_content_{current_cat.category_id}"):
                                                ct_title = st.text_input("عنوان الموضوع")
                                                
                                                if st_quill:
                                                    ct_body = st_quill(placeholder="اكتب المحتوى هنا...", key=f"q_{current_cat.category_id}")
                                                else:
                                                    ct_body = st.text_area("المحتوى", key=f"a_{current_cat.category_id}")
                                                
                                                social_link = st.text_input("رابط (انستقرام، تيك توك، يوتيوب، سناب...)")
                                                st.caption("سيتم تكبير الفيديو تلقائياً ليناسب الجوال.")
                                                
                                                if st.form_submit_button("نشر"):
                                                    if ct_title:
                                                        bk.ContentModel.create_content(
                                                            current_cat.category_id, "text", ct_title, ct_body, social_link, user.name
                                                        )
                                                        st.success("تم النشر")
                                                        time.sleep(1)
                                                        st.rerun()
                                                    else:
                                                        st.error("العنوان مطلوب")

                                    # منطقة العرض
                                    contents = bk.ContentModel.get_content_by_category(current_cat.category_id)
                                    if contents:
                                        for item in contents:
                                            with st.container(border=True):
                                                # العنوان + الحذف
                                                c1, c2 = st.columns([0.95, 0.05])
                                                c1.markdown(f"### {item.title}")
                                                if is_super_admin():
                                                    if c2.button("🗑", key=f"del_{item.content_id}"):
                                                        bk.ContentModel.delete_content(item.content_id)
                                                        st.rerun()
                                                
                                                # النص
                                                if item.body:
                                                    st.markdown(item.body, unsafe_allow_html=True)
                                                
                                                # الرابط الذكي (الفيديو)
                                                if item.social_link:
                                                    st.divider()
                                                    smart_embed_link(item.social_link)
                                                
                                                st.caption(f"✍️ {item.created_by} | 📅 {item.created_at}")
                                    else:
                                        st.info("لا يوجد محتوى هنا.")
