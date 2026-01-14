import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & STYLE ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold; margin-top: -10px;}
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Logic Same) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
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
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. TOP WELCOME HEADER & LOGO ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)

col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    try:
        st.image("1000302358.webp", width=150)
    except:
        st.markdown("<h1 style='text-align: center;'>👑</h1>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Sales Register", "📅 Report Center"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. DASHBOARD (Amount Fix) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_cash = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Cash')
    t_online = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Online')
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    col_a, col_b, col_c = st.columns(3)
    # yahan int() lagane se .000000 hat gaye hain
    col_a.metric("TOTAL SALES", f"₹{int(t_sale)}")
    col_b.metric("CASH TOTAL", f"₹{int(t_cash)}")
    col_c.metric("ONLINE TOTAL", f"₹{int(t_online)}")
    
    st.divider()
    st.metric("TOTAL EXPENSES", f"₹{int(t_exp)}")

# --- 7. BILLING TERMINAL ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory: st.warning("Stock khali hai!")
    else:
        with st.form("bill_f"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            # Stock ko rounded dikhaya hai bina zero ke
            st.info(f"Available: {int(st.session_state.inventory[item]['qty'])}")
            qty = st.number_input("Quantity", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment Method", ["Cash", "Online"])
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({
                        "Date": datetime.now().date(), "Item": item, "Qty": qty, 
                        "total": qty*pr, "Method": meth, "Customer": cust, 
                        "profit": (pr-inv['p_price'])*qty
                    })
                    st.rerun()

# --- 8. LIVE STOCK (Zero Fix) ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Status")
    if st.session_state.inventory:
        # Stock table mein number ko clean (int) kar diya hai
        stock_data = [{"Item": k, "Available": f"{int(v['qty'])}", "Price": f"₹{int(v['p_price'])}"} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(stock_data))

# --- BAAKI SECTIONS (SAB SAFE HAIN) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    st.subheader("👤 Create Staff ID")
    new_u = st.text_input("New Staff Username")
    new_p = st.text_input("New Staff Password", type="password")
    if st.button("CREATE ID"):
        if new_u and new_p: st.session_state.users[new_u] = new_p; st.success("ID Created!")
    
    st.divider()
    st.subheader("🏢 Company Udhaar Record")
    with st.form("udh_form"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE UDHAAR"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff", "Tea/Snacks", "Other"])
    amt = st.number_input("Amount", min_value=1)
    if st.button("Save"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
        st.rerun()
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_reg"):
        n = st.text_input("Customer Name"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Other"])
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": n, "Breed": b, "Date": datetime.now().date()})
            st.rerun()

elif menu == "📅 Report Center":
    st.title("📅 Monthly Sales Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("📥 Download Report", df.to_csv(index=False).encode('utf-8'), "Report.csv")
