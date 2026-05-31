import streamlit as st
import numpy as np
from PIL import Image
import json
import os
import plotly.graph_objects as go
from deep_translator import GoogleTranslator

try:
    import tflite_runtime.interpreter as tflite
    USE_TFLITE = True
except ImportError:
    import tensorflow as tf
    USE_TFLITE = False

# ─── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="AgroVision",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Load CSS ────────────────────────────────────────────
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

# ─── Font Awesome ─────────────────────────────────────────
st.markdown("""
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
""", unsafe_allow_html=True)

# ─── Theme State ─────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

theme_attr = "dark" if st.session_state.dark_mode else "light"
st.markdown(f"""
<script>
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
    "accuracy":     [0.7370, 0.8356, 0.8518, 0.8607,
                     0.8770, 0.8810, 0.8853, 0.8890],
    "val_accuracy": [0.8527, 0.8719, 0.8814, 0.8797,
                     0.9005, 0.8971, 0.8993, 0.8986],
    "loss":         [0.8050, 0.4925, 0.4305, 0.3935,
                     0.3602, 0.3434, 0.3310, 0.3186],
    "val_loss":     [0.4455, 0.3976, 0.3449, 0.3492,
                     0.2976, 0.3054, 0.2906, 0.2888]
}

# ─── Load Model ──────────────────────────────────────────
@st.cache_resource
def load_model():
    base_dir   = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, "..", "model", "crop_disease_model.tflite")
    model_path = os.path.abspath(model_path)
    if USE_TFLITE:
        interpreter = tflite.Interpreter(model_path=model_path)
    else:
        interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

@st.cache_resource
def load_class_names():
    base_dir  = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "..", "model", "class_names.json")
    json_path = os.path.abspath(json_path)
    with open(json_path, "r") as f:
        return json.load(f)

def predict(image, interpreter, class_names):
    img       = image.resize((224, 224))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    inp       = interpreter.get_input_details()
    out       = interpreter.get_output_details()
    interpreter.set_tensor(inp[0]['index'], img_array)
    interpreter.invoke()
    preds     = interpreter.get_tensor(out[0]['index'])[0]
    top3      = np.argsort(preds)[::-1][:3]
    return [(class_names[i], float(preds[i]) * 100) for i in top3]

def clean_name(cn):
    return cn.replace('___', ' ').replace('__', ' ').replace('_', ' ')

# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo-row">
            <div class="sidebar-icon">
                <i class="fa-solid fa-leaf"></i>
            </div>
            <span class="sidebar-logo-text">AgroVision</span>
        </div>
        <div class="sidebar-tagline">
            AI-Powered Crop Disease Detection
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_icon  = "☀️" if st.session_state.dark_mode else "🌙"
    btn_label = "Switch to Light Mode" if st.session_state.dark_mode \
                else "Switch to Dark Mode"
    if st.button(f"{btn_icon}  {btn_label}", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown(
        '<div class="sidebar-section-label">'
        '<i class="fa-solid fa-compass" style="margin-right:6px"></i>'
        'Navigate</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "",
        options=["🏠  Home", "ℹ️  About", "📖  How to Use", "📊  Statistics"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-section-label">'
        '<i class="fa-solid fa-globe" style="margin-right:6px"></i>'
        'Language / भाषा</div>',
        unsafe_allow_html=True
    )
    selected_language = st.selectbox(
        "", list(LANGUAGES.keys()), label_visibility="collapsed"
    )
    lang_code = LANGUAGES[selected_language]

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="sidebar-section-label">'
        '<i class="fa-solid fa-chart-bar" style="margin-right:6px"></i>'
        'Quick Stats</div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <div class="stat-grid">
        <div class="stat-card-mini">
            <span class="stat-icon">🎯</span>
            <span class="stat-value">90.05%</span>
            <span class="stat-label">Accuracy</span>
        </div>
        <div class="stat-card-mini">
            <span class="stat-icon">🌱</span>
            <span class="stat-value">3</span>
            <span class="stat-label">Crops</span>
        </div>
        <div class="stat-card-mini">
            <span class="stat-icon">🦠</span>
            <span class="stat-value">15</span>
            <span class="stat-label">Diseases</span>
        </div>
        <div class="stat-card-mini">
            <span class="stat-icon">🌐</span>
            <span class="stat-value">24</span>
            <span class="stat-label">Languages</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# PLOT THEME HELPER
# ════════════════════════════════════════════════════════
def plot_theme():
    if st.session_state.dark_mode:
        return {"bg": "#161B27", "paper": "#161B27",
                "font": "#E8EDF5", "grid": "#1E2A3A"}
    else:
        return {"bg": "#FFFFFF", "paper": "#FFFFFF",
                "font": "#1A2332", "grid": "#D0DAE8"}

# ════════════════════════════════════════════════════════
# HOME PAGE
# ════════════════════════════════════════════════════════
if "Home" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            <i class="fa-solid fa-leaf"
               style="font-size:3rem;margin-right:0.5rem;
                      -webkit-text-fill-color:#00D4AA"></i>
            AgroVision
        </div>
        <div class="hero-subtitle">
            {translate('AI-Powered Crop Disease Detection & Treatment System', lang_code)}
        </div>
        <div class="stat-row">
            <span class="stat-pill">
                <i class="fa-solid fa-bullseye"></i>&nbsp;90.05% Accuracy
            </span>
            <span class="stat-pill">
                <i class="fa-solid fa-seedling"></i>&nbsp;3 Crops
            </span>
            <span class="stat-pill">
                <i class="fa-solid fa-virus"></i>&nbsp;15 Diseases
            </span>
            <span class="stat-pill">
                <i class="fa-solid fa-globe"></i>&nbsp;24 Languages
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown(f"""
        <div class="card card-green">
            <h4>
                <i class="fa-solid fa-cloud-arrow-up"
                   style="color:var(--primary)"></i>
                {translate('Upload Leaf Image', lang_code)}
            </h4>
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
        <div class="card card-blue">
            <h4>
                <i class="fa-solid fa-magnifying-glass"
                   style="color:var(--info)"></i>
                {translate('Detection Results', lang_code)}
            </h4>
            <p>{translate('AI analysis results will appear here after uploading an image.', lang_code)}</p>
        </div>
        """, unsafe_allow_html=True)

        if uploaded_file:
            with st.spinner(translate("Analyzing leaf with AI...", lang_code)):
                interpreter = load_model()
                class_names = load_class_names()
                results     = predict(image, interpreter, class_names)

            top_class, top_conf = results[0]
            display_name    = clean_name(top_class)
            translated_name = translate(display_name, lang_code)
            conf_label      = translate("Confidence Score", lang_code)

            if "healthy" in top_class.lower():
                st.markdown(f"""
                <div class="result-healthy">
                    <div class="result-name">
                        <i class="fa-solid fa-circle-check"
                           style="color:#2ED573"></i>
                        &nbsp;{translated_name}
                    </div>
                    <div class="result-conf">{top_conf:.1f}%</div>
                    <div class="result-label">{conf_label}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-disease">
                    <div class="result-name">
                        <i class="fa-solid fa-triangle-exclamation"
                           style="color:#FFA502"></i>
                        &nbsp;{translated_name}
                    </div>
                    <div class="result-conf">{top_conf:.1f}%</div>
                    <div class="result-label">{conf_label}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"**{translate('Top 3 Predictions', lang_code)}:**")
            for name, conf in results:
                label = translate(clean_name(name), lang_code)
                st.progress(int(conf))
                st.caption(f"{label} — {conf:.1f}%")
        else:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;">
                <i class="fa-solid fa-leaf"
                   style="font-size:3rem;color:var(--primary);
                          opacity:0.4;margin-bottom:1rem;
                          display:block"></i>
                <p style="color:var(--text-muted)">
                    {translate('Upload a leaf image to get started', lang_code)}
                </p>
            </div>
            """, unsafe_allow_html=True)

    if uploaded_file and results:
        st.markdown("---")
        st.markdown(f"""
        <div class="card card-green">
            <h4>
                <i class="fa-solid fa-notes-medical"
                   style="color:var(--primary)"></i>
                &nbsp;{translate('Disease Information & Treatment Guide', lang_code)}
            </h4>
        </div>
        """, unsafe_allow_html=True)

        top_class = results[0][0]
        info      = DISEASE_INFO.get(top_class)

        if info:
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.markdown(f"""
                <div class="card card-blue">
                    <h4>
                        <i class="fa-solid fa-circle-info"
                           style="color:var(--info)"></i>
                        &nbsp;{translate('Description', lang_code)}
                    </h4>
                    <p>{translate(info['description'], lang_code)}</p>
                </div>
                <div class="card card-orange">
                    <h4>
                        <i class="fa-solid fa-microscope"
                           style="color:var(--gold)"></i>
                        &nbsp;{translate('Symptoms', lang_code)}
                    </h4>
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
                    <h4>
                        <i class="fa-solid fa-kit-medical"
                           style="color:var(--danger)"></i>
                        &nbsp;{translate('Treatment', lang_code)}
                    </h4>
                    <ul>{t_items}</ul>
                </div>
                <div class="card card-green">
                    <h4>
                        <i class="fa-solid fa-shield-halved"
                           style="color:var(--success)"></i>
                        &nbsp;{translate('Prevention', lang_code)}
                    </h4>
                    <ul>{p_items}</ul>
                </div>
                """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">
        <i class="fa-solid fa-leaf" style="color:var(--primary)"></i>
        &nbsp;<span>AgroVision</span> —
        {translate('AI-Powered Crop Disease Detection & Treatment System', lang_code)}
        &nbsp;|&nbsp;<span>Asansol Engineering College</span>&nbsp;|&nbsp;MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# ABOUT PAGE
# ════════════════════════════════════════════════════════
elif "About" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            <i class="fa-solid fa-circle-info"
               style="font-size:2.5rem;margin-right:0.5rem;
                      -webkit-text-fill-color:#F4C430"></i>
            {translate('About AgroVision', lang_code)}
        </div>
        <div class="hero-subtitle">
            {translate('AI-Powered Crop Disease Detection & Treatment System', lang_code)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(f"""
        <div class="card card-green">
            <h4>
                <i class="fa-solid fa-bullseye"
                   style="color:var(--primary)"></i>
                &nbsp;{translate('Project Overview', lang_code)}
            </h4>
            <p>{translate('AgroVision is an AI-powered crop disease detection and multilingual treatment advisory system built as an MCA final year project. It uses deep learning and computer vision to identify diseases in crop leaves and provides detailed treatment and prevention guidance in 24 Indian languages.', lang_code)}</p>
        </div>
        <div class="card card-blue">
            <h4>
                <i class="fa-solid fa-crosshairs"
                   style="color:var(--info)"></i>
                &nbsp;{translate('Objective', lang_code)}
            </h4>
            <p>{translate('To help farmers and agricultural workers quickly identify crop diseases using smartphone cameras and get actionable treatment advice in their native language — making AI accessible to rural India.', lang_code)}</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card card-orange">
            <h4>
                <i class="fa-solid fa-layer-group"
                   style="color:var(--gold)"></i>
                &nbsp;{translate('Technology Stack', lang_code)}
            </h4>
            <p>
            <i class="fa-solid fa-brain" style="color:var(--primary)"></i>
            &nbsp;<b>AI Model:</b> MobileNetV2 (Transfer Learning)<br>
            <i class="fa-solid fa-bolt" style="color:var(--gold)"></i>
            &nbsp;<b>Framework:</b> TensorFlow 2.13 / TFLite<br>
            <i class="fa-solid fa-palette" style="color:var(--info)"></i>
            &nbsp;<b>Frontend:</b> Streamlit<br>
            <i class="fa-solid fa-globe" style="color:var(--success)"></i>
            &nbsp;<b>Translation:</b> Google Translate API<br>
            <i class="fa-solid fa-microchip" style="color:var(--warning)"></i>
            &nbsp;<b>Training:</b> Google Colab (T4 GPU)<br>
            <i class="fa-solid fa-database" style="color:var(--danger)"></i>
            &nbsp;<b>Dataset:</b> PlantVillage (20,639 images)<br>
            <i class="fa-brands fa-python" style="color:var(--primary)"></i>
            &nbsp;<b>Language:</b> Python 3.11
            </p>
        </div>
        <div class="card card-red">
            <h4>
                <i class="fa-solid fa-chart-line"
                   style="color:var(--danger)"></i>
                &nbsp;{translate('Model Performance', lang_code)}
            </h4>
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
    <div class="card card-green" style="margin-bottom:1rem">
        <h4>
            <i class="fa-solid fa-users"
               style="color:var(--primary)"></i>
            &nbsp;{translate('Meet The Team', lang_code)}
        </h4>
        <p style="color:var(--text-muted)">
            {translate('Asansol Engineering College | Department of MCA | 2025-2026', lang_code)}
        </p>
    </div>
    """, unsafe_allow_html=True)

    team = [
        {"name": "Akanksha Singh",  "roll": "108710240003",
         "role": "Problem Definition & Dataset",  "icon": "👩‍💻"},
        {"name": "Ankita Kumari",   "roll": "108710240006",
         "role": "Model Architecture & Training", "icon": "👩‍🔬"},
        {"name": "Bipasa Nath",     "roll": "108710240010",
         "role": "TFLite Conversion & Backend",   "icon": "👩‍💼"},
        {"name": "Shifa Iqbal",     "roll": "108710240033",
         "role": "UI Development & Deployment",   "icon": "👩‍🎨"},
    ]

    cols = st.columns(4, gap="medium")
    for i, member in enumerate(team):
        with cols[i]:
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar">{member['icon']}</div>
                <div class="team-name">{member['name']}</div>
                <div class="team-roll">{member['roll']}</div>
                <div class="team-role">{member['role']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="footer">
        <i class="fa-solid fa-leaf" style="color:var(--primary)"></i>
        &nbsp;<span>AgroVision</span>&nbsp;|&nbsp;
        <span>Asansol Engineering College</span>&nbsp;|&nbsp;MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# HOW TO USE PAGE
# ════════════════════════════════════════════════════════
elif "How to Use" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            <i class="fa-solid fa-book-open"
               style="font-size:2.5rem;margin-right:0.5rem;
                      -webkit-text-fill-color:#4FACFE"></i>
            {translate('How to Use', lang_code)}
        </div>
        <div class="hero-subtitle">
            {translate('Follow these simple steps to detect crop diseases instantly', lang_code)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    steps = [
        {"num": "1",
         "icon": '<i class="fa-solid fa-globe" style="color:var(--primary)"></i>',
         "title": translate("Select Your Language", lang_code),
         "desc":  translate("From the sidebar on the left, select your preferred language from the dropdown. AgroVision supports 24 Indian languages including Hindi, Bengali, Tamil, Telugu and more.", lang_code)},
        {"num": "2",
         "icon": '<i class="fa-solid fa-house" style="color:var(--gold)"></i>',
         "title": translate("Go to Home Page", lang_code),
         "desc":  translate("Click on Home in the navigation menu in the sidebar to go to the main disease detection page.", lang_code)},
        {"num": "3",
         "icon": '<i class="fa-solid fa-camera" style="color:var(--info)"></i>',
         "title": translate("Take or Choose a Photo", lang_code),
         "desc":  translate("Click the Upload button and select a clear photo of the affected crop leaf. Make sure the leaf is clearly visible and well lit. Supported formats: JPG, JPEG, PNG.", lang_code)},
        {"num": "4",
         "icon": '<i class="fa-solid fa-bolt" style="color:var(--warning)"></i>',
         "title": translate("Wait for AI Analysis", lang_code),
         "desc":  translate("AgroVision's AI model analyzes your leaf image automatically using deep learning. This takes just 1-2 seconds.", lang_code)},
        {"num": "5",
         "icon": '<i class="fa-solid fa-magnifying-glass" style="color:var(--success)"></i>',
         "title": translate("View Detection Results", lang_code),
         "desc":  translate("The detected disease name appears with a confidence score. Green means healthy, Red means disease detected. Top 3 predictions are also shown.", lang_code)},
        {"num": "6",
         "icon": '<i class="fa-solid fa-kit-medical" style="color:var(--danger)"></i>',
         "title": translate("Read Treatment Guide", lang_code),
         "desc":  translate("Scroll down to see detailed disease information including description, symptoms, treatment and prevention tips — all in your selected language.", lang_code)},
    ]

    for step in steps:
        st.markdown(f"""
        <div class="step-card">
            <div class="step-num">{step['num']}</div>
            <div>
                <div class="step-title">
                    {step['icon']}&nbsp;{step['title']}
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
            <h4>
                <i class="fa-solid fa-circle-check"
                   style="color:var(--success)"></i>
                &nbsp;{translate('Tips for Best Results', lang_code)}
            </h4>
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
            <h4>
                <i class="fa-solid fa-circle-xmark"
                   style="color:var(--danger)"></i>
                &nbsp;{translate('Common Mistakes to Avoid', lang_code)}
            </h4>
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
        <h4>
            <i class="fa-solid fa-seedling"
               style="color:var(--gold)"></i>
            &nbsp;{translate('Supported Crops & Diseases', lang_code)}
        </h4>
        <p>🌶️ <b>Pepper</b> — {translate('Bacterial Spot, Healthy', lang_code)}</p>
        <p>🥔 <b>Potato</b> — {translate('Early Blight, Late Blight, Healthy', lang_code)}</p>
        <p>🍅 <b>Tomato</b> — {translate('Bacterial Spot, Early Blight, Late Blight, Leaf Mold, Septoria Leaf Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus, Healthy', lang_code)}</p>
    </div>
    <div class="footer">
        <i class="fa-solid fa-leaf" style="color:var(--primary)"></i>
        &nbsp;<span>AgroVision</span>&nbsp;|&nbsp;
        <span>Asansol Engineering College</span>&nbsp;|&nbsp;MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# STATISTICS PAGE
