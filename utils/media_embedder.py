import streamlit as st
import streamlit.components.v1 as components

def render_social_media(url):
    """
    دالة ذكية لعرض المحتوى بتصميم متجاوب وأنيق (خلفية بيضاء نظيفة).
    """
    if not url:
        return

    clean_url = url.split("?")[0].strip()

    # دالة مساعدة لتغليف المحتوى في صندوق أبيض نظيف بمنتصف الصفحة
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
                max-width: 400px; /* عرض الجوال */
                background-color: #ffffff; /* 👈 الحل: خلفية بيضاء صريحة */
                border-radius: 12px; 
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); /* ظل خفيف جداً */
                border: 1px solid #f0f0f0; /* حدود خفيفة جداً */
            ">
                {html_content}
            </div>
        </div>
        """

    # ==========================================
    # 1. يوتيوب (YouTube)
    # ==========================================
    if "youtube.com" in url or "youtu.be" in url:
        st.video(url)

    # ==========================================
    # 2. انستقرام (Instagram)
    # ==========================================
    elif "instagram.com" in url:
        if "/embed" not in clean_url:
            if clean_url.endswith("/"):
                embed_url = clean_url + "embed"
            else:
                embed_url = clean_url + "/embed"
        else:
            embed_url = clean_url

        # إضافة ستايل للخلفية البيضاء داخل الـ iframe نفسه
        html_code = f"""
            <iframe 
                src="{embed_url}" 
                width="100%" 
                height="600" 
                frameborder="0" 
                scrolling="no" 
                allowtransparency="true"
                style="background-color: #ffffff; border: none;"> 
            </iframe>
        """
        # تقليل الارتفاع قليلاً لإزالة الفراغ السفلي
        components.html(make_responsive_html(html_code, height=600), height=605, scrolling=False)

    # ==========================================
    # 3. تيك توك (TikTok)
    # ==========================================
    elif "tiktok.com" in url:
        video_id = clean_url.split("/")[-1]
        html_code = f"""
            <div style="background-color: #ffffff;">
                <blockquote class="tiktok-embed" cite="{clean_url}" data-video-id="{video_id}" style="max-width: 100%; margin: 0; background-color: #ffffff;"> 
                <section> <a target="_blank" href="{clean_url}">Watch on TikTok</a> </section> 
                </blockquote> 
                <script async src="https://www.tiktok.com/embed.js"></script>
            </div>
        """
        components.html(make_responsive_html(html_code), height=760, scrolling=True)

    # ==========================================
    # 4. تويتر / إكس (X)
    # ==========================================
    elif "twitter.com" in url or "x.com" in url:
        html_code = f"""
            <div style="background-color: #ffffff; display: flex; justify-content: center;">
                <blockquote class="twitter-tweet" data-theme="light" align="center">
                <a href="{url}"></a>
                </blockquote>
                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
            </div>
        """
        components.html(make_responsive_html(html_code), height=600, scrolling=True)

    # ==========================================
    # 5. سناب شات (Snapchat)
    # ==========================================
    elif "snapchat.com" in url:
        html_code = f"""
            <iframe src="{clean_url}" width="100%" height="600" frameborder="0" style="background-color: #ffffff;"></iframe>
        """
        components.html(make_responsive_html(html_code), height=610)

    # ==========================================
    # 6. فيسبوك (Facebook)
    # ==========================================
    elif "facebook.com" in url or "fb.watch" in url:
        from urllib.parse import quote
        encoded_url = quote(url)
        is_video = "/videos/" in url or "fb.watch" in url or "/reel/" in url
        plugin = "video.php" if is_video else "post.php"
        height = 500 if is_video else 250
        
        embed_src = f"https://www.facebook.com/plugins/{plugin}?href={encoded_url}&show_text=true&width=500&height={height}&appId"
        
        html_code = f"""
            <div style="background-color: #ffffff; display: flex; justify-content: center;">
                <iframe src="{embed_src}" width="100%" height="{height}" style="border:none;overflow:hidden;background-color:#ffffff;" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
            </div>
        """
        components.html(make_responsive_html(html_code), height=height+50, scrolling=True)

    # ==========================================
    # 7. روابط أخرى
    # ==========================================
    else:
        st.info(f"🔗 رابط مرفق: {url}")
        st.link_button("فتح الرابط", url)
