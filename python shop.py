import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION (NO CHANGES) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN (NO CHANGES) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU (NO CHANGES) ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (FIXED FOR GROSS PROFIT) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #4A90E2;'>📊 Business Performance Dashboard</h2>", unsafe_allow_html=True)
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")

    today = datetime.now().date()
    curr_month = datetime.now().month
    curr_year = datetime.now().year

    # Calculations for Today
    s_today = s_df[s_df['Date'].dt.date == today] if not s_df.empty else pd.DataFrame()
    e_today = e_df[e_df['Date'].dt.date == today] if not e_df.empty else pd.DataFrame()
    
    sale_today = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum() if not s_today.empty else 0
    exp_today = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty else 0
    gross_today = sale_today - exp_today

    # Calculations for This Month
    s_month = s_df[(s_df['Date'].dt.month == curr_month) & (s_df['Date'].dt.year == curr_year)] if not s_df.empty else pd.DataFrame()
    e_month = e_df[(e_df['Date'].dt.month == curr_month) & (df_s['Date'].dt.year == curr_year)] if not e_df.empty else pd.DataFrame()
    
    sale_month = pd.to_numeric(s_month.iloc[:, 3], errors='coerce').sum() if not s_month.empty else 0
    exp_month = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum() if not e_month.empty else 0
    gross_month = sale_month - exp_month

    # Dashboard Cards
    st.markdown("---")
    st.subheader(f"📍 Today's Gross Status ({today})")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today's Sale", f"₹{int(sale_today)}")
    c2.metric("Today's Expense", f"₹{int(exp_today)}")
    c3.metric("GROSS PROFIT (TODAY)", f"₹{int(gross_today)}", delta=f"{int(gross_today)}")

    st.markdown("---")
    st.subheader(f"📅 Monthly Gross Status ({datetime.now().strftime('%B')})")
    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly Sale", f"₹{int(sale_month)}")
    m2.metric("Monthly Expense", f"₹{int(exp_month)}")
    m3.metric("GROSS PROFIT (MONTH)", f"₹{int(gross_month)}", delta=f"{int(gross_month)}")
    st.markdown("---")

# --- BAAKI CODE (BILKUL VAISA HI HAI - NO CHANGES) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory")
    it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    with st.form("bill_f"):
        it = st.selectbox("Select Product", it_list)
        q = st.number_input("Qty", min_value=0.1); pr = st.number_input("Selling Price")
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"])
            st.rerun()
    st.table(load_data("Sales").tail(10))

elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); q = st.number_input("Qty"); p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); st.rerun()
    st.table(load_data("Inventory").tail(10))

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Other"])
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); st.rerun()
    st.table(p_df.tail(10))

elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    e_df = load_data("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous", "Staff Salary", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(e_df.tail(10))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar (Dues)"); d_df = load_data("Dues")
    c = st.text_input("Company"); a = st.number_input("Amount")
    if st.button("Save Due"): save_data("Dues", [c, a, str(datetime.now().date())]); st.rerun()
    st.table(d_df)
