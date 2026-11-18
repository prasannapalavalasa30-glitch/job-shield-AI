import streamlit as st
import joblib
from pathlib import Path
import re
import numpy as np
import pandas as pd

# -------------------------------------------------
# Page Configuration & Custom CSS
# -------------------------------------------------
st.set_page_config(
    page_title="AI Fake Job & Internship Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom modern CSS styling
st.markdown("""
<style>
    /* Metric Card Modern Styling */
    .metric-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 4px;
        font-family: 'Segoe UI', sans-serif;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Result Badges */
    .status-badge-safe {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 10px;
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }
    .status-badge-suspicious {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 10px;
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
    }
    .status-badge-danger {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 10px;
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    /* Tag Pills */
    .pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 4px 4px 4px 0;
    }
    .pill-red { background: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .pill-yellow { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
    .pill-blue { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    
    /* Highlighted term */
    .highlight-scam {
        background-color: #fecaca;
        color: #b91c1c;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Heuristics & Detection Engine
# -------------------------------------------------
RED_FLAG_PATTERNS = {
    "Off-Platform Redirection (Telegram/WhatsApp)": [
        "telegram", "whatsapp", "signal app", "wa.me", "t.me", "chat on whatsapp", "contact via telegram"
    ],
    "Upfront Monetary Demands / Registration Fee": [
        "processing fee", "registration fee", "security deposit", "training fee",
        "laptop deposit", "pay upfront", "refundable deposit", "software license fee",
        "courier charge", "kit charge", "joining fee"
    ],
    "Unconventional Payment / Cryptocurrency": [
        "crypto", "bitcoin", "usdt", "wire transfer", "western union",
        "google pay to personal", "phonepe upfront", "gift card"
    ],
    "Sensitive Financial Data Request": [
        "bank details", "bank account", "atm card", "credit card details", 
        "otp", "provide your bank", "passbook copy"
    ],
    "Suspicious Compensation / Quick Cash": [
        "earn 5000 daily", "earn 40,000 per week", "daily payout", "no experience 50k",
        "guaranteed income", "like youtube videos and earn", "per day 2000"
    ]
}

def load_model(model_path: Path):
    if not model_path.exists():
        return None, None
    data = joblib.load(model_path)
    return data["model"], data["vectorizer"]

def train_model(csv_path: Path, model_path: Path):
    from model import train_and_save
    train_and_save(csv_path, model_path)
    return load_model(model_path)

def preprocess_input(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text

def scan_threat_categories(text: str):
    lowered = text.lower()
    matches = {}
    found_keywords = []
    
    for category, keywords in RED_FLAG_PATTERNS.items():
        matched_in_cat = [kw for kw in keywords if kw in lowered]
        if matched_in_cat:
            matches[category] = matched_in_cat
            found_keywords.extend(matched_in_cat)
            
    # Check for free emails used as official contact
    free_email = re.findall(r"\b[\w.+-]+@(gmail|yahoo|outlook|hotmail)\.com\b", lowered)
    if free_email:
        matches["Free Email Contact for Recruitment"] = [f"@{e}.com" for e in set(free_email)]
        found_keywords.append("free webmail domain")
        
    return matches, list(set(found_keywords))

def compute_composite_risk(ml_prob: float, matches: dict) -> float:
    # Rule engine contribution: each triggered threat category contributes 15%
    cat_count = len(matches)
    rule_score = min(1.0, cat_count * 0.22)
    # 55% ML Model probability + 45% Rule engine flags
    composite = (0.55 * ml_prob) + (0.45 * rule_score)
    # Severe boost if upfront money or crypto is demanded
    if "Upfront Monetary Demands / Registration Fee" in matches:
        composite = max(composite, 0.78)
    return min(1.0, composite) * 100

def get_top_features(model, vectorizer, top_n: int = 8):
    if not hasattr(model, "coef_"):
        return []
    coef = model.coef_[0]
    top_idx = np.argsort(coef)[-top_n:][::-1]
    feature_names = np.array(vectorizer.get_feature_names_out())
    return [(feature_names[i], float(coef[i])) for i in top_idx if coef[i] > 0]

# -------------------------------------------------
# Header Section
# -------------------------------------------------
col_title, col_stat = st.columns([3, 1])
with col_title:
    st.title("🛡️ AI Fake Job & Internship Detection Shield")
    st.caption("Enterprise-grade natural language assessment combining **TF-IDF + Logistic Regression ML** with a **Deterministic Cyber Scam Heuristic Engine**.")
with col_stat:
    st.markdown("""
    <div style='background: #1e293b; padding: 10px 14px; border-radius: 8px; border: 1px solid #334155; text-align: right;'>
        <span style='color: #10b981; font-weight: bold;'>● Engine Online</span><br/>
        <small style='color: #94a3b8;'>Model: TF-IDF Bi-gram + LR</small>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.header("Security Intelligence")
    st.info("""
    **Verification Guide:**
    - 🏢 Real companies **never** ask for application or training fees.
    - 🔒 Official interviews never happen exclusively on anonymous Telegram handles.
    - 📧 Genuine recruiters contact via corporate domains (`@company.com`).
    """)
    
    st.subheader("Inspection Parameters")
    strictness = st.slider("Strictness Sensitivity", min_value=1.0, max_value=1.5, value=1.1, step=0.05,
                           help="Adjust heuristic weight multiplier for zero-tolerance security environments.")
    
    st.markdown("---")
    st.caption("Academic & Verification Prototype. Predictions are advisory risk signals.")

# -------------------------------------------------
# Model Loading
# -------------------------------------------------
BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "sample_data.csv"
MODEL_PATH = BASE_DIR / "fake_job_model.joblib"

model, vectorizer = load_model(MODEL_PATH)
if model is None:
    with st.spinner("Initializing and training NLP classifier..."):
        model, vectorizer = train_model(CSV_PATH, MODEL_PATH)
    st.toast("Classifier ready!", icon="✅")

# -------------------------------------------------
# Quick Preset Selector
# -------------------------------------------------
presets = {
    "⚡ Legitimate: Google/Stripe Software Engineering Intern": {
        "title": "Software Engineering Intern - Cloud Platforms",
        "company": "Google Technologies India Pvt Ltd",
        "desc": "Join our distributed infrastructure engineering group. You will write clean, well-tested Python/Go code, participate in architecture design reviews, and build resilient microservices with guidance from staff engineers.",
        "reqs": "Enrolled in B.Tech/M.S. in Computer Science. Strong grasp of algorithms, data structures, and REST API development. Competitive monthly stipend: ₹65,000 + benefits."
    },
    "🚨 Scam: WhatsApp Data Entry (₹40,000/week + ₹999 Laptop Security Fee)": {
        "title": "Online Data Entry Assistant (Work from Home)",
        "company": "QuickGlobal Enterprise Solutions",
        "desc": "Earn 5000 daily with simple typing assignments. No experience required. Immediate joining with guaranteed daily payout. Directly contact our HR director on WhatsApp +91-9876543210 to start your shift today.",
        "reqs": "Basic English typing. Must transfer a refundable security deposit of ₹999 for remote software kit and laptop dispatch clearance. Provide your bank account details for payroll."
    },
    "🚨 Scam: Telegram Crypto Product Review Task": {
        "title": "Cryptocurrency Community Reviewer",
        "company": "Web3 Alpha Global",
        "desc": "Review trending mobile tokens and submit 5-star ratings. Earn $300 daily in USDT. Chat on Telegram handle @CryptoTaskHR to receive assignment links. Instant payment after each completed review.",
        "reqs": "Any smartphone user. Verification fee of $30 via crypto wallet required to activate applicant vendor portal."
    }
}

st.markdown("##### 💡 1-Click Interactive Test Cases")
selected_preset_key = st.selectbox(
    "Choose a preset scenario to evaluate:",
    ["-- Custom Manual Entry --"] + list(presets.keys()),
    label_visibility="collapsed"
)

preset_data = presets.get(selected_preset_key, {})

# -------------------------------------------------
# Input Tabs
# -------------------------------------------------
tab_structured, tab_raw = st.tabs(["📋 Structured Form (Recommended)", "📄 Quick Paste Full Description"])

with tab_structured:
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        in_title = st.text_input("Job / Internship Title", value=preset_data.get("title", ""), placeholder="e.g. Machine Learning Intern")
        in_company = st.text_input("Company Name / Recruiter Profile", value=preset_data.get("company", ""), placeholder="e.g. Acme Corp (Enterprise SaaS)")
    with col_f2:
        in_reqs = st.text_area("Requirements, Stipend & Interview Mode", height=100, value=preset_data.get("reqs", ""), placeholder="e.g. Stipend: ₹25,000/month. Interview via Google Meet. Proficiency in Python.")
    
    in_desc = st.text_area("Full Job Description", height=140, value=preset_data.get("desc", ""), placeholder="Paste the role description, job duties, and application steps here...")
    
    btn_structured = st.button("🔍 Run Full Security Analysis", type="primary", use_container_width=True, key="btn_struct")

with tab_raw:
    raw_paste = st.text_area("Paste the entire raw recruitment message, email, or chat offer:", height=260,
                             placeholder="Copy and paste the entire WhatsApp text, Telegram forward, or job post here...")
    btn_raw = st.button("🔍 Analyze Raw Text", type="primary", use_container_width=True, key="btn_raw")

# -------------------------------------------------
# Execution & Analysis Logic
# -------------------------------------------------
analyze_triggered = False
target_text = ""

if btn_structured:
    combined = f"{in_title} {in_company} {in_desc} {in_reqs}".strip()
    if not combined:
        st.warning("⚠️ Please provide at least one input field or choose a preset test case.")
    else:
        target_text = combined
        analyze_triggered = True

elif btn_raw:
    if not raw_paste.strip():
        st.warning("⚠️ Please paste some text into the box to analyze.")
    else:
        target_text = raw_paste.strip()
        analyze_triggered = True

if analyze_triggered and target_text:
    cleaned = preprocess_input(target_text)
    
    # 1. Machine Learning Probability
    X_vec = vectorizer.transform([cleaned])
    ml_prob = float(model.predict_proba(X_vec)[0][1])
    
    # 2. Heuristic Rules Engine
    cat_matches, red_flags = scan_threat_categories(target_text)
    
    # 3. Composite Risk Calculation
    composite_risk = compute_composite_risk(ml_prob, cat_matches) * strictness
    composite_risk = min(100.0, max(0.0, composite_risk))
    
    # Determine Threat Level
    if composite_risk < 35.0:
        status_label = "VERIFIED LEGITIMATE / LOW RISK"
        badge_class = "status-badge-safe"
        badge_icon = "✅"
        theme_color = "#10b981"
    elif composite_risk < 65.0:
        status_label = "SUSPICIOUS / ELEVATED CAUTION"
        badge_class = "status-badge-suspicious"
        badge_icon = "⚠️"
        theme_color = "#f59e0b"
    else:
        status_label = "HIGH RISK / PROBABLE RECRUITMENT SCAM"
        badge_class = "status-badge-danger"
        badge_icon = "🚨"
        theme_color = "#ef4444"
        
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("📊 Threat Assessment Dashboard")
    
    # Status Banner
    st.markdown(f"""
    <div class="{badge_class}">
        {badge_icon} <b>VERDICT: {status_label}</b> (Calculated Risk: {composite_risk:.1f}%)
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # 3 KPI Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Composite Risk Score</div>
            <div class="metric-value" style="color: {theme_color};">{composite_risk:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">ML Model Confidence</div>
            <div class="metric-value" style="color: #38bdf8;">{ml_prob * 100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Scam Categories Matched</div>
            <div class="metric-value" style="color: #fbbf24;">{len(cat_matches)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Specific Trigger Terms</div>
            <div class="metric-value" style="color: #f87171;">{len(red_flags)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Visual Progress Bar
    st.progress(composite_risk / 100.0)
    
    # Two Columns: Detailed Breakdown
    col_left, col_right = st.columns([1.1, 0.9])
    
    with col_left:
        st.markdown("#### 🚨 Heuristic Threat Breakdown")
        if cat_matches:
            for cat, triggers in cat_matches.items():
                with st.container():
                    st.markdown(f"**• {cat}**")
                    trigger_pills = " ".join([f"<span class='pill pill-red'>{t}</span>" for t in triggers])
                    st.markdown(trigger_pills, unsafe_allow_html=True)
                    st.write("")
        else:
            st.success("✅ No direct rule-based scam patterns (money extortion, Telegram redirects, free webmail HR) detected.")
            
        st.markdown("#### 🔍 Influential Lexical Features (TF-IDF NLP Evidence)")
        top_words = get_top_features(model, vectorizer, top_n=6)
        if top_words:
            feat_df = pd.DataFrame(top_words, columns=["Scam Correlated Word/Bigram", "Model Coefficient Weight"])
            st.dataframe(feat_df, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("#### 🛡️ Student Safety Protocol & Action Checklist")
        if composite_risk >= 50:
            st.error("""
            **IMMEDIATE PRECAUTIONS REQUIRED:**
            1. ⛔ **Do NOT send money:** Genuine employers will NEVER ask for laptop deposits, document verification fees, or training charges.
            2. ⛔ **Do NOT share OTP or Bank Credentials:** Do not provide cancelled cheques or bank logins.
            3. ⛔ **Avoid anonymous chat migration:** Refuse to conduct formal interviews exclusively over Telegram or personal WhatsApp.
            4. 🔍 **Verify Domain:** Check if the recruiter's email matches the verified domain on LinkedIn.
            """)
        else:
            st.info("""
            **STANDARD VERIFICATION STEPS:**
            1. Search the company on LinkedIn and verify their current active employees.
            2. Verify that the interview link uses Google Meet, Zoom, or Microsoft Teams with an official invite.
            3. Ensure compensation is documented in a formal written Offer Letter on company letterhead.
            """)
            
        with st.expander("ℹ️ How did the Hybrid Engine calculate this?"):
            st.write(f"""
            - **Machine Learning Layer (55% weight):** Extracted unigram and bigram TF-IDF sparse features, evaluated against a trained balanced Logistic Regression model. (Raw score: `{ml_prob*100:.1f}%`).
            - **Heuristic Threat Layer (45% weight):** Scanned for high-severity extortion signals ({len(cat_matches)} threat patterns discovered).
            """)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>
    AI Fake Job & Internship Detection System • Machine Learning & Heuristic Security Gateway • Academic Capstone 2026
</div>
""", unsafe_allow_html=True)
