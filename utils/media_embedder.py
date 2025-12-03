import streamlit as st
import streamlit.components.v1 as components

def render_social_media(url):
    """
    دالة ذكية لعرض المحتوى بتصميم متجاوب (Responsive) 
    يحاكي شاشة الجوال لضمان عدم قص المحتوى.
    """
    if not url:
        return

    clean_url = url.split("?")[0].strip()

    # دالة مساعدة لتغليف المحتوى في صندوق بمنتصف الصفحة وبحجم الجوال
    def make_responsive_html(html_content, height=700):
        return f"""
        <div style="
            display: flex; 
            justify-content: center; 
            align-items: center; 
            width: 100%; 
            margin-bottom: 20px;">
            
            <div style="
                width: 100%; 
                max-width: 400px; /* عرض يشبه الجوال */
                border-radius: 12px; 
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1); /* ظل خفيف للجمالية */
            ">
                {html_content}
            </div>
        </div>
        """

    # ==========================================
    # 1. يوتيوب (YouTube)
    # ==========================================
    if "youtube.com" in url or "youtu.be" in url:
        # يوتيوب ممتاز في ستريم لايت ولا يحتاج تعديل، نتركه بعرض كامل
        st.video(url)

    # ==========================================
    # 2. انستقرام (Instagram)
    # ==========================================
    elif "instagram.com" in url:
        # إضافة /embed للحصول على النسخة القابلة للتضمين
        if "/embed" not in clean_url:
            if clean_url.endswith("/"):
                embed_url = clean_url + "embed"
            else:
                embed_url = clean_url + "/embed"
        else:
            embed_url = clean_url

        # كود HTML المحسن
        html_code = f"""
            <iframe 
                src="{embed_url}" 
                width="100%" 
                height="600" 
                frameborder="0" 
                scrolling="yes" 
                allowtransparency="true"
                style="background: white;">
            </iframe>
        """
        # نستخدم ارتفاع أقل لانستقرام
        components.html(make_responsive_html(html_code, height=600), height=610, scrolling=False)

    # ==========================================
    # 3. تيك توك (TikTok)
    # ==========================================
    elif "tiktok.com" in url:
        # تيك توك يحتاج مساحة طولية أكبر
        video_id = clean_url.split("/")[-1]
        html_code = f"""
            <blockquote class="tiktok-embed" cite="{clean_url}" data-video-id="{video_id}" style="max-width: 100%; margin: 0;"> 
            <section> <a target="_blank" href="{clean_url}">Watch on TikTok</a> </section> 
            </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
        """
        components.html(make_responsive_html(html_code), height=750, scrolling=True)

    # ==========================================
    # 4. تويتر / إكس (X)
    # ==========================================
    elif "twitter.com" in url or "x.com" in url:
        html_code = f"""
            <blockquote class="twitter-tweet" data-theme="light" align="center">
            <a href="{url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        """
        # تويتر يتمركز تلقائياً بفضل align="center"
        components.html(html_code, height=600, scrolling=True)

    # ==========================================
    # 5. سناب شات (Snapchat)
    # ==========================================
    elif "snapchat.com" in url:
        html_code = f"""
            <iframe src="{clean_url}" width="100%" height="650" frameborder="0"></iframe>
        """
        components.html(make_responsive_html(html_code), height=660)

    # ==========================================
    # 6. فيسبوك (Facebook)
    # ==========================================
    elif "facebook.com" in url or "fb.watch" in url:
        from urllib.parse import quote
        encoded_url = quote(url)
        
        # نحدد نوع المحتوى (فيديو أم بوست) لتعديل الارتفاع
        is_video = "/videos/" in url or "fb.watch" in url or "/reel/" in url
        plugin = "video.php" if is_video else "post.php"
        height = 600 if is_video else 300
        
        # فيسبوك يحتاج iframe مباشر من سيرفراتهم
        embed_src = f"https://www.facebook.com/plugins/{plugin}?href={encoded_url}&show_text=true&width=500"
        
        html_code = f"""
            <iframe src="{embed_src}" width="100%" height="{height}" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
        """
        components.html(make_responsive_html(html_code), height=height+20, scrolling=True)

    # ==========================================
    # 7. روابط أخرى
    # ==========================================
    else:
        st.info(f"🔗 رابط مرفق: {url}")
        st.link_button("فتح الرابط", url)
