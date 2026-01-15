import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION (BILKUL SAME) ---
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

# --- 2. LOGIN (BILKUL SAME) ---
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

# --- 3. MENU (BILKUL SAME) ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (SIRF CALCULATION BADLI HAI) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #4A90E2;'>📊 Margin Profit Dashboard</h2>", unsafe_allow_html=True)
    
    s_df = load_data("Sales")
    i_df = load_data("Inventory")
    e_df = load_data("Expenses")

    today = datetime.now().date()
    curr_month = datetime.now().month
    curr_year = datetime.now().year

    # 10 ka kharida, 20 ka becha -> 10 Profit logic
    def calculate_margin(sales_subset, inv_df):
        m_profit = 0
        m_sale = 0
        for _, row in sales_subset.iterrows():
            item = row.iloc[1]
            q = pd.to_numeric(row.iloc[2], errors='coerce')
            s_val = pd.to_numeric(row.iloc[3], errors='coerce')
            m_sale += s_val
            
            # Inventory se kharid rate dhundna
            item_stock = inv_df[inv_df.iloc[:, 0] == item]
            if not item_stock.empty:
                # Latest purchase rate uthana
                p_rate = pd.to_numeric(item_stock.iloc[-1, 3], errors='coerce')
                cost = p_rate * q
                m_profit += (s_val - cost)
        return m_sale, m_profit

    s_today = s_df[s_df['Date'].dt.date == today] if not s_df.empty else pd.DataFrame()
    s_month = s_df[(s_df['Date'].dt.month == curr_month) & (s_df['Date'].dt.year == curr_year)] if not s_df.empty else pd.DataFrame()
    
    sale_t, profit_t = calculate_margin(s_today, i_df)
    sale_m, profit_m = calculate_margin(s_month, i_df)

    st.markdown("---")
    st.subheader(f"📍 Today's Summary ({today})")
    c1, c2 = st.columns(2)
    c1.metric("Today Sale", f"₹{int(sale_t)}")
    c2.metric("ASLI MUNAFA (TODAY)", f"₹{int(profit_t)}")

    st.markdown("---")
    st.subheader(f"📅 Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2 = st.columns(2)
    m1.metric("Monthly Sale", f"₹{int(sale_m)}")
    m2.metric("ASLI MUNAFA (MONTH)", f"₹{int(profit_m)}")
    st.markdown("---")

# --- BAAKI POORA CODE (BILKUL VAISA HI HAI) ---
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
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(e_df.tail(10))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar (Dues)"); d_df = load_data("Dues")
    c = st.text_input("Company"); a = st.number_input("Amount")
    if st.button("Save Due"): save_data("Dues", [c, a, str(datetime.now().date())]); st.rerun()
    st.table(d_df)
