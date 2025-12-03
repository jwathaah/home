import streamlit as st
import pandas as pd
from models.form_model import FormModel, FormAnswerModel
from models.section_model import CategoryModel, SectionModel, TabModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR

# 1. إعداد الصفحة
st.set_page_config(page_title="النماذج والاستبيانات", page_icon="📝", layout="wide")

user = get_current_user()
if not user:
    st.warning("🔒 يرجى تسجيل الدخول.")
    st.stop()

from ui.layout import render_sidebar
render_sidebar()

# 2. تحديد الصلاحيات
is_admin = user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]
is_supervisor = user.role_id == ROLE_SUPERVISOR

st.title("📝 النماذج والاستبيانات")

# تقسيم الصفحة إلى تبويبات حسب الدور
tabs_list = ["تعبئة نموذج"]
if is_admin or is_supervisor:
    tabs_list.extend(["إنشاء نموذج جديد", "عرض الردود"])

page_tabs = st.tabs(tabs_list)

# --- تبويب 1: تعبئة النماذج (للجميع) ---
with page_tabs[0]:
    st.header("النماذج المتاحة")
    all_forms = FormModel.get_all_forms()
    
    if not all_forms:
        st.info("لا توجد نماذج متاحة حالياً.")
    else:
        # قائمة اختيار النموذج
        form_titles = [f.title for f in all_forms]
        selected_title = st.selectbox("اختر النموذج:", form_titles)
        
        # البحث عن كائن النموذج المختار
        selected_form = next((f for f in all_forms if f.title == selected_title), None)
        
        if selected_form:
            st.markdown(f"### {selected_form.title}")
            st.caption(selected_form.description)
            st.divider()
            
            # بناء النموذج ديناميكياً
            with st.form(f"submit_form_{selected_form.form_id}"):
                answers = {}
                fields = selected_form.get_fields() # جلب الأسئلة من JSON
                
                for field in fields:
                    q_text = field.get("question", "سؤال بدون نص")
                    q_type = field.get("type", "text")
                    q_options = field.get("options", "").split(",") if "options" in field else []
                    required = field.get("required", False)
                    
                    label = f"{q_text} {'(مطلوب)' if required else ''}"
                    
                    if q_type == "text":
                        answers[q_text] = st.text_input(label)
                    elif q_type == "textarea":
                        answers[q_text] = st.text_area(label)
                    elif q_type == "number":
                        answers[q_text] = st.number_input(label, step=1)
                    elif q_type == "radio":
                        answers[q_text] = st.radio(label, q_options)
                    elif q_type == "checkbox":
                        answers[q_text] = st.multiselect(label, q_options)
                    elif q_type == "date":
                        answers[q_text] = str(st.date_input(label))
                
                submitted = st.form_submit_button("إرسال الإجابة", use_container_width=True)
                
                if submitted:
                    # التحقق من الحقول المطلوبة (بسيط)
                    missing = False
                    for field in fields:
                        if field.get("required") and not answers.get(field["question"]):
                            missing = True
                    
                    if missing:
                        st.error("يرجى تعبئة الحقول المطلوبة.")
                    else:
                        FormAnswerModel.submit_answer(selected_form.form_id, user.user_id, answers)
                        st.success("✅ تم إرسال إجابتك بنجاح! شكراً لك.")

# --- تبويب 2: إنشاء نموذج جديد (للمدراء) ---
if is_admin or is_supervisor:
    with page_tabs[1]:
        st.header("🛠 بناء نموذج جديد")
        
        # مرحلة 1: البيانات الأساسية
        with st.container(border=True):
            new_title = st.text_input("عنوان النموذج")
            new_desc = st.text_area("وصف النموذج")
            
            # ربط النموذج بفئة (Category) اختيارياً
            # (يمكننا تركه عاماً أو ربطه، هنا سنضعه عاماً "General" للتبسيط)
            cat_id = "General" 
            
        st.divider()
        
        # مرحلة 2: بناء الأسئلة
        st.subheader("إضافة الأسئلة")
        
        # نستخدم session_state لتخزين الأسئلة مؤقتاً قبل الحفظ
        if 'temp_fields' not in st.session_state:
            st.session_state.temp_fields = []
            
        # نموذج إضافة سؤال واحد
        with st.expander("➕ أضف سؤالاً جديداً", expanded=True):
            c1, c2 = st.columns([2, 1])
            q_text = c1.text_input("نص السؤال")
            q_type = c2.selectbox("نوع السؤال", ["text", "textarea", "number", "radio", "checkbox", "date"])
            
            q_opts = ""
            if q_type in ["radio", "checkbox"]:
                q_opts = st.text_input("الخيارات (افصل بينها بفاصلة ,)", placeholder="نعم,لا,ربما")
            
            q_req = st.checkbox("هذا السؤال مطلوب؟")
            
            if st.button("إدراج السؤال"):
                if q_text:
                    st.session_state.temp_fields.append({
                        "question": q_text,
                        "type": q_type,
                        "options": q_opts,
                        "required": q_req
                    })
                    st.rerun()

        # عرض الأسئلة المضافة حالياً
        if st.session_state.temp_fields:
            st.write("🔽 الأسئلة الحالية:")
            for idx, f in enumerate(st.session_state.temp_fields):
                st.info(f"{idx+1}. {f['question']} ({f['type']})")
                
            if st.button("🗑 مسح الكل والبدء من جديد"):
                st.session_state.temp_fields = []
                st.rerun()

            # زر الحفظ النهائي
            if st.button("💾 حفظ النموذج نهائياً", type="primary"):
                if new_title and st.session_state.temp_fields:
                    FormModel.create_form(cat_id, new_title, new_desc, st.session_state.temp_fields, user.name)
                    st.success("تم إنشاء النموذج بنجاح!")
                    st.session_state.temp_fields = [] # تصفير
                    st.rerun()
                else:
                    st.error("يرجى كتابة عنوان وإضافة سؤال واحد على الأقل.")

# --- تبويب 3: عرض الردود (للمدراء) ---
if is_admin or is_supervisor:
    with page_tabs[2]:
        st.header("📊 نتائج الاستبيانات")
        
        all_forms_2 = FormModel.get_all_forms()
        if not all_forms_2:
            st.write("لا نماذج.")
        else:
            target_form_title = st.selectbox("اختر النموذج لعرض نتائجه:", [f.title for f in all_forms_2], key="res_sel")
            target_form = next((f for f in all_forms_2 if f.title == target_form_title), None)
            
            if target_form:
                # جلب الإجابات
                answers_list = FormAnswerModel.get_answers_by_form(target_form.form_id)
                
                if not answers_list:
                    st.info("لا توجد إجابات لهذا النموذج بعد.")
                else:
                    st.metric("عدد الإجابات", len(answers_list))
                    
                    # تحويل البيانات لجدول عرض جميل
                    # سنقوم بفك JSON لكل إجابة ووضعه في صف
                    data_rows = []
                    for ans in answers_list:
                        row_data = ans.get_parsed_answers()
                        row_data['تاريخ الإجابة'] = ans.created_at
                        # يمكن إضافة اسم المستخدم إذا أردنا (يحتاج جلب user by id)
                        data_rows.append(row_data)
                    
                    df = pd.DataFrame(data_rows)
                    st.dataframe(df, use_container_width=True)
                    
                    # زر تحميل إكسل
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 تحميل النتائج (Excel/CSV)", csv, "results.csv", "text/csv")
