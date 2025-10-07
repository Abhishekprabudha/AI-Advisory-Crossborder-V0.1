import streamlit as st
import requests
import json
from rapidfuzz import process

# --- Page Config ---
st.set_page_config(page_title="ATS Validator", layout="wide")

# --- Remove Top Padding ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>📦 ATS – Cross-Border Tariff Validator</h1>", unsafe_allow_html=True)

# --- API KEY for Broker Genius ---
API_KEY = "8c613a45-7d06-4c4a-9761-d67706f2372e"  # Replace with your actual API key

# --- Load Fallback JSON (hs_lookup.json) ---
@st.cache_data
def load_fallback_json():
    with open("hs_lookup.json", "r") as f:
        return json.load(f)

fallback_data = load_fallback_json()

# --- Fuzzy Search from JSON ---
def fuzzy_match(query):
    choices = [item["description"] for item in fallback_data]
    best, score, idx = process.extractOne(query, choices)
    match = fallback_data[idx]
    return {
        "hs_code": match["code"],
        "description": match["description"],
        "tariff_percent": match.get("duty", 0.0)
    }

# --- Primary API Call ---
def query_api(product_input, country_code):
    url = "https://api.brokergenius.ai/classify"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "description": product_input,
        "country": country_code.upper()
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            return {
                "hs_code": result["code"],
                "description": result["description"],
                "tariff_percent": result.get("duty", 0.0)
            }
    except:
        pass
    return None

# --- Country Map for ISO codes ---
country_map = {
    "United States": "US", "India": "IN", "Germany": "DE",
    "Singapore": "SG", "Vietnam": "VN", "UAE": "AE"
}

# --- Initialize Session State ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "chat" not in st.session_state:
    st.session_state.chat = []
if "partial" not in st.session_state:
    st.session_state.partial = {}
if "results" not in st.session_state:
    st.session_state.results = []

# --- Layout ---
col1, col2 = st.columns([1, 1])

# === LEFT PANEL ===
with col1:
    st.markdown("### 💬 Chat")
    for msg in st.session_state.chat:
        st.markdown(msg)

    # Step 1: Ask for product
    if st.session_state.step == 1:
        product_input = st.text_input("What are you shipping?")
        if product_input:
            st.session_state.partial["product"] = product_input
            st.session_state.chat.append(f"**You:** {product_input}")
            st.session_state.chat.append("**Bot:** Please select the destination country.")
            st.session_state.step = 2
            st.rerun()

    # Step 2: Ask for destination country
    elif st.session_state.step == 2:
        dest_country = st.selectbox("Destination Country", list(country_map.keys()))
        if dest_country:
            st.session_state.partial["country"] = dest_country
            st.session_state.chat.append(f"**You:** {dest_country}")
            st.session_state.chat.append("**Bot:** What is the invoice value in USD?")
            st.session_state.step = 3
            st.rerun()

    # Step 3: Ask for invoice value
    elif st.session_state.step == 3:
        invoice_value = st.number_input("Invoice Value (USD)", min_value=1.0, value=1000.0, step=50.0)
        submit = st.button("Submit")
        if submit:
            st.session_state.partial["invoice"] = invoice_value
            st.session_state.chat.append(f"**You:** ${invoice_value:,.2f}")

            # Primary API
            query = st.session_state.partial["product"]
            iso = country_map[st.session_state.partial["country"]]
            result = query_api(query, iso)

            # Fallback if API fails
            if not result:
                result = fuzzy_match(query)

            result["invoice"] = invoice_value
            result["country"] = st.session_state.partial["country"]
            result["query"] = query
            result["estimated_duty"] = (result["tariff_percent"] / 100.0) * invoice_value
            st.session_state.results.append(result)
            st.session_state.chat.append("**Bot:** Classification complete. Check the right panel.")

            # Reset for next interaction
            st.session_state.partial = {}
            st.session_state.step = 1
            st.rerun()

# === RIGHT PANEL ===
with col2:
    st.markdown("""
        <h3 style='margin-top: 0.2rem; margin-bottom: 0.4rem;'>📊 Results</h3>
    """, unsafe_allow_html=True)
    if not st.session_state.results:
        st.info("Validated results will appear here.")
    else:
        for res in reversed(st.session_state.results):
            st.markdown(f"**Product:** {res['query']}")
            st.success("✅ HS Match Found")
            st.markdown(f"**HS Code:** `{res['hs_code']}`")
            st.markdown(f"**Description:** {res['description']}")
            st.markdown(f"**Destination Country:** {res['country']}")
            st.markdown(f"**Tariff %:** `{res['tariff_percent']}%`")
            st.markdown(f"**Invoice Value:** `${res['invoice']:,.2f}`")
            st.markdown(f"**Estimated Duty:** `${res['estimated_duty']:,.2f}`")
            st.markdown("---")
