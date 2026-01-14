import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 35px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 10px; background-color: #2E5BFF; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 40px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. LOGIN & AUTO-LOGOUT ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "💰 Expenses", "⚙️ Admin Settings", "📋 Live Stock", "📅 Report Center"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (CASH & ONLINE ADDED) ---
if menu == "📊 Dashboard":
    st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)
    
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_cash = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Cash')
    t_online = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Online')
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("CASH IN HAND", f"₹{int(t_cash)}")
    c3.metric("ONLINE PAYMENT", f"₹{int(t_online)}")
    
    st.divider()
    st.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")

# --- 6. BILLING (WITH PAYMENT METHOD) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if st.session_state.inventory:
        with st.form("bill_f"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            qty = st.number_input("Qty", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            method = st.selectbox("Payment Method", ["Cash", "Online"]) # Naya Option
            if st.form_submit_button("COMPLETE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({
                        "Date": datetime.now().date(), "Item": item, 
                        "total": qty*pr, "Method": method,
                        "profit": (pr-inv['p_price'])*qty
                    })
                    st.success("Bill Done!")
                    st.rerun()
                else: st.error("Out of stock!")

# --- 7. EXPENSES (FIXED BLACK WINDOW) ---
elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    exp_cats = ["Rent", "Electricity", "Staff Salary", "Tea/Snacks", "Other"]
    e_cat = st.selectbox("Category", exp_cats)
    e_amt = st.number_input("Amount", min_value=1)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Category": e_cat, "Amount": e_amt})
        st.success("Saved!")
        st.rerun()
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# --- 8. ADMIN SETTINGS (ID CREATE + UDHAAR) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    
    # ID Creation Logic
    st.subheader("👤 Create Staff ID")
    new_u = st.text_input("New Username")
    new_p = st.text_input("New Password")
    if st.button("Create Account"):
        if new_u and new_p:
            st.session_state.users[new_u] = new_p
            st.success(f"ID Created for {new_u}!")
    
    st.divider()
    
    # Udhaar Logic
    st.subheader("🏢 Company Udhaar")
    with st.form("udh"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca})
            st.rerun()
    if st.session_state.company_dues:
        st.table(pd.DataFrame(st.session_state.company_dues))

# --- BAAKI ORIGINAL CODE (Purchase, Stock, etc.) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()
