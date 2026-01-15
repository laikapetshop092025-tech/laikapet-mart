import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# AAPKA URL SET HAI
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
        # Date column ko sahi format mein convert karna
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN ---
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

# --- 3. MENU ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (NET PROFIT: TODAY VS MONTHLY) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #4A90E2;'>📊 Net Profit Analysis</h2>", unsafe_allow_html=True)
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    i_df = load_data("Inventory")

    today = datetime.now().date()
    curr_month = datetime.now().month
    curr_year = datetime.now().year

    # Calculations
    def calc_metrics(df_s, df_e, df_i, filter_type="all"):
        if filter_type == "today":
            s = df_s[df_s['Date'].dt.date == today]
            e = df_e[df_e['Date'].dt.date == today]
        elif filter_type == "month":
            s = df_s[(df_s['Date'].dt.month == curr_month) & (df_s['Date'].dt.year == curr_year)]
            e = df_e[(df_e['Date'].dt.month == curr_month) & (df_e['Date'].dt.year == curr_year)]
        else:
            s, e = df_s, df_e

        sale = pd.to_numeric(s.iloc[:, 3], errors='coerce').sum() if not s.empty else 0
        exp = pd.to_numeric(e.iloc[:, 2], errors='coerce').sum() if not e.empty else 0
        # Purchase filter by date if needed, otherwise total
        pur = (pd.to_numeric(df_i.iloc[:, 1], errors='coerce') * pd.to_numeric(df_i.iloc[:, 3], errors='coerce')).sum() if not df_i.empty else 0
        return sale, exp, (sale - exp)

    t_sale, t_exp, t_profit = calc_metrics(s_df, e_df, i_df, "today")
    m_sale, m_exp, m_profit = calc_metrics(s_df, e_df, i_df, "month")

    st.subheader("📍 Today's Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{int(t_sale)}")
    c2.metric("Today Expense", f"₹{int(t_exp)}")
    c3.metric("NET PROFIT (TODAY)", f"₹{int(t_profit)}", delta=f"{int(t_profit)}")

    st.markdown("---")
    st.subheader(f"📅 Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly Sale", f"₹{int(m_sale)}")
    m2.metric("Monthly Expense", f"₹{int(m_exp)}")
    m3.metric("NET PROFIT (MONTH)", f"₹{int(m_profit)}", delta_color="normal")

# --- 5. BILLING (MONTH-WISE SYNC) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    with st.form("bill_f"):
        it = st.selectbox("Product", it_list)
        q = st.number_input("Qty", min_value=0.1); pr = st.number_input("Rate")
        if st.form_submit_button("SAVE BILL"):
            # Yahan date ke saath current month bhi save hoga backend mein
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"])
            st.success(f"Sale recorded for {datetime.now().strftime('%B')}!"); st.rerun()
    st.table(load_data("Sales").tail(10))

# --- BAAKI CODE (SAME AS BEFORE - NO CHANGES) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); q = st.number_input("Qty"); p = st.number_input("Price")
        if st.form_submit_button("ADD"):
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
    st.header("💰 Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(load_data("Expenses").tail(10))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar (Dues)")
    comp = st.text_input("Company"); d_amt = st.number_input("Due")
    if st.button("Save"):
        save_data("Dues", [comp, d_amt, str(datetime.now().date())]); st.rerun()
    st.table(load_data("Dues"))
