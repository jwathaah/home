import streamlit as st
import os

def apply_custom_style():
    """
    دالة لقراءة ملف التنسيق (CSS) وتطبيقه على الصفحة.
    يجب استدعاء هذه الدالة في بداية كل صفحة.
    """
    css_file = "assets/style.css"
    
    # التحقق من وجود الملف لتجنب الأخطاء
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            # حقن كود CSS داخل الصفحة
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # في حال عدم وجود الملف (اختياري)
        pass
