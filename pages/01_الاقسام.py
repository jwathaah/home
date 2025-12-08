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
# 🔥 دالة المعالجة الشاملة للروابط (The Ultimate Embedder)
# ==========================================
def smart_embed_link(link):
    if not link: return
    link = link.strip()

    # دالة لإنشاء حاوية HTML تحاكي الجوال
    def render_html_component(html_content, height=650):
        # تغليف المحتوى بتصميم الجوال
        wrapper = f"""
        <div style="
            display: flex; 
            justify-content: center; 
            width: 100%; 
            background-color: transparent;">
            
            <div style="
                width: 100%; 
                max-width: 400px; /* عرض الجوال */
                min-height: {height}px;
                overflow: hidden;
                border-radius: 12px;
                display: flex;
                justify-content: center;
                align-items: center;
            ">
                {html_content}
            </div>
        </div>
        """
        components.html(wrapper, height=height, scrolling=True)

    # ---------------------------------------
    # 1. إنستقرام (Instagram) - جميع الأشكال
    # ---------------------------------------
    if "instagram.com" in link:
        # استخراج معرف الفيديو بدقة (سواء كان reel أو p أو tv)
        # يدعم الروابط الطويلة والقصيرة والتي تحتوي على اسم المستخدم
        match = re.search(r'instagram\.com/(?:.*/)?(reel|p|tv)/([^/?#&]+)', link)
        if match:
            post_id = match.group(2)
            # نستخدم كود التضمين الرسمي من انستقرام لضمان العمل
            embed_code = f"""
            <blockquote class="instagram-media" 
                data-instgrm-permalink="https://www.instagram.com/p/{post_id}/" 
                data-instgrm-version="14" 
                style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);">
            </blockquote>
            <script async src="//www.instagram.com/embed.js"></script>
            """
            render_html_component(embed_code, height=700)
        else:
            st.error("رابط إنستقرام غير صحيح، تأكد من نسخه بشكل كامل.")

    # ---------------------------------------
    # 2. تيك توك (TikTok)
    # ---------------------------------------
    elif "tiktok.com" in link:
        # استخراج معرف الفيديو من تيك توك
        match = re.search(r'video/(\d+)', link)
        if match:
            video_id = match.group(1)
            # كود التضمين الرسمي لتيك توك (الأكثر ضماناً)
            embed_code = f"""
            <blockquote class="tiktok-embed" cite="{link}" data-video-id="{video_id}" style="max-width: 605px;min-width: 325px;" > 
            <section> </section> 
            </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
            """
            render_html_component(embed_code, height=750)
        else:
             # في حال فشل استخراج المعرف، نحاول استخدام الرابط المختصر
             st.markdown(f"🎥 [اضغط هنا لمشاهدة فيديو تيك توك]({link})")

    # ---------------------------------------
    # 3. يوتيوب (Shorts & Regular)
    # ---------------------------------------
    elif "youtube.com" in link or "youtu.be" in link:
        # استخراج المعرف بجميع الأشكال
        video_id = None
        if "shorts" in link:
            match = re.search(r'shorts/([^/?#&]+)', link)
            if match: video_id = match.group(1)
        elif "youtu.be" in link:
            match = re.search(r'youtu\.be/([^/?#&]+)', link)
            if match: video_id = match.group(1)
        else:
            match = re.search(r'v=([^&]+)', link)
            if match: video_id = match.group(1)

        if video_id:
            # نستخدم Iframe لليوتيوب لأنه الأسرع والأفضل
            embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0&playsinline=1"
            html_code = f"""
            <style>
            .iframe-container {{ position: relative; width: 100%; padding-bottom: 56.25%; height: 0; }}
            .iframe-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 10px; }}
            </style>
            <div class="iframe-container">
                <iframe src="{embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            """
            # إذا كان شورتس نعدل الارتفاع ليكون طولياً
            h = 400 if "shorts" not in link else 700
            if "shorts" in link:
                 html_code = html_code.replace("padding-bottom: 56.25%;", "padding-bottom: 177%;") # نسبة الشورتس
            
            render_html_component(html_code, height=h)
        else:
            st.video(link)

    # ---------------------------------------
    # 4. سناب شات (Snapchat) - Spotlight/Story
    # ---------------------------------------
    elif "snapchat.com" in link:
        # سناب شات صعب التضمين المباشر بدون API، نستخدم Iframe مباشر قد يعمل لبعض القصص العامة
        # الأفضل عرضه كرابط خارجي منسق بشكل جميل إذا فشل التضمين
        st.components.v1.iframe(link, height=600, scrolling=True)

    # ---------------------------------------
    # 5. تويتر / X (Twitter)
    # ---------------------------------------
    elif "twitter.com" in link or "x.com" in link:
        embed_code = f"""
        <blockquote class="twitter-tweet">
        <a href="{link}"></a>
        </blockquote> 
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        """
        render_html_component(embed_code, height=600)

    # ---------------------------------------
    # 6. فيسبوك (Facebook)
    # ---------------------------------------
    elif "facebook.com" in link or "fb.watch" in link:
        # فيسبوك يتطلب Iframe خاص بـ "plugins/video.php"
        safe_link = link.replace("&", "&amp;")
        embed_code = f"""
        <iframe src="https://www.facebook.com/plugins/video.php?href={safe_link}&show_text=false&width=350" 
        width="350" height="600" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
        """
        render_html_component(embed_code, height=600)

    # ---------------------------------------
    # 7. ملفات مباشرة
    # ---------------------------------------
    elif link.endswith(('.mp4', '.mov', '.avi', '.mp3', '.wav')):
        if link.endswith(('.mp3', '.wav')):
            st.audio(link)
        else:
            st.video(link)

    # ---------------------------------------
    # 8. رابط عادي
    # ---------------------------------------
    else:
        st.info(f"🔗 رابط خارجي: {link}")
        st.link_button("اضغط لفتح الرابط", link)


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
                                                st.caption("يدعم: Reels, Shorts, TikTok, Tweets, Snapchat")
                                                
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
