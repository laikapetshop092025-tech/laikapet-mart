import streamlit as st

st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.title("🐾 LAIKA PET MART - MASTER ADMIN")
st.sidebar.title("Menu")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock", "💸 Udhaar"])

if menu == "📊 Dashboard":
    st.subheader("Business Health")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SALES", "Rs. 0")
    c2.metric("PURCHASE", "Rs. 0")
    c3.metric("GROSS PROFIT", "Rs. 0")
    c4.metric("NET PROFIT", "Rs. 0")
    st.info("Bhai, aapka software ab live hai! Phone par check karein.")
