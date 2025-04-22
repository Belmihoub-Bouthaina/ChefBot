import streamlit as st
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display
import arabic_reshaper
from io import BytesIO
import random

# ========== إعدادات الألوان الجديدة ==========
FOOD_COLORS = {
    "primary": "#E65100",    # لون اليقطين الدافئ
    "secondary": "#F57C00",  # لون البرتقالي الفاتح
    "accent": "#FFA000",     # لون الكركم
    "background": "#FFF8E1", # لون خلفية فاتح مشابه للقشدة
    "text": "#5D4037",       # لون بني داكن للكتابة
    "success": "#388E3C",    # لون أخضر طازج
    "warning": "#FBC02D",    # لون ليموني
    "error": "#D32F2F",      # لون طماطم
    "info": "#1976D2"        # لون سماوي
}

# ========== إعدادات الصفحة ==========
st.set_page_config(
    page_title="ChefBot",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ========== مفاتيح الترجمة ==========
lang_labels = {
    "fr": {
        "title": "🍽️ ChefBot",
        "ingredient_label": "🧂 Entrez vos ingrédients",
        "input_hint": "Exemple : tomate, fromage, poulet",
        "add_btn": "➕ Ajouter",
        "generate_btn": "🍽️ Générer une recette",
        "loading": "⏳ Génération de la recette...",
        "success": "✅ Recette générée !",
        "warning": "⚠️ Entrez au moins deux ingrédients valides !",
        "invalid": "⚠️ Ingrédient(s) non reconnu(s) !",
        "download": "📄 Télécharger la recette en PDF",
        "select_ingredients": "Sélectionnez des ingrédients",
        "or": "OU",
        "write_ingredients": "Écrivez vos ingrédients",
        "random_btn": "🎲 Ingrédients aléatoires",
        "clear_btn": "🧹 Effacer tout",
        "difficulty_label": "📊 Niveau de difficulté",
        "cuisine_label": "🌍 Type de cuisine",
        "time_label": "⏱️ Temps de préparation",
        "diet_label": "🥗 Régime alimentaire"
    },
    "ar": {
        "title": "🍽️  شاف بوت ",
        "ingredient_label": "🧂 أدخل المكونات",
        "input_hint": "مثال: طماطم، جبن، دجاج",
        "add_btn": "➕ إضافة",
        "generate_btn": "🍽️ تحضير وصفة",
        "loading": "⏳ جاري تحضير الوصفة...",
        "success": "✅ تم تحضير الوصفة!",
        "warning": "⚠️ أدخل مكونين صحيحين على الأقل!",
        "invalid": "⚠️ هناك مكونات غير معروفة!",
        "download": "📄 تحميل الوصفة PDF",
        "select_ingredients": "اختر مكونات",
        "or": "أو",
        "write_ingredients": "اكتب مكوناتك",
        "random_btn": "🎲 مكونات عشوائية",
        "clear_btn": "🧹 مسح الكل",
        "difficulty_label": "📊 مستوى الصعوبة",
        "cuisine_label": "🌍 نوع المطبخ",
        "time_label": "⏱️ وقت التحضير",
        "diet_label": "🥗 نظام غذائي"
    }
}

# ========== قوائم الخيارات ==========
difficulty_levels = {
    "fr": ["Facile", "Moyen", "Difficile"],
    "ar": ["سهلة", "متوسطة", "صعبة"]
}

cuisine_types = {
    "fr": ["Française", "Italienne", "Mexicaine", "Espagnole", "Libanaise", "Marocaine", "Asiatique", "Indienne", "Internationale"],
    "ar": ["فرنسي", "إيطالي", "مكسيكي", "إسباني", "لبناني", "مغربي", "آسيوي", "هندي", "عالمي"]
}

prep_times = {
    "fr": ["Rapide (<30 min)", "Moyen (30-60 min)", "Long (>1 heure)"],
    "ar": ["سريع (<30 دقيقة)", "متوسط (30-60 دقيقة)", "طويل (>1 ساعة)"]
}

diet_types = {
    "fr": ["Aucun", "Végétarien", "Végan", "Sans gluten", "Faible en calories"],
    "ar": ["بدون قيود", "نباتي", "نباتي صرف", "خالي من الجلوتين", "قليل السعرات"]
}

# ========== قائمة المكونات المقبولة ==========
valid_ingredients = {
    "fr": [
        "Tomate", "Oignon", "Ail", "Poulet", "Bœuf", "Poisson", "Crevettes",
        "Pomme de terre", "Carotte", "Courgette", "Aubergine", "Poivron",
        "Œuf", "Fromage", "Lait", "Crème", "Beurre", "Huile d'olive",
        "Vinaigre", "Citron", "Sel", "Poivre", "Pâtes", "Riz", "Pain",
        "Farine", "Sucre", "Chocolat", "Amandes", "Noix", "Miel"
    ],
    "ar": [
        "طماطم", "بصل", "ثوم", "دجاج", "لحم بقري", "سمك", "روبيان",
        "بطاطا", "جزر", "كوسة", "باذنجان", "فلفل رومي",
        "بيض", "جبن", "حليب", "قشطة", "زبدة", "زيت زيتون",
        "خل", "ليمون", "ملح", "فلفل", "معكرونة", "أرز", "خبز",
        "طحين", "سكر", "شوكولاتة", "لوز", "جوز", "عسل"
    ]
}

# ========== تنسيقات CSS المخصصة ==========
def apply_custom_styles():
    st.markdown(f"""
    <style>
        /* تنسيقات عامة */
        body {{
            color: {FOOD_COLORS['text']};
            background-color: #f9f9f9;
        }}
        
        /* الأزرار */
        .stButton>button {{
            background-color: {FOOD_COLORS['primary']};
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .stButton>button:hover {{
            background-color: {FOOD_COLORS['secondary']};
            transform: scale(1.02);
        }}
        
        /* حقول الإدخال */
        .stTextInput>div>div>input, 
        .stSelectbox>div>div>select {{
            border-radius: 6px;
            border: 1px solid {FOOD_COLORS['accent']};
        }}
        
        /* التبويبات */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {FOOD_COLORS['background']};
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            transition: all 0.3s;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {FOOD_COLORS['primary']};
            color: white !important;
        }}
        
        /* الأقسام المخصصة */
        .ingredients-section {{
            background-color: #FFF3E0;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid {FOOD_COLORS['accent']};
        }}
        .preparation-section {{
            background-color: #E8F5E9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid {FOOD_COLORS['success']};
        }}
        .info-section {{
            background-color: #E3F2FD;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid {FOOD_COLORS['info']};
        }}
    </style>
    """, unsafe_allow_html=True)

# ========== دالة إنشاء PDF ==========
def create_pdf(text, lang="ar"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    try:
        if lang == "ar":
            pdfmetrics.registerFont(TTFont('ArabicFont', 'Amiri-Regular.ttf'))
            c.setFont('ArabicFont', 14)
        else:
            c.setFont("Helvetica", 14)
    except:
        c.setFont("Helvetica", 14)
    
    lines = text.split('\n')
    y = height - 50

    for line in lines:
        if lang == "ar":
            try:
                reshaped_text = arabic_reshaper.reshape(line)
                bidi_text = get_display(reshaped_text)
                c.drawRightString(width - 40, y, bidi_text)
            except:
                c.drawRightString(width - 40, y, line)
        else:
            c.drawString(40, y, line)
        y -= 22
        if y < 40:
            c.showPage()
            y = height - 50
            try:
                if lang == "ar":
                    c.setFont('ArabicFont', 14)
                else:
                    c.setFont("Helvetica", 14)
            except:
                c.setFont("Helvetica", 14)

    c.save()
    buffer.seek(0)
    return buffer

# ========== واجهة المستخدم ==========
def main():
    apply_custom_styles()
    
    # اختيار اللغة
    language_choice = st.sidebar.selectbox("🌐 Choisir la langue / اختر اللغة", ["Français", "العربية"])
    lang = "fr" if language_choice == "Français" else "ar"
    t = lang_labels[lang]

    # عرض العنوان
    st.markdown(f"""
    <div style="text-align:center; background-color:{FOOD_COLORS['background']}; 
                padding:20px; border-radius:10px; margin-bottom:20px;
                border-left: 5px solid {FOOD_COLORS['primary']};
                border-right: 5px solid {FOOD_COLORS['primary']};">
        <h1 style="color:{FOOD_COLORS['primary']}; font-weight:bold;">{t['title']}</h1>
        <p style="color:{FOOD_COLORS['text']}; font-size:16px;">
            {'Créez des recettes personnalisées en un clic' if lang == 'fr' else 'أنشئ وصفات مخصصة بنقرة واحدة'}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # تبويبات إدخال المكونات
    tab1, tab2 = st.tabs([t["select_ingredients"], t["write_ingredients"]])

    with tab1:
        selected = st.multiselect(
            t["select_ingredients"],
            valid_ingredients[lang],
            placeholder=t["select_ingredients"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t["random_btn"]):
                selected = random.sample(valid_ingredients[lang], 5)
                st.session_state.ingredients = selected
                st.success(f"✅ {t['random_btn']}: {', '.join(selected)}")
        
        with col2:
            if st.button(t["add_btn"]):
                if selected:
                    st.session_state.ingredients = selected
                    st.success(f"✅ {', '.join(selected)}")
                else:
                    st.warning(t["warning"])

    with tab2:
        user_input = st.text_input(t["ingredient_label"], placeholder=t["input_hint"])
        
        if st.button(t["add_btn"], key="add_manual"):
            cleaned = [i.strip() for i in user_input.split(",") if i.strip()]
            if cleaned:
                st.session_state.ingredients = cleaned
                st.success(f"✅ {', '.join(cleaned)}")
            else:
                st.warning(t["warning"])

    # خيارات الوصفة
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        difficulty = st.selectbox(t["difficulty_label"], difficulty_levels[lang])
    with col2:
        cuisine = st.selectbox(t["cuisine_label"], cuisine_types[lang])
    with col3:
        prep_time = st.selectbox(t["time_label"], prep_times[lang])
    with col4:
        diet = st.selectbox(t["diet_label"], diet_types[lang])

    # زر مسح الكل
    if st.button(t["clear_btn"]):
        if "ingredients" in st.session_state:
            del st.session_state.ingredients
        st.rerun()

    # عرض المكونات المختارة
    if "ingredients" in st.session_state and st.session_state.ingredients:
        st.markdown(f"**📝 {('المكونات المختارة' if lang == 'ar' else 'Ingrédients sélectionnés')}:**")
        st.write(", ".join(set(st.session_state.ingredients)))

    # توليد الوصفة
    if st.button(t["generate_btn"]):
        if "ingredients" not in st.session_state or len(st.session_state.ingredients) < 2:
            st.warning(t["warning"])
        else:
            with st.spinner(t["loading"]):
                ingredients = ", ".join(st.session_state.ingredients)
                
                if lang == "ar":
                    prompt = f"""
                    أنشئ وصفة طهي كاملة باللغة العربية باستخدام المكونات التالية: {ingredients}
                    مواصفات الوصفة:
                    - مستوى الصعوبة: {difficulty}
                    - نوع المطبخ: {cuisine}
                    - وقت التحضير: {prep_time}
                    - النظام الغذائي: {diet}
                    
                    يجب أن تحتوي الوصفة على:
                    1. اسم الوصفة (مبتكر وجذاب)
                    2. المكونات بالتفصيل مع الكميات
                    3. خطوات التحضير المرقمة
                    4. وقت التحضير ووقت الطهي
                    5. عدد الحصص
                    6. نصائح تقديم
                    
                    استخدم اللغة العربية الفصحى فقط بدون أي كلمات أجنبية.
                    اكتب الأرقام بالأحرف العربية.
                    اجعل الوصفة متناسبة مع مستوى الصعوبة المطلوب.
                    """
                else:
                    prompt = f"""
                    Créez une recette de cuisine complète en français avec les ingrédients suivants: {ingredients}
                    Spécifications:
                    - Difficulté: {difficulty}
                    - Type de cuisine: {cuisine}
                    - Temps de préparation: {prep_time}
                    - Régime alimentaire: {diet}
                    
                    La recette doit contenir:
                    1. Un nom de recette (original et attrayant)
                    2. La liste détaillée des ingrédients avec quantités
                    3. Les étapes de préparation numérotées
                    4. Temps de préparation et temps de cuisson
                    5. Nombre de portions
                    6. Conseils de présentation
                    
                    Utilisez uniquement la langue française sans aucun mot arabe.
                    Écrivez les nombres en lettres.
                    Adaptez la recette au niveau de difficulté demandé.
                    """
                
                try:
                    # إعداد نموذج Gemini
                    API_KEY = "AIzaSyCcnPKnspaBqJiY-xIh0i9zB2KMC_uH_DQ"
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content(prompt)
                    recipe_text = response.text
                    
                    # تنظيف النص الناتج
                    clean_recipe = []
                    for line in recipe_text.split("\n"):
                        if line.strip():
                            if lang == "ar":
                                if not any(word in line.lower() for word in ["ingredients", "preparation", "temps", "step"]):
                                    clean_recipe.append(line)
                            else:
                                if not any(word in line for word in ["مقادير", "طريقة", "خطوة"]):
                                    clean_recipe.append(line)
                    
                    recipe_text = "\n".join(clean_recipe)
                    
                    # عرض الوصفة
                    st.success(t["success"])
                    
                    # اسم الوصفة
                    st.markdown(f"""
                    <div style="background-color:{FOOD_COLORS['background']}; 
                                padding:15px; border-radius:10px; margin-bottom:20px;
                                border-top: 3px solid {FOOD_COLORS['primary']};">
                        <h3 style="color:{FOOD_COLORS['primary']}; text-align:center;">{recipe_text.split('\n')[0]}</h3>
                        <p style="text-align:center; color:{FOOD_COLORS['text']};">
                            {difficulty} | {cuisine} | {prep_time} | {diet}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # المكونات
                    st.markdown(f"### {'🧂 المكونات' if lang == 'ar' else '🧂 Ingrédients'}")
                    ingredients_section = "\n".join([line for line in recipe_text.split("\n")[1:] if not line.startswith(("1.", "2.", "3.", "4."))])
                    st.markdown(ingredients_section)
                     # طريقة التحضير
                    st.markdown(f"### {'👩‍🍳 طريقة التحضير' if lang == 'ar' else '👩‍🍳 Préparation'}")
                    preparation_section = "\n".join([line for line in recipe_text.split("\n") if line.startswith(("1.", "2.", "3.", "4."))])
                    st.markdown(preparation_section)


                    # معلومات إضافية
                    st.markdown(f"### {'ℹ️ معلومات إضافية' if lang == 'ar' else 'ℹ️ Informations supplémentaires'}")
                    cols = st.columns(2)
                    with cols[0]:
                     st.markdown(f"**{'⏱️ وقت التحضير' if lang == 'ar' else '⏱️ Temps de préparation'}:**\n\n{prep_time}")
                    with cols[1]:
                      st.markdown(f"**{'🍽️ عدد الحصص' if lang == 'ar' else '🍽️ Portions'}:**\n\n{'غير محدد' if lang == 'ar' else 'Non spécifié'}")
                    # حفظ PDF
                    pdf = create_pdf(recipe_text, lang=lang)
                    st.download_button(
                        label=t["download"],
                        data=pdf,
                        file_name=("recette.pdf" if lang == "fr" else "وصفة.pdf"),
                        mime="application/pdf",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"❌ {'حدث خطأ أثناء توليد الوصفة' if lang == 'ar' else 'Erreur lors de la génération de la recette'}: {str(e)}")

if __name__ == "__main__":
    main()