# ════════════════════════════════════════════════════════
elif "Statistics" in page:

    st.markdown(f"""
    <div class="hero">
        <div class="hero-logo">
            <i class="fa-solid fa-chart-bar"
               style="font-size:2.5rem;margin-right:0.5rem;
                      -webkit-text-fill-color:#F4C430"></i>
            {translate('Statistics', lang_code)}
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

    pt     = plot_theme()
    epochs = list(range(1, 9))
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown(f"""
        <div class="card card-green" style="margin-bottom:0.5rem">
            <h4>
                <i class="fa-solid fa-arrow-trend-up"
                   style="color:var(--primary)"></i>
                &nbsp;{translate('Model Accuracy Over Epochs', lang_code)}
            </h4>
        </div>
        """, unsafe_allow_html=True)
        fig_acc = go.Figure()
        fig_acc.add_trace(go.Scatter(
            x=epochs,
            y=[a*100 for a in TRAINING_HISTORY["accuracy"]],
            mode='lines+markers',
            name=translate('Training Accuracy', lang_code),
            line=dict(color='#00D4AA', width=3),
            marker=dict(size=8, symbol='circle', color='#00D4AA',
                        line=dict(width=2, color='#007A60'))
        ))
        fig_acc.add_trace(go.Scatter(
            x=epochs,
            y=[a*100 for a in TRAINING_HISTORY["val_accuracy"]],
            mode='lines+markers',
            name=translate('Validation Accuracy', lang_code),
            line=dict(color='#F4C430', width=3),
            marker=dict(size=8, symbol='diamond', color='#F4C430',
                        line=dict(width=2, color='#9A7A00'))
        ))
        fig_acc.update_layout(
            plot_bgcolor=pt["bg"], paper_bgcolor=pt["paper"],
            font=dict(color=pt["font"], family='Inter'),
            xaxis=dict(title=translate('Epoch', lang_code),
                       gridcolor=pt["grid"], tickmode='linear', showgrid=True),
            yaxis=dict(title=translate('Accuracy (%)', lang_code),
                       gridcolor=pt["grid"], range=[70, 95], showgrid=True),
            legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor=pt["grid"]),
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode='x unified'
        )
        st.plotly_chart(fig_acc, use_container_width=True)

    with c2:
        st.markdown(f"""
        <div class="card card-red" style="margin-bottom:0.5rem">
            <h4>
                <i class="fa-solid fa-arrow-trend-down"
                   style="color:var(--danger)"></i>
                &nbsp;{translate('Model Loss Over Epochs', lang_code)}
            </h4>
        </div>
        """, unsafe_allow_html=True)
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(
            x=epochs, y=TRAINING_HISTORY["loss"],
            mode='lines+markers',
            name=translate('Training Loss', lang_code),
            line=dict(color='#FF4757', width=3),
            marker=dict(size=8, symbol='circle', color='#FF4757',
                        line=dict(width=2, color='#A00010'))
        ))
        fig_loss.add_trace(go.Scatter(
            x=epochs, y=TRAINING_HISTORY["val_loss"],
            mode='lines+markers',
            name=translate('Validation Loss', lang_code),
            line=dict(color='#4FACFE', width=3),
            marker=dict(size=8, symbol='diamond', color='#4FACFE',
                        line=dict(width=2, color='#005A9E'))
        ))
        fig_loss.update_layout(
            plot_bgcolor=pt["bg"], paper_bgcolor=pt["paper"],
            font=dict(color=pt["font"], family='Inter'),
            xaxis=dict(title=translate('Epoch', lang_code),
                       gridcolor=pt["grid"], tickmode='linear', showgrid=True),
            yaxis=dict(title=translate('Loss', lang_code),
                       gridcolor=pt["grid"], showgrid=True),
            legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor=pt["grid"]),
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode='x unified'
        )
        st.plotly_chart(fig_loss, use_container_width=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="card card-blue">
        <h4>
            <i class="fa-solid fa-chart-bar"
               style="color:var(--info)"></i>
            &nbsp;{translate('Dataset Distribution by Disease Class', lang_code)}
        </h4>
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

    bar_colors = [
        '#2ED573' if 'Healthy' in k
        else '#FF4757' if 'Virus' in k
        else '#00D4AA'
        for k in disease_counts.keys()
    ]

    fig_bar = go.Figure(go.Bar(
        x=list(disease_counts.values()),
        y=list(disease_counts.keys()),
        orientation='h',
        marker=dict(color=bar_colors, opacity=0.9, line=dict(width=0)),
        text=list(disease_counts.values()),
        textposition='outside',
        textfont=dict(color=pt["font"], size=11)
    ))
    fig_bar.update_layout(
        plot_bgcolor=pt["bg"], paper_bgcolor=pt["paper"],
        font=dict(color=pt["font"], family='Inter'),
        xaxis=dict(title=translate('Number of Images', lang_code),
                   gridcolor=pt["grid"], showgrid=True),
        yaxis=dict(gridcolor=pt["grid"], showgrid=False),
        margin=dict(l=10, r=70, t=10, b=10),
        height=520
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"""
    <div class="footer">
        <i class="fa-solid fa-leaf" style="color:var(--primary)"></i>
        &nbsp;<span>AgroVision</span>&nbsp;|&nbsp;
        <span>Asansol Engineering College</span>&nbsp;|&nbsp;MCA 2025-2026
    </div>
    """, unsafe_allow_html=True)