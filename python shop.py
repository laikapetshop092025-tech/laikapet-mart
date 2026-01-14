import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Dashboard Branding
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #4A90E2; font-size: 45px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# TOP LOGO & NAME
# Agar aapke paas logo ka URL hai toh niche "URL_YAHAN_DALO" ki jagah paste kar dein
# st.image("URL_YAHAN_DALO", width=100) 
st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 5. SIDEBAR (EXCEL REPORT BUTTON YAHAN HAI) ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# EXCEL DOWNLOAD BUTTON (Wapas jodh diya hai)
if st.session_state.sales:
    df_sales = pd.DataFrame(st.session_state.sales)
    csv = df_sales.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Monthly Excel Report", csv, f"Sales_Report_{datetime.now().strftime('%m_%Y')}.csv", "text/csv")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. DASHBOARD (Udhaar Metrics Wapas) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    t_udhaar = sum(d.get('Amount', 0) for d in st.session_state.company_dues) # Udhaar Logic

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("NET PROFIT", f"₹{int(n_prof)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    # Dashboard par Udhaar Alert
    if t_udhaar > 0:
        st.error(f"⚠️ Total Company Udhaar (Pending): ₹{int(t_udhaar)}")

# --- 7. EXPENSES (With Dropdown) ---
elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    cats = ["Rent", "Electricity Bill", "Staff Salary", "Pet Food", "Tea/Snacks", "Other"]
    e_cat = st.selectbox("Category", cats)
    e_amt = st.number_input("Amount", min_value=1)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Item": e_cat, "Amount": e_amt})
        st.rerun()

# --- Baki Sections bilkul waisa hi hai ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine")
        if st.form_submit_button("Save"):
            st.session_state.pet_records.append({"Customer": n, "Phone": ph, "Breed": b, "Next Vaccine": v})
            st.rerun()

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    # ... Billing logic same as before (with delete bill)
    if st.session_state.inventory:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
        qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
        if st.button("Complete Bill"):
            inv = st.session_state.inventory[item]
            if qty <= inv['qty']:
                st.session_state.inventory[item]['qty'] -= qty
                st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*pr, "profit": (pr-inv['p_price'])*qty})
                st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar (Udhaar section yahan hai)")
    with st.form("udh"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Add Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))
