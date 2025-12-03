import streamlit as st
import streamlit.components.v1 as components

def render_social_media(link):
    """
    دالة ذكية تكتشف نوع الرابط وتقوم بتضمينه في الصفحة مباشرة
    """
    if not link:
        return

    # 1. يوتيوب (YouTube)
    if "youtube.com" in link or "youtu.be" in link:
        st.video(link)
    
    # 2. منصة X (تويتر سابقاً)
    elif "twitter.com" in link or "x.com" in link:
        # كود تضمين تغريدة
        try:
            # استخراج معرف التغريدة
            tweet_id = link.split("/")[-1].split("?")[0]
            components.html(
                f"""
                <blockquote class="twitter-tweet" data-theme="light">
                <a href="{link}"></a>
                </blockquote>
                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                """,
                height=500, # ارتفاع تقديري
                scrolling=True
            )
        except:
            st.error("رابط التغريدة غير صحيح")

    # 3. تيك توك (TikTok)
    elif "tiktok.com" in link:
        components.html(
            f"""
            <blockquote class="tiktok-embed" cite="{link}" data-video-id="{link.split('/')[-1]}" style="max-width: 605px;min-width: 325px;" > 
            <section> <a target="_blank" href="{link}">Watch on TikTok</a> </section> 
            </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
            """,
            height=700,
            scrolling=True
        )

    # 4. روابط أخرى (عرض كزر)
    else:
        st.info(f"رابط خارجي: {link}")
        st.link_button("🔗 فتح الرابط", link)
