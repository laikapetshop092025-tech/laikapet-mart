import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & STYLE (No Change) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold; margin-top: -10px;}
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px; margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (No Change) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. LOGIN & AUTO-LOGOUT (No Change) ---
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

# --- 4. TOP BRANDING ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)
col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    try: st.image("1000302358.webp", width=150)
    except: st.markdown("<h1 style='text-align: center;'>👑</h1>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Sales Register", "📅 Report Center"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. PET SALES REGISTER (FIXED: AGE, WEIGHT, VACCINE) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_reg_form"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Customer Name")
            ph = st.text_input("Phone Number")
            b = st.selectbox("Dog Breed", ["Labrador", "German Shepherd", "Pug", "Beagle", "Rottweiler", "Other"])
        with c2:
            a = st.text_input("Dog Age (e.g. 2 Months)")
            w = st.text_input("Dog Weight (e.g. 5 KG)")
            v = st.selectbox("Vaccine Status", ["Fully Vaccinated", "First Dose Done", "Not Vaccinated", "Pending"])
            v_date = st.date_input("Next Vaccine Date")
            
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({
                "Date": datetime.now().date(),
                "Customer": n,
                "Phone": ph,
                "Breed": b,
                "Age": a,
                "Weight": w,
                "Vaccine Status": v,
                "Next Date": v_date
            })
            st.success("Pet Record Saved!")
            st.rerun()
            
    if st.session_state.pet_records:
        st.subheader("Registered Pets")
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- BAAKI SAB ORIGINAL SECTIONS (No Changes) ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_cash = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Cash')
    t_online = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Online')
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALES", f"₹{int(t_sale)}")
    c2.metric("CASH TOTAL", f"₹{int(t_cash)}")
    c3.metric("ONLINE TOTAL", f"₹{int(t_online)}")
    st.divider()
    st.metric("TOTAL EXPENSES", f"₹{int(t_exp)}")

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if st.session_state.inventory:
        with st.form("bill"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            st.info(f"Stock: {int(st.session_state.inventory[item]['qty'])}")
            qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment", ["Cash", "Online"])
            if st.form_submit_button("BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": qty*pr, "Method": meth, "profit": (pr-inv['p_price'])*qty})
                    st.rerun()

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": int(v['qty']), "Price": int(v['p_price'])} for k, v in st.session_state.inventory.items()]))

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur"):
        n = st.text_input("Name"); r = st.number_input("Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    cat = st.selectbox("Cat", ["Rent", "Electricity", "Staff", "Other"])
    amt = st.number_input("Amt", min_value=1)
    if st.button("Save"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
        st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin")
    st.subheader("👤 New ID")
    new_u = st.text_input("Username"); new_p = st.text_input("Password")
    if st.button("Create"):
        if new_u and new_p: st.session_state.users[new_u] = new_p; st.success("Created!")
    st.divider()
    st.subheader("🏢 Udhaar")
    with st.form("udh"):
        cn = st.text_input("Company"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca}); st.rerun()

elif menu == "📅 Report Center":
    st.title("📅 Sales Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("Download", df.to_csv(index=False).encode('utf-8'), "Report.csv")
