import streamlit as st
import json
import difflib

# Set page layout
st.set_page_config(page_title="ATS - Tariff Validator", layout="wide")

st.title("📦 ATS Prototype – Harmonized Code & Duty Validator")

st.markdown("Type a product you're shipping and select source & destination countries. We'll find the right HS Code and estimate the duty.")

# --- Load fallback HS code data ---
with open("hs_lookup.json", "r") as f:
    hs_data = json.load(f)

# --- Helper to match product description ---
def find_best_match(user_input):
    products = [item["product"] for item in hs_data]
    matches = difflib.get_close_matches(user_input.lower(), products, n=1, cutoff=0.4)
    if matches:
        for item in hs_data:
            if item["product"] == matches[0]:
                return item
    return None

# --- UI Layout ---
col1, col2 = st.columns(2)

with col1:
    product_input = st.text_input("What are you shipping?", placeholder="e.g., lithium ion batteries")

    origin_country = st.selectbox("Country of Origin", ["Vietnam", "India", "Thailand", "China", "Germany"])
    dest_country = st.selectbox("Destination Country", ["United States", "Singapore", "Japan", "UAE", "Australia"])
    invoice_value = st.number_input("Invoice Value ($)", min_value=100.0, step=50.0, value=1000.0)

    if st.button("Validate & Estimate Duty"):
        if product_input:
            result = find_best_match(product_input)
            if result:
                st.success("✅ Match found! Here are the details:")

                colA, colB = st.columns(2)
                with colA:
                    st.metric("HS Code", result["hs_code"])
                    st.write(f"**Description:** {result['description']}")
                    st.write(f"**Product Match:** `{result['product']}`")

                with colB:
                    st.metric("Estimated Duty %", f"{result['tariff_percent']}%")
                    estimated_duty = (result["tariff_percent"] / 100.0) * invoice_value
                    st.metric("Estimated Duty ($)", f"${estimated_duty:,.2f}")

                st.markdown("---")
                st.info("📎 You can now download this information for your shipping declaration.")
            else:
                st.error("❌ Sorry, we couldn't find a match. Try a simpler product name.")
        else:
            st.warning("Please enter a product name to search.")

with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/679/679922.png", width=300)
    st.markdown("###### Powered by Streamlit • Fallback mode • No API calls")
