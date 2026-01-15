import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# URL pehle se set hai
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
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
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
st.sidebar.title("🐾 NAVIGATION")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (NEW DESIGN) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #4A90E2;'>📊 Business Performance Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    t_sale = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    t_exp = pd.to_numeric(e_df.iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    t_pur = (pd.to_numeric(i_df.iloc[:, 1], errors='coerce') * pd.to_numeric(i_df.iloc[:, 3], errors='coerce')).sum() if not i_df.empty else 0
    t_profit = t_sale - t_exp - t_pur

    # Styled Metrics
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"<div style='background-color: #D4EDDA; padding: 20px; border-radius: 10px; text-align: center;'><h3 style='color: #155724;'>TOTAL SALE</h3><h2>₹{int(t_sale)}</h2></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div style='background-color: #FFF3CD; padding: 20px; border-radius: 10px; text-align: center;'><h3 style='color: #856404;'>PURCHASE</h3><h2>₹{int(t_pur)}</h2></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div style='background-color: #F8D7DA; padding: 20px; border-radius: 10px; text-align: center;'><h3 style='color: #721C24;'>EXPENSES</h3><h2>₹{int(t_exp)}</h2></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div style='background-color: #CCE5FF; padding: 20px; border-radius: 10px; text-align: center;'><h3 style='color: #004085;'>PROFIT</h3><h2>₹{int(t_profit)}</h2></div>", unsafe_allow_html=True)
    st.markdown("---")

# --- 5. PURCHASE (With Delete) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    inv_df = load_data("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())])
            st.rerun()
    
    st.subheader("📋 Stock List")
    st.dataframe(inv_df.tail(10))
    if st.button("❌ Delete Last Entry"):
        st.warning("Google Sheet se entry manually delete karein (Coming soon auto-delete)")

# --- 6. BILLING ---
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

# --- 7. PET REGISTER (Weight, Age, Vaccine) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie Dog/Cat", "Other"])
        with c2:
            age = st.text_input("Pet Age"); wt = st.text_input("Weight (Kg)")
            vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.rerun()
    st.table(p_df.tail(10))

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Shop Stock (Live)")
    st.table(load_data("Inventory"))

# --- 9. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Records")
    e_df = load_data("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous", "Staff Salary", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(e_df.tail(10))

# --- 10. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar (Dues)")
    d_df = load_data("Dues")
    with st.form("due_f"):
        comp = st.text_input("Company Name"); amt = st.number_input("Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); st.rerun()
    st.table(d_df)
