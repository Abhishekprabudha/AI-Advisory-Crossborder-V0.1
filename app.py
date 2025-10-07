import streamlit as st
import json
import difflib

# Page config
st.set_page_config(page_title="ATS Validator", layout="wide")

# ✅ Remove Streamlit's default top padding
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center;'>📦 ATS – Cross-Border Tariff Validator</h1>", unsafe_allow_html=True)

# Load fallback HS code data
with open("hs_lookup.json", "r") as f:
    hs_data = json.load(f)

# Match input to product
def find_best_match(user_input):
    products = [item["product"] for item in hs_data]
    matches = difflib.get_close_matches(user_input.lower(), products, n=1, cutoff=0.4)
    if matches:
        for item in hs_data:
            if item["product"] == matches[0]:
                return item
    return None

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "result_history" not in st.session_state:
    st.session_state.result_history = []

# Layout: two columns (chat left, result right)
col1, col2 = st.columns([1, 1])

# === LEFT PANEL ===
with col1:
    st.markdown("### 🧠 Chat with AI Advisory")

    # Show prior chats in a scrollable container
    chat_container = st.container(height=220)
    with chat_container:
        for chat in st.session_state.chat_history:
            st.markdown(f"🧠 **You:** {chat}")

    # Input box
    user_input = st.text_area("Enter product description:", placeholder="e.g., Shipping solar panels from Vietnam to US", height=100)

    # Submit
    if st.button("Submit"):
        if user_input.strip():
            st.session_state.chat_history.append(user_input)
            result = find_best_match(user_input)

            if result:
                invoice_value = 1000
                estimated_duty = (result["tariff_percent"] / 100.0) * invoice_value
                st.session_state.result_history.append({
                    "query": user_input,
                    "hs_code": result["hs_code"],
                    "description": result["description"],
                    "product": result["product"],
                    "tariff_percent": result["tariff_percent"],
                    "estimated_duty": estimated_duty
                })
            else:
                st.session_state.result_history.append({
                    "query": user_input,
                    "error": "No matching HS code found"
                })

# === RIGHT PANEL ===
with col2:
    st.markdown("### 📊 Validated HS Code & Duty")
    result_container = st.container(height=500)
    with result_container:
        if not st.session_state.result_history:
            st.info("Results will appear here after you submit your first shipment description.")
        else:
            for res in reversed(st.session_state.result_history):
                st.markdown("---")
                st.markdown(f"**Query:** {res['query']}")

                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("✅ HS Match Found")
                    st.markdown(f"**HS Code:** `{res['hs_code']}`")
                    st.markdown(f"**Product:** {res['product']}")
                    st.markdown(f"**Description:** {res['description']}")
                    st.markdown(f"**Tariff %:** `{res['tariff_percent']}%`")
                    st.markdown(f"**Duty on $1000 Invoice:** `${res['estimated_duty']:.2f}`")
