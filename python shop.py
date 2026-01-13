import streamlit as st

st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.title("🐾 LAIKA PET MART")
st.write("Welcome, *Ayush Saxena*! Aapki App Live Hai.")

# 4 MNC Dashboard Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("TOTAL SALES", "Rs. 0")
col2.metric("TOTAL PURCHASE", "Rs. 0")
col3.metric("GROSS PROFIT", "Rs. 0")
col4.metric("NET PROFIT", "Rs. 0")

st.sidebar.title("Menu")
menu = st.sidebar.radio("Navigate", ["Dashboard", "Billing", "Stock Entry", "Udhaar Tracker"])
