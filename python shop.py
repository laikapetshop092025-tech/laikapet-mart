import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & LOOK ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 40px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 10px; background-color: #2E5BFF; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT LOGIC (10 Minutes) ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

# --- 4. LOGIN SYSTEM (CASE-SENSITIVE FIX) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Secure Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u_id = st.text_input("Username (Example: Laika)").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN NOW"):
            # Yahan hum check kar rahe hain ki kya details wahi hain jo aap daal rahe hain
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Ghalat ID/Password! Username 'Laika' (L bada) aur Password sahi se bhariye.")
    st.stop()

# --- 5. TOP BRANDING & LOGO ---
st.markdown("<h1 style='text-align: center; margin-bottom: -10px;'>👑</h1>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>QUALITY PET CARE SINCE 2025</p>", unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 7. DASHBOARD SECTIONS ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2 = st.columns(2)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c1.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c2.metric("NET PROFIT", f"₹{int(n_prof)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f", clear_on_submit=True):
        n = st.text_input("Item Name"); r = st.number_input("Purchase Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()
    if st.session_state.inventory:
        st.subheader("Current Stock List")
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Price": v['p_price']} for k, v in st.session_state.inventory.items()]))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if not st.session_state.inventory: st.warning("Stock khali hai!")
    else:
        with st.form("bill_f"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            st.info(f"Available: {st.session_state.inventory[item]['qty']}")
            qty = st.number_input("Qty", min_value=0.1); price = st.number_input("Price", min_value=1)
            if st.form_submit_button("GENERATE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*price, "profit": (price-inv['p_price'])*qty})
                    st.rerun()

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer Name"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Name": n, "Breed": b, "Vaccine": v})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin")
    st.subheader("🏢 Company Udhaar Record")
    with st.form("udh"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))
