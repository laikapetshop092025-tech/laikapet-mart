import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PREMIUM LOOK (CSS) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    /* Sabse upar ka menu hide karne ke liye */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Decent Background & Card Styling */
    .main { background-color: #F8F9FB; }
    
    div[data-testid="stMetricValue"] {
        font-size: 42px; 
        color: #2E5BFF; 
        font-weight: 800;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 18px; 
        color: #555; 
        font-weight: 600;
        text-transform: uppercase;
    }
    
    /* Metrics Box - Ekdum Clean Look */
    [data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #EAECEF;
        transition: transform 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0px 15px 35px rgba(46, 91, 255, 0.1);
    }

    /* Professional Sidebar & Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #2E5BFF 0%, #1435A1 100%);
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(46, 91, 255, 0.3);
    }

    .main-title {
        text-align: center; 
        background: -webkit-linear-gradient(#2E5BFF, #1435A1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 48px; 
        font-weight: 900;
        margin-top: -10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO SECTION (Yahan aapka pink logo show hoga) ---
col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    # Agar aapne GitHub par 'logo.webp' naam se file dali hai toh yahan naam change karein
    try:
        st.image("1000302358.webp", width=160)
    except:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>👑</h1>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #777; font-size: 16px; letter-spacing: 2px;'>QUALITY PET CARE SINCE 2025</p>", unsafe_allow_html=True)

# --- 3. DATA & LOGIN LOGIC (Original - No Change) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# Auto-Logout (10 Mins)
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.markdown("### 🔐 Secure Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN NOW"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout Session"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Clean & Attractive Style) ---
if menu == "📊 Dashboard":
    st.markdown("### 📊 Business Performance Summary")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    m1, m2 = st.columns(2)
    with m1:
        st.metric("Total Revenue", f"₹{int(t_sale)}")
        st.metric("Total Investment", f"₹{int(t_pur)}")
    with m2:
        st.metric("Net Earnings", f"₹{int(n_prof)}")
        st.metric("Total Overhead", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        if t_udh > 0: st.error(f"🚨 ALERT: Company Dues Pending: ₹{int(t_udh)}")

# --- BAAKI SAB ORIGINAL LOGIC (Purchase, Billing, etc. - NO CHANGE) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine Date")
        if st.form_submit_button("Save Record"):
            st.session_state.pet_records.append({"Customer": n, "Phone": ph, "Breed": b, "Age": a, "Next Vaccine": v})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    st.subheader("👤 Staff Management")
    new_u = st.text_input("New Staff ID")
    new_p = st.text_input("Set Password", type="password")
    if st.button("CREATE ACCOUNT"):
        if new_u and new_p: st.session_state.users[new_u] = new_p; st.success("Account Ready!")
    
    st.write("---")
    st.subheader("🏢 Udhaar (Company Dues)")
    with st.form("udh"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Terminal")
    if st.session_state.inventory:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
        qty = st.number_input("Quantity", min_value=0.1); price = st.number_input("Price", min_value=1)
        if st.button("GENERATE BILL"):
            inv = st.session_state.inventory[item]
            if qty <= inv['qty']:
                st.session_state.inventory[item]['qty'] -= qty
                st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*price, "profit": (price-inv['p_price'])*qty})
                st.rerun()
