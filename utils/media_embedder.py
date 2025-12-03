import streamlit as st
import streamlit.components.v1 as components
import re

def render_social_media(url):
    """
    دالة شاملة لتضمين روابط وسائل التواصل الاجتماعي (فيديو، صور، تدوينات)
    تدعم: Instagram, YouTube, Twitter (X), TikTok, Facebook, Snapchat
    """
    if not url:
        return

    # تنظيف الرابط من أي إضافات زائدة (مثل ?utm_source=...)
    clean_url = url.split("?")[0]

    # ==========================================
    # 1. يوتيوب (YouTube) - يدعم Shorts و Videos
    # ==========================================
    if "youtube.com" in url or "youtu.be" in url:
        # ستريم لايت يدعم يوتيوب بشكل ممتاز أصلاً
        st.video(url)

    # ==========================================
    # 2. انستقرام (Instagram) - Reels, Posts
    # ==========================================
    elif "instagram.com" in url:
        # انستقرام يحتاج تحويل الرابط إلى صيغة Embed
        # مثال: تحويل /reel/ID/ إلى /reel/ID/embed
        
        # استخراج المعرف ID بغض النظر عن كونه reel أو p (post)
        # الصيغة تكون عادة instagram.com/type/ID
        try:
            # إضافة /embed في نهاية الرابط النظيف
            if clean_url.endswith("/"):
                embed_url = clean_url + "embed"
            else:
                embed_url = clean_url + "/embed"
            
            # عرض النتيجة داخل iframe
            components.html(
                f"""
                <iframe src="{embed_url}" 
                width="100%" height="600" frameborder="0" 
                scrolling="no" allowtransparency="true"></iframe>
                """,
                height=650, # ارتفاع الحاوية
                scrolling=True
            )
        except:
            st.error("رابط انستقرام غير صالح للعرض المباشر")

    # ==========================================
    # 3. تويتر / إكس (Twitter / X)
    # ==========================================
    elif "twitter.com" in url or "x.com" in url:
        try:
            # استخدام مكتبة Publish Twitter الرسمية
            components.html(
                f"""
                <blockquote class="twitter-tweet" data-theme="light">
                <a href="{url}"></a>
                </blockquote>
                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                """,
                height=600,
                scrolling=True
            )
        except:
            st.error("رابط التغريدة غير صحيح")

    # ==========================================
    # 4. تيك توك (TikTok)
    # ==========================================
    elif "tiktok.com" in url:
        # استخراج ID الفيديو إذا أمكن، أو استخدام الرابط الكامل مع السكربت الرسمي
        video_id = clean_url.split("/")[-1]
        components.html(
            f"""
            <blockquote class="tiktok-embed" cite="{clean_url}" data-video-id="{video_id}" style="max-width: 605px;min-width: 325px;" > 
            <section> <a target="_blank" href="{clean_url}">Watch on TikTok</a> </section> 
            </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
            """,
            height=750, # تيك توك يحتاج ارتفاع أكبر
            scrolling=True
        )

    # ==========================================
    # 5. فيسبوك (Facebook) - Watch, Posts
    # ==========================================
    elif "facebook.com" in url or "fb.watch" in url:
        # فيسبوك معقد قليلاً ويحتاج لتوليد رابط iframe خاص
        # نستخدم رابط الامبد العام لفيسبوك
        try:
            # تشفير الرابط ليكون آمناً داخل الـ src
            from urllib.parse import quote
            encoded_url = quote(url)
            
            # نحدد ما إذا كان فيديو أم بوست
            plugin_type = "video.php" if "/videos/" in url or "fb.watch" in url or "/reel/" in url else "post.php"
            
            embed_src = f"https://www.facebook.com/plugins/{plugin_type}?href={encoded_url}&show_text=true&width=500"
            
            components.iframe(embed_src, height=600, scrolling=True)
            
        except:
            st.info(f"رابط فيسبوك: {url}")
            st.link_button("🔗 فتح في فيسبوك", url)

    # ==========================================
    # 6. سناب شات (Snapchat) - Spotlight, Stories
    # ==========================================
    elif "snapchat.com" in url:
        # سناب شات يوفر رابط embed مباشر
        # عادة يكون الرابط: https://www.snapchat.com/embed/ID
        try:
            # إذا كان الرابط عادي، نحاول تحويله لـ embed
            # الروابط تأتي بصيغ كثيرة، الأفضل استخدام التضمين المباشر إذا كان مدعوماً
            if "/embed/" not in url:
                # محاولة استخراج الجزء الأخير
                parts = clean_url.split("/")
                if len(parts) > 3:
                     # هذه محاولة تقريبية، سناب شات معقد في الروابط العامة
                     # لكن أفضل حل هو عرض الرابط كـ iframe للموقع نفسه
                     components.iframe(clean_url, height=600, scrolling=True)
            else:
                 components.iframe(clean_url, height=600)
        except:
             components.iframe(clean_url, height=600)

    # ==========================================
    # 7. روابط أخرى (SoundCloud, Spotify, etc.)
    # ==========================================
    elif "soundcloud.com" in url:
         components.html(f'<iframe width="100%" height="300" scrolling="no" frameborder="no" allow="autoplay" src="https://w.soundcloud.com/player/?url={url}&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true"></iframe>', height=300)
         
    else:
        # في حال كان رابطاً لموقع عادي أو غير مدعوم أعلاه
        st.info(f"🔗 رابط مرفق: {url}")
        st.link_button("فتح الرابط في نافذة جديدة", url)
