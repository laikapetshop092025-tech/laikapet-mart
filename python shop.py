import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PROFESSIONAL LOOK (CSS) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* Professional Card Styling */
    div[data-testid="stMetricValue"] {font-size: 38px; color: #4A90E2; font-weight: bold;}
    div[data-testid="stMetricLabel"] {font-size: 20px; color: #333; font-weight: bold;}
    [data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #f0f0f0;
    }
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4A90E2;
        color: white;
        font-weight: bold;
        border: none;
    }
    .main-title {text-align: center; color: #4A90E2; font-size: 45px; font-weight: bold; margin-bottom: 0px;}
    .sub-title {text-align: center; color: #777; font-size: 18px; margin-bottom: 30px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Logic Bilkul Same) ---
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
    st.markdown("<h1 style='text-align: center;'>🔐 Staff Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN NOW"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. TOP BRANDING ---
st.markdown("<h1 style='text-align: center; margin-bottom: -10px;'>👑</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #ff3399; font-weight: bold; font-size: 20px;'>Pet Store</p>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Hamesha Aapke Pet Ke Saath 🤝</div>", unsafe_allow_html=True)

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. DASHBOARD (Photo Wala Look) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("TOTAL SALE", f"₹{int(t_sale)}")
        st.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    with col_b:
        st.metric("NET PROFIT", f"₹{int(n_prof)}")
        st.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        if t_udh > 0: st.error(f"⚠️ Udhaar Pending: ₹{int(t_udh)}")

# --- 7. ADMIN SETTINGS (Udhaar + ID Creation Both Added) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    
    # Section 1: Create ID
    st.subheader("👤 Create New Staff ID")
    new_u = st.text_input("New Username")
    new_p = st.text_input("New Password", type="password")
    if st.button("CREATE ACCOUNT"):
        if new_u and new_p:
            st.session_state.users[new_u] = new_p
            st.success(f"ID Created for {new_u}!")
        else: st.error("Details bhariye!")

    st.write("---")
    
    # Section 2: Udhaar
    st.subheader("🏢 Company Udhaar Record")
    with st.form("udh_f"):
        cn = st.text_input("Company Name")
        ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE UDHAAR"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))

# --- BAAKI SAB CODE (Sahi Logic Ke Saath) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine Date")
        if st.form_submit_button("Save Record"):
            st.session_state.pet_records.append({"Customer": n, "Phone": ph, "Breed": b, "Age": a, "Next Vaccine": v})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if st.session_state.inventory:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
        st.info(f"Available Stock: {st.session_state.inventory[item]['qty']}")
        qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
        cust = st.text_input("Customer Name")
        if st.button("GENERATE BILL"):
            inv = st.session_state.inventory[item]
            if qty <= inv['qty']:
                st.session_state.inventory[item]['qty'] -= qty
                st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*pr, "profit": (pr-inv['p_price'])*qty, "Customer": cust})
                st.rerun()

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Price": v['p_price']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    exp_cats = ["Rent", "Electricity", "Staff Salary", "Snacks", "Other"]
    e_cat = st.selectbox("Category", exp_cats); e_amt = st.number_input("Amount", min_value=1)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Item": e_cat, "Amount": e_amt})
        st.rerun()
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "📅 Report Center":
    st.title("📅 Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("Download Excel", df.to_csv(index=False).encode('utf-8'), "Report.csv")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty']} for k, v in st.session_state.inventory.items()]))
