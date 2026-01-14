import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# App jaisa look aur Branding
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #4A90E2; font-size: 40px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGO SECTION (Yahan aapka logo aayega) ---
# Maine columns banaye hain taaki logo bilkul beech (Center) mein dikhe
col1, col2, col3 = st.columns([2,1,2])
with col2:
    # Jo image aapne dikhayi hai, uska icon yahan set kar diya hai
    st.markdown("<h1 style='text-align: center;'>👑</h1>", unsafe_allow_html=True) 
    st.markdown("<p style='text-align: center; color: #ff3399; font-weight: bold; margin-top: -20px;'>Pet Store</p>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Hamesha Aapke Pet Ke Saath 🤝</p>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (No Change) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT & LOGIN ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Asli Classic Style) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("NET PROFIT", f"₹{int(n_prof)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        if t_udh > 0: st.error(f"⚠️ Pending Company Udhaar: ₹{int(t_udh)}")

# --- BAAKI SAB CODE BILKUL WAISA HI HAI ---
elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    exp_cats = ["Rent", "Electricity Bill", "Staff Salary", "Pet Food", "Snacks", "Other"]
    e_cat = st.selectbox("Select Category", exp_cats)
    e_amt = st.number_input("Amount", min_value=1)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Item": e_cat, "Amount": e_amt})
        st.rerun()

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f", clear_on_submit=True):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1)
        q = st.number_input("Qty", min_value=1); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
            st.rerun()
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Price": v['p_price']} for k, v in st.session_state.inventory.items()]))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if st.session_state.inventory:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
        st.info(f"Stock: {st.session_state.inventory[item]['qty']}")
        qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
        cust = st.text_input("Customer")
        if st.button("Generate Bill"):
            inv = st.session_state.inventory[item]
            if qty <= inv['qty']:
                st.session_state.inventory[item]['qty'] -= qty
                st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*pr, "profit": (pr-inv['p_price'])*qty, "Customer": cust})
                st.rerun()

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Name"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine")
        if st.form_submit_button("Save"):
            st.session_state.pet_records.append({"Customer": n, "Breed": b, "Next Vaccine": v})
            st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar")
    with st.form("udh"):
        cn = st.text_input("Company"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))

elif menu == "📅 Report Center":
    st.title("📅 Report Center")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("Download Report", df.to_csv(index=False).encode('utf-8'), "Report.csv")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Qty": v['qty']} for k, v in st.session_state.inventory.items()]))
