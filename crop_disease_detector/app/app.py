import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import json
import time
import plotly.graph_objects as go
from deep_translator import GoogleTranslator

# ─── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="AgroVision",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Load CSS ────────────────────────────────────────────
def load_css():
    with open("style.css", "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

# ─── Theme State ─────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Apply theme via JS
theme_class = "dark-mode" if st.session_state.dark_mode else "light-mode"
theme_attr = "dark" if st.session_state.dark_mode else "light"
st.markdown(f"""
<script>
    document.body.className = '{theme_class}';
    document.documentElement.setAttribute('data-theme', '{theme_attr}');
</script>
""", unsafe_allow_html=True)

# ─── Language Setup ──────────────────────────────────────
LANGUAGES = {
    "English": "en",
    "Hindi (हिंदी)": "hi",
    "Bengali (বাংলা)": "bn",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Marathi (मराठी)": "mr",
    "Gujarati (ગુજરાતી)": "gu",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Malayalam (മലയാളം)": "ml",
    "Punjabi (ਪੰਜਾਬੀ)": "pa",
    "Odia (ଓଡ଼ିଆ)": "or",
    "Urdu (اردو)": "ur",
    "Assamese (অসমীয়া)": "as",
    "Sindhi (سنڌي)": "sd",
    "Sanskrit (संस्कृतम्)": "sa",
    "Nepali (नेपाली)": "ne",
    "Sinhala (සිංහල)": "si",
    "Maithili (मैथिली)": "mai",
    "Kashmiri (کٲشُر)": "ks",
    "Dogri (डोगरी)": "doi",
    "Konkani (कोंकणी)": "gom",
    "Manipuri (মৈতৈলোন্)": "mni-Mtei",
    "Bodo (बड़ो)": "brx",
    "Santali (ᱥᱟᱱᱛᱟᱲᱤ)": "sat"
}

# ─── Translation Cache ───────────────────────────────────
if "translation_cache" not in st.session_state:
    st.session_state.translation_cache = {}

def translate(text, target_lang):
    if target_lang == "en" or not text:
        return text
    cache_key = f"{target_lang}:{text}"
    if cache_key in st.session_state.translation_cache:
        return st.session_state.translation_cache[cache_key]
    try:
        result = GoogleTranslator(
            source='en', target=target_lang).translate(text)
        st.session_state.translation_cache[cache_key] = result
        return result
    except:
        return text

def translate_list(items, target_lang):
    if target_lang == "en":
        return items
    return [translate(item, target_lang) for item in items]

# ─── Disease Database ────────────────────────────────────
DISEASE_INFO = {
    "Pepper__bell___Bacterial_spot": {
        "description": "A bacterial disease caused by Xanthomonas campestris that affects pepper plants.",
        "symptoms": "Water-soaked spots on leaves, brown lesions with yellow halos, fruit spots.",
        "treatment": [
            "Apply copper-based bactericides every 7-10 days",
            "Remove and destroy infected plant parts immediately",
            "Use streptomycin-based sprays in early stages"
        ],
        "prevention": [
            "Use disease-free certified seeds",
            "Avoid overhead irrigation",
            "Rotate crops every season",
            "Maintain proper plant spacing for air circulation"
        ]
    },
    "Pepper__bell___healthy": {
        "description": "Your pepper plant is healthy and showing no signs of disease.",
        "symptoms": "No symptoms detected. Plant looks great!",
        "treatment": ["No treatment needed"],
        "prevention": [
            "Continue regular watering schedule",
            "Monitor plants weekly for early signs",
            "Maintain soil nutrition with balanced fertilizer"
        ]
    },
    "Potato___Early_blight": {
        "description": "A fungal disease caused by Alternaria solani affecting potato plants.",
        "symptoms": "Dark brown spots with concentric rings, yellow surrounding tissue, lower leaves affected first.",
        "treatment": [
            "Apply chlorothalonil or mancozeb fungicide",
            "Spray every 7-14 days during wet weather",
            "Remove infected leaves immediately"
        ],
        "prevention": [
            "Plant certified disease-free seed potatoes",
            "Avoid wetting foliage during irrigation",
            "Ensure proper crop rotation every 3-4 years",
            "Apply mulch to prevent soil splash"
        ]
    },
    "Potato___Late_blight": {
        "description": "A devastating disease caused by Phytophthora infestans — same pathogen that caused the Irish Potato Famine.",
        "symptoms": "Water-soaked lesions on leaves, white fuzzy growth on undersides, brown rot spreading rapidly.",
        "treatment": [
            "Apply metalaxyl or cymoxanil fungicides immediately",
            "Spray every 5-7 days in wet conditions",
            "Destroy infected plants completely — do not compost"
        ],
        "prevention": [
            "Use resistant potato varieties",
            "Plant in well-drained soil",
            "Monitor weather — disease spreads fast in cool wet conditions",
            "Avoid overhead irrigation"
        ]
    },
    "Potato___healthy": {
        "description": "Your potato plant is healthy and showing no signs of disease.",
        "symptoms": "No symptoms detected. Plant looks great!",
        "treatment": ["No treatment needed"],
        "prevention": [
            "Continue regular monitoring",
            "Maintain proper irrigation",
            "Use balanced NPK fertilizer"
        ]
    },
    "Tomato_Bacterial_spot": {
        "description": "Caused by Xanthomonas vesicatoria, spreads rapidly in warm wet conditions.",
        "symptoms": "Small water-soaked spots on leaves and fruits, spots turn brown with yellow halos.",
        "treatment": [
            "Apply copper hydroxide sprays",
            "Use bactericides every 7 days",
            "Remove heavily infected plants"
        ],
        "prevention": [
            "Use resistant tomato varieties",
            "Avoid working with plants when wet",
            "Disinfect tools regularly",
            "Use drip irrigation instead of overhead"
        ]
    },
    "Tomato_Early_blight": {
        "description": "Fungal disease caused by Alternaria solani, very common in tomato crops.",
        "symptoms": "Dark spots with rings on older leaves, yellowing around spots, stem lesions.",
        "treatment": [
            "Apply mancozeb or chlorothalonil fungicide",
            "Remove infected lower leaves",
            "Spray every 7-10 days"
        ],
        "prevention": [
            "Stake plants for better air circulation",
            "Mulch around base to prevent soil splash",
            "Water at base of plant only",
            "Rotate crops annually"
        ]
    },
    "Tomato_Late_blight": {
        "description": "Caused by Phytophthora infestans, can destroy entire crop within days.",
        "symptoms": "Greasy grey-green spots on leaves, white mold on undersides, brown fruit rot.",
        "treatment": [
            "Apply metalaxyl fungicide immediately",
            "Remove and bag infected plant material",
            "Spray every 5 days in wet weather"
        ],
        "prevention": [
            "Plant resistant varieties",
            "Improve field drainage",
            "Monitor forecasts — spray before rain"
        ]
    },
    "Tomato_Leaf_Mold": {
        "description": "Caused by Passalora fulva fungus, common in humid greenhouse conditions.",
        "symptoms": "Yellow patches on upper leaf surface, olive-green mold on undersides.",
        "treatment": [
            "Apply fungicides containing chlorothalonil",
            "Improve greenhouse ventilation",
            "Reduce humidity below 85%"
        ],
        "prevention": [
            "Use resistant tomato varieties",
            "Space plants well for airflow",
            "Avoid wetting leaves during watering"
        ]
    },
    "Tomato_Septoria_leaf_spot": {
        "description": "Fungal disease caused by Septoria lycopersici, spreads from lower leaves upward.",
        "symptoms": "Small circular spots with dark borders and light centers, tiny black dots inside spots.",
        "treatment": [
            "Apply copper or chlorothalonil fungicide",
            "Remove infected leaves immediately",
            "Spray every 7-10 days"
        ],
        "prevention": [
            "Avoid overhead watering",
            "Mulch to prevent soil splash",
            "Rotate crops every 2-3 years"
        ]
    },
    "Tomato_Spider_mites_Two_spotted_spider_mite": {
        "description": "Infestation by Tetranychus urticae mites, worse in hot dry conditions.",
        "symptoms": "Tiny yellow or white dots on leaves, fine webbing on undersides, leaves turn bronze.",
        "treatment": [
            "Apply miticide or insecticidal soap spray",
            "Use neem oil spray every 5-7 days",
            "Introduce predatory mites for biological control"
        ],
        "prevention": [
            "Keep plants well watered — mites prefer dry conditions",
            "Spray water on leaf undersides regularly",
            "Avoid excessive nitrogen fertilizer"
        ]
    },
    "Tomato__Target_Spot": {
        "description": "Caused by Corynespora cassiicola fungus, affects leaves, stems and fruits.",
        "symptoms": "Brown spots with concentric rings, yellowing leaves, defoliation in severe cases.",
        "treatment": [
            "Apply azoxystrobin or chlorothalonil fungicide",
            "Remove infected plant material",
            "Spray every 7 days"
        ],
        "prevention": [
            "Improve air circulation between plants",
            "Avoid leaf wetness",
            "Use mulch to prevent soil splash"
        ]
    },
    "Tomato__Tomato_YellowLeaf__Curl_Virus": {
        "description": "Viral disease spread by whiteflies, one of the most damaging tomato diseases.",
        "symptoms": "Upward curling of leaves, yellowing leaf edges, stunted growth, reduced fruit set.",
        "treatment": [
            "No cure for virus — remove infected plants immediately",
            "Control whitefly population with insecticides",
            "Use yellow sticky traps to monitor whiteflies"
        ],
        "prevention": [
            "Use virus-resistant tomato varieties",
            "Control whiteflies before planting",
            "Use reflective mulch to repel whiteflies",
            "Install insect-proof nets in greenhouse"
        ]
    },
    "Tomato__Tomato_mosaic_virus": {
        "description": "Highly contagious viral disease that persists in soil and plant debris for years.",
        "symptoms": "Mosaic pattern of light and dark green on leaves, distorted leaves, stunted plants.",
        "treatment": [
            "No cure — remove and destroy infected plants",
            "Disinfect all tools with bleach solution",
            "Wash hands thoroughly after handling plants"
        ],
        "prevention": [
            "Use certified virus-free seeds",
            "Control aphids which spread the virus",
            "Avoid smoking near plants",
            "Rotate crops for 2+ years"
        ]
    },
    "Tomato_healthy": {
        "description": "Your tomato plant is healthy and showing no signs of disease.",
        "symptoms": "No symptoms detected. Plant looks great!",
        "treatment": ["No treatment needed — plant looks great!"],
        "prevention": [
            "Continue regular watering and fertilizing",
            "Monitor weekly for early disease signs",
            "Maintain good air circulation"
        ]
    }
}

# ─── Training History ────────────────────────────────────
TRAINING_HISTORY = {
    "accuracy": [0.7370, 0.8356, 0.8518, 0.8607,
                 0.8770, 0.8810, 0.8853, 0.8890],
    "val_accuracy": [0.8527, 0.8719, 0.8814, 0.8797,
                     0.9005, 0.8971, 0.8993, 0.8986],
    "loss": [0.8050, 0.4925, 0.4305, 0.3935,
             0.3602, 0.3434, 0.3310, 0.3186],
    "val_loss": [0.4455, 0.3976, 0.3449, 0.3492,
                 0.2976, 0.3054, 0.2906, 0.2888]
}

# ─── Load Model ──────────────────────────────────────────
@st.cache_resource
def load_model():
    interpreter = tf.lite.Interpreter(
        model_path="../model/crop_disease_model.tflite"
    )
    interpreter.allocate_tensors()
    return interpreter

@st.cache_resource
def load_class_names():
    with open("../model/class_names.json", "r") as f:
        return json.load(f)

def predict(image, interpreter, class_names):
    img = image.resize((224, 224))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    predictions = interpreter.get_tensor(
        output_details[0]['index'])[0]
    top3_idx = np.argsort(predictions)[::-1][:3]
    return [(class_names[i], float(predictions[i]) * 100)
            for i in top3_idx]

def clean_name(class_name):
    return class_name.replace(
        '___', ' ').replace('__', ' ').replace('_', ' ')

# ─── Sidebar ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">🌿 AgroVision</div>
        <div class="sidebar-tagline">
            AI-Powered Crop Disease Detection
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle
    theme_icon = "☀️ Light Mode" if st.session_state.dark_mode \
        else "🌙 Dark Mode"
    if st.button(theme_icon, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Navigate</div>',
                unsafe_allow_html=True)
    page = st.radio("", ["🏠 Home", "ℹ️ About",
                         "📖 How to Use", "📊 Statistics"],
                    label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Language / भाषा</div>',
                unsafe_allow_html=True)
    selected_language = st.selectbox(
        "", list(LANGUAGES.keys()), label_visibility="collapsed")
    lang_code = LANGUAGES[selected_language]
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-label">Quick Stats</div>
        <div class="stat-mini">
            <span class="stat-mini-label">🎯 Accuracy</span>
            <span class="stat-mini-value">90.05%</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">🌱 Crops</span>
            <span class="stat-mini-value">3</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">🦠 Diseases</span>
            <span class="stat-mini-value">15</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">🌐 Languages</span>
            <span class="stat-mini-value">24</span>
        </div>
        <div class="stat-mini">
            <span class="stat-mini-label">📸 Dataset</span>
            <span class="stat-mini-value">20,639</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# HOME PAGE
# ════════════════════════════════════════════════════════
if "🏠 Home" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">🌿 AgroVision</div>
        <div class="hero-subtitle">
            {translate('AI-Powered Crop Disease Detection & Treatment System',
                       lang_code)}
        </div>
        <div class="stat-row">
            <span class="stat-pill">🎯 90.05% Accuracy</span>
            <span class="stat-pill">🌱 3 Crops</span>
            <span class="stat-pill">🦠 15 Diseases</span>
            <span class="stat-pill">🌐 24 Languages</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown(f"""
        <div class="card card-green" style="margin-bottom:1rem">
            <h4>📤 {translate('Upload Leaf Image', lang_code)}</h4>
            <p>{translate('Take a clear photo of the affected crop leaf and upload it below for instant AI analysis.', lang_code)}</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            translate("Choose a leaf image (JPG, PNG)", lang_code),
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            image = Image.open(uploaded_file).convert('RGB')
            st.image(image,
                     caption=translate("Uploaded Leaf Image", lang_code),
                     use_column_width=True)

    with col2:
        st.markdown(f"""
        <div class="card card-blue" style="margin-bottom:1rem">
            <h4>🔍 {translate('Detection Results', lang_code)}</h4>
            <p>{translate('AI analysis results will appear here after uploading an image.', lang_code)}</p>
        </div>
        """, unsafe_allow_html=True)

        if uploaded_file:
            with st.spinner(
                    translate("Analyzing leaf with AI...", lang_code)):
                interpreter = load_model()
                class_names = load_class_names()
                results = predict(image, interpreter, class_names)

            top_class, top_conf = results[0]
            display_name = clean_name(top_class)
            translated_name = translate(display_name, lang_code)
            conf_label = translate("Confidence Score", lang_code)

            if "healthy" in top_class.lower():
                st.markdown(f"""
                <div class="result-healthy">
                    <div class="result-name">✅ {translated_name}</div>
                    <div class="result-conf">{top_conf:.1f}%</div>
                    <div class="result-label">{conf_label}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-disease">
                    <div class="result-name">⚠️ {translated_name}</div>
                    <div class="result-conf">{top_conf:.1f}%</div>
                    <div class="result-label">{conf_label}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(
                f"**{translate('Top 3 Predictions', lang_code)}:**")
            for name, conf in results:
                label = translate(clean_name(name), lang_code)
                st.progress(int(conf))
                st.caption(f"{label} — {conf:.1f}%")
        else:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;
                        color:var(--text-muted)">
                <div style="font-size:3rem;margin-bottom:1rem">🌿</div>
                <p>{translate('Upload a leaf image to get started', lang_code)}</p>
            </div>
            """, unsafe_allow_html=True)

    # Disease info section
    if uploaded_file and results:
        st.markdown("---")
        st.markdown(f"""
        <div class="card card-green">
            <h4>📋 {translate('Disease Information & Treatment Guide', lang_code)}</h4>
        </div>
        """, unsafe_allow_html=True)

        top_class = results[0][0]
        info = DISEASE_INFO.get(top_class)

        if info:
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.markdown(f"""
                <div class="card card-blue">
                    <h4>📝 {translate('Description', lang_code)}</h4>
                    <p>{translate(info['description'], lang_code)}</p>
                </div>
                <div class="card card-orange">
                    <h4>🔬 {translate('Symptoms', lang_code)}</h4>
                    <p>{translate(info['symptoms'], lang_code)}</p>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                t_items = "".join(
                    [f"<li>{t}</li>" for t in
                     translate_list(info['treatment'], lang_code)])
                p_items = "".join(
                    [f"<li>{p}</li>" for p in
                     translate_list(info['prevention'], lang_code)])
                st.markdown(f"""
                <div class="card card-red">
                    <h4>💊 {translate('Treatment', lang_code)}</h4>
                    <ul>{t_items}</ul>
                </div>
                <div class="card card-green">
                    <h4>🛡️ {translate('Prevention', lang_code)}</h4>
                    <ul>{p_items}</ul>
                </div>
                """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">
        <span>🌿 AgroVision</span> —
        AI-Powered Crop Disease Detection & Treatment System |
        <span>Asansol Engineering College</span> |
        MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# ABOUT PAGE
# ════════════════════════════════════════════════════════
elif "ℹ️ About" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">ℹ️ {translate('About', lang_code)}</div>
        <div class="hero-subtitle">
            {translate('AgroVision — AI-Powered Crop Disease Detection & Treatment System', lang_code)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(f"""
        <div class="card card-green">
            <h4>📌 {translate('Project Overview', lang_code)}</h4>
            <p>{translate('AgroVision is an AI-powered crop disease detection and multilingual treatment advisory system built as an MCA final year project. It uses deep learning and computer vision to identify diseases in crop leaves and provides detailed treatment and prevention guidance in 24 Indian languages.', lang_code)}</p>
        </div>
        <div class="card card-blue">
            <h4>🎯 {translate('Objective', lang_code)}</h4>
            <p>{translate('To help farmers and agricultural workers quickly identify crop diseases using smartphone cameras and get actionable treatment advice in their native language — making AI accessible to rural India.', lang_code)}</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card card-orange">
            <h4>🛠️ {translate('Technology Stack', lang_code)}</h4>
            <p>
            🧠 <b>AI Model:</b> MobileNetV2 (Transfer Learning)<br>
            ⚡ <b>Framework:</b> TensorFlow 2.21 / TFLite<br>
            🎨 <b>Frontend:</b> Streamlit<br>
            🌐 <b>Translation:</b> Google Translate API<br>
            📊 <b>Training:</b> Google Colab (T4 GPU)<br>
            📦 <b>Dataset:</b> PlantVillage (20,639 images)<br>
            🐍 <b>Language:</b> Python 3.11
            </p>
        </div>
        <div class="card card-red">
            <h4>📈 {translate('Model Performance', lang_code)}</h4>
            <p>
            🎯 <b>Accuracy:</b> 90.05%<br>
            🌱 <b>Crops:</b> Pepper, Potato, Tomato<br>
            🦠 <b>Diseases:</b> 15 classes<br>
            🌐 <b>Languages:</b> 24 Indian languages<br>
            ⚡ <b>Model Size:</b> 2.7 MB (TFLite)<br>
            🏋️ <b>Training Images:</b> 16,516<br>
            ✅ <b>Validation Images:</b> 4,122
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="card card-green">
        <h4>👥 {translate('Meet The Team', lang_code)}</h4>
        <p>{translate('Asansol Engineering College | Department of MCA | 2025-2026', lang_code)}</p>
    </div>
    """, unsafe_allow_html=True)

    team = [
        {"name": "Akanksha Singh",
         "roll": "108710240003", "role": ""},
        {"name": "Ankita Kumari",
         "roll": "108710240006", "role": ""},
        {"name": "Bipasa Nath",
         "roll": "108710240010", "role": ""},
        {"name": "Shifa Iqbal",
         "roll": "108710240033", "role": ""},
    ]

    cols = st.columns(4, gap="medium")
    for i, member in enumerate(team):
        with cols[i]:
            role = member["role"] if member["role"] else "Role TBD"
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar">👩‍💻</div>
                <div class="team-name">{member['name']}</div>
                <div class="team-roll">{member['roll']}</div>
                <div class="team-role">{role}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">
        <span>🌿 AgroVision</span> |
        <span>Asansol Engineering College</span> |
        MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# HOW TO USE PAGE
# ════════════════════════════════════════════════════════
elif "📖 How to Use" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            📖 {translate('How to Use', lang_code)}
        </div>
        <div class="hero-subtitle">
            {translate('Follow these simple steps to detect crop diseases instantly', lang_code)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        {
            "num": "1", "icon": "🌐",
            "title": translate("Select Your Language", lang_code),
            "desc": translate("From the sidebar on the left, select your preferred language from the dropdown. AgroVision supports 24 Indian languages including Hindi, Bengali, Tamil, Telugu and more. All content will instantly translate to your chosen language.", lang_code)
        },
        {
            "num": "2", "icon": "🏠",
            "title": translate("Go to Home Page", lang_code),
            "desc": translate("Click on Home in the navigation menu in the sidebar to go to the main disease detection page.", lang_code)
        },
        {
            "num": "3", "icon": "📷",
            "title": translate("Take or Choose a Photo", lang_code),
            "desc": translate("Click the Upload button and select a clear photo of the affected crop leaf. Make sure the leaf is clearly visible and well lit. Supported formats: JPG, JPEG, PNG.", lang_code)
        },
        {
            "num": "4", "icon": "⚡",
            "title": translate("Wait for AI Analysis", lang_code),
            "desc": translate("AgroVision's AI model analyzes your leaf image automatically using deep learning. This takes just 1-2 seconds. You will see a spinner while it processes.", lang_code)
        },
        {
            "num": "5", "icon": "🔍",
            "title": translate("View Detection Results", lang_code),
            "desc": translate("The detected disease name appears with a confidence score percentage. Green color means healthy plant, Red means disease detected. Top 3 possible predictions are also shown.", lang_code)
        },
        {
            "num": "6", "icon": "💊",
            "title": translate("Read Treatment Guide", lang_code),
            "desc": translate("Scroll down to see detailed disease information including description, symptoms, step-by-step treatment instructions and prevention tips — all translated to your selected language.", lang_code)
        }
    ]

    for step in steps:
        st.markdown(f"""
        <div class="step-card">
            <div class="step-num">{step['num']}</div>
            <div>
                <div class="step-title">
                    {step['icon']} {step['title']}
                </div>
                <div class="step-desc">{step['desc']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    t1, t2 = st.columns(2, gap="large")

    with t1:
        st.markdown(f"""
        <div class="card card-green">
            <h4>✅ {translate('Tips for Best Results', lang_code)}</h4>
            <ul>
                <li>{translate('Take photo in good natural daylight', lang_code)}</li>
                <li>{translate('Make sure leaf fills most of the frame', lang_code)}</li>
                <li>{translate('Use a single clear undamaged leaf', lang_code)}</li>
                <li>{translate('Keep camera steady while clicking', lang_code)}</li>
                <li>{translate('Clean the lens before taking photo', lang_code)}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown(f"""
        <div class="card card-red">
            <h4>❌ {translate('Common Mistakes to Avoid', lang_code)}</h4>
            <ul>
                <li>{translate('Blurry or dark photos', lang_code)}</li>
                <li>{translate('Multiple leaves in one photo', lang_code)}</li>
                <li>{translate('Using photos downloaded from internet', lang_code)}</li>
                <li>{translate('Extremely zoomed out shots', lang_code)}</li>
                <li>{translate('Photos with heavy shadows or glare', lang_code)}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card card-orange" style="margin-top:0.5rem">
        <h4>🌱 {translate('Supported Crops & Diseases', lang_code)}</h4>
        <p>🌶️ <b>Pepper</b> — {translate('Bacterial Spot, Healthy', lang_code)}</p>
        <p>🥔 <b>Potato</b> — {translate('Early Blight, Late Blight, Healthy', lang_code)}</p>
        <p>🍅 <b>Tomato</b> — {translate('Bacterial Spot, Early Blight, Late Blight, Leaf Mold, Septoria Leaf Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus, Healthy', lang_code)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">
        <span>🌿 AgroVision</span> |
        <span>Asansol Engineering College</span> |
        MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# STATISTICS PAGE
# ════════════════════════════════════════════════════════
elif "📊 Statistics" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            📊 {translate('Statistics', lang_code)}
        </div>
        <div class="hero-subtitle">
            {translate('Dataset details, model performance and training results', lang_code)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🎯 Best Accuracy", "90.05%", "+4.78%")
    with m2:
        st.metric("📸 Total Images", "20,639")
    with m3:
        st.metric("🏋️ Training", "16,516", "80%")
    with m4:
        st.metric("✅ Validation", "4,122", "20%")

    st.markdown("---")

    epochs = list(range(1, 9))
    plot_bg = "#151F15" if st.session_state.dark_mode else "#ffffff"
    plot_paper = "#151F15" if st.session_state.dark_mode else "#ffffff"
    font_color = "#D8F3DC" if st.session_state.dark_mode else "#1B4332"
    grid_color = "#2D6A4F" if st.session_state.dark_mode else "#e0e0e0"

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown(f"""
        <div class="card card-green" style="margin-bottom:0.5rem">
            <h4>📈 {translate('Model Accuracy Over Epochs', lang_code)}</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_acc = go.Figure()
        fig_acc.add_trace(go.Scatter(
            x=epochs,
            y=[a * 100 for a in TRAINING_HISTORY["accuracy"]],
            mode='lines+markers',
            name=translate('Training Accuracy', lang_code),
            line=dict(color='#52B788', width=3),
            marker=dict(size=8, symbol='circle',
                        line=dict(width=2, color='#1B4332'))
        ))
        fig_acc.add_trace(go.Scatter(
            x=epochs,
            y=[a * 100 for a in TRAINING_HISTORY["val_accuracy"]],
            mode='lines+markers',
            name=translate('Validation Accuracy', lang_code),
            line=dict(color='#F4A261', width=3),
            marker=dict(size=8, symbol='diamond',
                        line=dict(width=2, color='#8B4513'))
        ))
        fig_acc.update_layout(
            plot_bgcolor=plot_bg,
            paper_bgcolor=plot_paper,
            font=dict(color=font_color, family='Inter'),
            xaxis=dict(
                title=translate('Epoch', lang_code),
                gridcolor=grid_color, tickmode='linear'),
            yaxis=dict(
                title=translate('Accuracy (%)', lang_code),
                gridcolor=grid_color, range=[70, 95]),
            legend=dict(bgcolor='rgba(0,0,0,0)',
                        bordercolor=grid_color),
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode='x unified'
        )
        st.plotly_chart(fig_acc, use_container_width=True)

    with c2:
        st.markdown(f"""
        <div class="card card-red" style="margin-bottom:0.5rem">
            <h4>📉 {translate('Model Loss Over Epochs', lang_code)}</h4>
        </div>
        """, unsafe_allow_html=True)
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(
            x=epochs,
            y=TRAINING_HISTORY["loss"],
            mode='lines+markers',
            name=translate('Training Loss', lang_code),
            line=dict(color='#E63946', width=3),
            marker=dict(size=8, symbol='circle',
                        line=dict(width=2, color='#8B0000'))
        ))
        fig_loss.add_trace(go.Scatter(
            x=epochs,
            y=TRAINING_HISTORY["val_loss"],
            mode='lines+markers',
            name=translate('Validation Loss', lang_code),
            line=dict(color='#4895EF', width=3),
            marker=dict(size=8, symbol='diamond',
                        line=dict(width=2, color='#00008B'))
        ))
        fig_loss.update_layout(
            plot_bgcolor=plot_bg,
            paper_bgcolor=plot_paper,
            font=dict(color=font_color, family='Inter'),
            xaxis=dict(
                title=translate('Epoch', lang_code),
                gridcolor=grid_color, tickmode='linear'),
            yaxis=dict(
                title=translate('Loss', lang_code),
                gridcolor=grid_color),
            legend=dict(bgcolor='rgba(0,0,0,0)',
                        bordercolor=grid_color),
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode='x unified'
        )
        st.plotly_chart(fig_loss, use_container_width=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="card card-blue">
        <h4>🌱 {translate('Dataset Distribution by Disease Class', lang_code)}</h4>
    </div>
    """, unsafe_allow_html=True)

    disease_counts = {
        "Pepper - Bacterial Spot": 997,
        "Pepper - Healthy": 1478,
        "Potato - Early Blight": 1000,
        "Potato - Late Blight": 1000,
        "Potato - Healthy": 152,
        "Tomato - Bacterial Spot": 2127,
        "Tomato - Early Blight": 1000,
        "Tomato - Late Blight": 1909,
        "Tomato - Leaf Mold": 952,
        "Tomato - Septoria Leaf Spot": 1771,
        "Tomato - Spider Mites": 1676,
        "Tomato - Target Spot": 1404,
        "Tomato - Yellow Leaf Curl Virus": 3209,
        "Tomato - Mosaic Virus": 373,
        "Tomato - Healthy": 1591
    }

    colors = ['#52B788' if 'Healthy' in k
              else '#E63946' if 'Virus' in k
              else '#F4A261'
              for k in disease_counts.keys()]

    fig_bar = go.Figure(go.Bar(
        x=list(disease_counts.values()),
        y=list(disease_counts.keys()),
        orientation='h',
        marker=dict(color=colors, opacity=0.85),
        text=list(disease_counts.values()),
        textposition='outside',
        textfont=dict(color=font_color, size=11)
    ))
    fig_bar.update_layout(
        plot_bgcolor=plot_bg,
        paper_bgcolor=plot_paper,
        font=dict(color=font_color, family='Inter'),
        xaxis=dict(
            title=translate('Number of Images', lang_code),
            gridcolor=grid_color),
        yaxis=dict(gridcolor=grid_color),
        margin=dict(l=10, r=60, t=10, b=10),
        height=520
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"""
    <div class="footer">
        <span>🌿 AgroVision</span> |
        <span>Asansol Engineering College</span> |
        MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)