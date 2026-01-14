import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & BRANDING (Logo Addition) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold; margin-top: -10px;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGO DISPLAY ---
col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
with col_l2:
    # Aapka Pink Logo (File name check kar lena GitHub par)
    try:
        st.image("1000302358.webp", width=150)
    except:
        st.markdown("<h1 style='text-align: center;'>👑</h1>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Hamesha Aapke Pet Ke Saath 🐾</p>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Original Logic) ---
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
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Ghalat ID/Password!")
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Sales Register", "📅 Report Center"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Cash & Online Added) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_cash = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Cash')
    t_online = sum(s.get('total', 0) for s in st.session_state.sales if s.get('Method') == 'Online')
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("TOTAL SALES", f"₹{int(t_sale)}")
    col_b.metric("CASH TOTAL", f"₹{int(t_cash)}")
    col_c.metric("ONLINE TOTAL", f"₹{int(t_online)}")
    
    st.divider()
    st.metric("TOTAL EXPENSES", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        if t_udh > 0: st.error(f"⚠️ Company Udhaar Pending: ₹{int(t_udh)}")

# --- 6. BILLING (With Payment Method) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory: st.warning("Stock khali hai!")
    else:
        with st.form("bill_f"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            st.info(f"Available: {st.session_state.inventory[item]['qty']}")
            qty = st.number_input("Quantity", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment Method", ["Cash", "Online"]) # Added
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
                    st.success("Bill Generated Successfully!")
                    st.rerun()
    if st.session_state.sales:
        st.subheader("Recent Bills")
        st.table(pd.DataFrame(st.session_state.sales).tail(5))

# --- 7. ADMIN SETTINGS (ID Creation + Udhaar) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    
    # Staff ID Management
    st.subheader("👤 Create Staff ID")
    new_u = st.text_input("New Staff Username")
    new_p = st.text_input("New Staff Password", type="password")
    if st.button("CREATE ID"):
        if new_u and new_p:
            st.session_state.users[new_u] = new_p
            st.success(f"ID Created for {new_u}!")
        else: st.error("Please fill both fields!")
    
    st.divider()
    
    # Company Udhaar
    st.subheader("🏢 Company Udhaar Record")
    with st.form("udh_form"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE UDHAAR"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues:
        st.table(pd.DataFrame(st.session_state.company_dues))

# --- BAAKI ORIGINAL SECTIONS (Purchase, Stock, Pet, Report) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r}
            st.rerun()
    if st.session_state.inventory: st.table(pd.DataFrame([{"Item": k, "Qty": v['qty']} for k, v in st.session_state.inventory.items()]))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Status")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Purchase Price": v['p_price']} for k, v in st.session_state.inventory.items()]))

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
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer Name"); ph = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": n, "Breed": b, "Next Vaccine": v})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "📅 Report Center":
    st.title("📅 Monthly Sales Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("📥 Download Excel Report", df.to_csv(index=False).encode('utf-8'), "Report.csv")
