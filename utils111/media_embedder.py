import streamlit as st
import streamlit.components.v1 as components

def render_social_media(url):
    """
    دالة لعرض المحتوى الاجتماعي داخل صندوق أبيض نقي 100%
    يحل مشكلة الخلفية الرمادية بإجبار المتصفح على استخدام اللون الأبيض لكامل الإطار.
    """
    if not url:
        return

    clean_url = url.split("?")[0].strip()

    # --- دالة التغليف السحرية (The Magic Wrapper) ---
    # هذه الدالة تبني صفحة HTML كاملة مع إجبار الخلفية على البياض
    def inject_white_background(content_html, height=700):
        full_html = f"""
        <!DOCTYPE html>
        <html style="background-color: #ffffff;">
        <head>
            <style>
                /* إجبار كل العناصر الرئيسية على اللون الأبيض */
                html, body {{
                    background-color: #ffffff !important;
                    background: #ffffff !important;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    overflow: hidden; /* لمنع أشرطة التمرير المزدوجة */
                    font-family: sans-serif;
                }}
                /* حاوية المحتوى لضمان التمركز */
                .container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    height: 100%;
                    background-color: #ffffff;
                }}
                /* تحسين شكل البطاقة الداخلية */
                .card {{
                    background-color: #ffffff;
                    width: 100%;
                    max-width: 450px; /* عرض مناسب للجوال */
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    {content_html}
                </div>
            </div>
        </body>
        </html>
        """
        # نمرر الكود الكامل للمكون
        components.html(full_html, height=height, scrolling=True)

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
            embed_url = clean_url.rstrip("/") + "/embed"
        else:
            embed_url = clean_url
        
        # كود الانستقرام
        html_code = f"""
            <iframe 
                src="{embed_url}" 
                width="100%" 
                height="600" 
                frameborder="0" 
                scrolling="no" 
                allowtransparency="true"
                style="background-color: #ffffff; border: 1px solid #f0f0f0; border-radius: 8px;">
            </iframe>
        """
        inject_white_background(html_code, height=620)

    # ==========================================
    # 3. تيك توك (TikTok)
    # ==========================================
    elif "tiktok.com" in url:
        video_id = clean_url.split("/")[-1]
        html_code = f"""
            <blockquote class="tiktok-embed" cite="{clean_url}" data-video-id="{video_id}" 
                style="max-width: 100%; min-width: 300px; margin: 0; background-color: #ffffff;"> 
                <section> <a target="_blank" href="{clean_url}">Watch on TikTok</a> </section> 
            </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
        """
        inject_white_background(html_code, height=780)

    # ==========================================
    # 4. تويتر / إكس (Twitter/X)
    # ==========================================
    elif "twitter.com" in url or "x.com" in url:
        html_code = f"""
            <blockquote class="twitter-tweet" data-theme="light" align="center">
            <a href="{url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        """
        inject_white_background(html_code, height=600)

    # ==========================================
    # 5. سناب شات (Snapchat)
    # ==========================================
    elif "snapchat.com" in url:
        html_code = f"""
            <iframe src="{clean_url}" width="100%" height="600" frameborder="0" 
            style="background-color: #ffffff; border-radius: 8px;"></iframe>
        """
        inject_white_background(html_code, height=610)

    # ==========================================
    # 6. فيسبوك (Facebook)
    # ==========================================
    elif "facebook.com" in url or "fb.watch" in url:
        from urllib.parse import quote
        encoded_url = quote(url)
        is_video = "/videos/" in url or "fb.watch" in url or "/reel/" in url
        plugin = "video.php" if is_video else "post.php"
        iframe_height = 500 if is_video else 250
        
        embed_src = f"https://www.facebook.com/plugins/{plugin}?href={encoded_url}&show_text=true&width=500&height={iframe_height}&appId"
        
        html_code = f"""
            <iframe src="{embed_src}" width="100%" height="{iframe_height}" 
            style="border:none; overflow:hidden; background-color:#ffffff;" 
            scrolling="no" frameborder="0" allowfullscreen="true" 
            allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
        """
        inject_white_background(html_code, height=iframe_height + 50)

    # ==========================================
    # 7. روابط أخرى
    # ==========================================
    else:
        st.info(f"🔗 رابط مرفق: {url}")
        st.link_button("فتح الرابط", url)
