import streamlit as st
import json
import difflib

# Page setup
st.set_page_config(page_title="AI Advisory", layout="wide")

st.title("🤖 AI Advisory – Harmonized Code & Duty Validator")

# Load fallback HS code data
with open("hs_lookup.json", "r") as f:
    hs_data = json.load(f)

# Product matching function
def find_best_match(user_input):
    products = [item["product"] for item in hs_data]
    matches = difflib.get_close_matches(user_input.lower(), products, n=1, cutoff=0.4)
    if matches:
        for item in hs_data:
            if item["product"] == matches[0]:
                return item
    return None

# Chat history (persists across reruns)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2-column layout: Chat (left), Result (right)
col1, col2 = st.columns([1, 1])

# Left Panel: Chat interface
with col1:
    st.subheader("💬 Ask about a shipment")

    for msg in st.session_state.chat_history:
        st.chat_message("user").write(msg)

    user_input = st.chat_input("Type your shipment description here...")

    if user_input:
        st.session_state.chat_history.append(user_input)

# Right Panel: Output result
with col2:
    st.subheader("📊 Validation Results")

    if user_input:
        result = find_best_match(user_input)

        if result:
            st.success("✅ HS Code Match Found")
            st.metric("HS Code", result["hs_code"])
            st.write(f"**Product Match:** {result['product']}")
            st.write(f"**Description:** {result['description']}")
            st.metric("Estimated Duty %", f"{result['tariff_percent']}%")

            invoice_value = 1000  # Assume fixed $1000 for now
            estimated_duty = (result["tariff_percent"] / 100.0) * invoice_value
            st.metric("Duty on $1000 Invoice", f"${estimated_duty:,.2f}")
        else:
            st.error("❌ No matching HS code found. Try using a more common product name.")
    else:
        st.info("Start by typing a sentence like: `Shipping solar panels from Vietnam to US`")
