import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# YAHA APNA NAYA DEPLOYMENT URL DALEIN (Step 1 wala)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        # Delete command yahan se jati hai
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- LOGIN SYSTEM (SAME) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- DASHBOARD (SAME) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center;'>📊 Business Performance</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses")
    today = datetime.now().date(); curr_m = datetime.now().month
    
    def get_stats(sales_df, inv_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today] if not sales_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
        
        t_sale = 0; t_margin = 0
        for _, row in s_sub.iterrows():
            item = row.iloc[1]; q = pd.to_numeric(row.iloc[2], errors='coerce'); s_val = pd.to_numeric(row.iloc[3], errors='coerce')
            t_sale += s_val
            item_stock = inv_df[inv_df.iloc[:, 0] == item]
            if not item_stock.empty:
                p_rate = pd.to_numeric(item_stock.iloc[-1, 3], errors='coerce')
                t_margin += (s_val - (p_rate * q))
        return t_sale, t_margin

    ts, tm = get_stats(s_df, i_df, "today")
    ms, mm = get_stats(s_df, i_df, "month")
    
    st.subheader(f"📅 Today's Report")
    c1, c2 = st.columns(2); c1.metric("Sale", f"₹{int(ts)}"); c2.metric("Profit (Margin)", f"₹{int(tm)}")
    st.divider()
    st.subheader(f"🗓️ Monthly Report")
    m1, m2 = st.columns(2); m1.metric("Sale", f"₹{int(ms)}"); m2.metric("Profit (Margin)", f"₹{int(mm)}")

# --- BILLING (DELETE FIXED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill_f"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); pr = st.number_input("Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"]); st.rerun()
    
    st.subheader("Recent Sales")
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE (Directly from Sheet)"):
        if delete_data("Sales"):
            st.success("Entry Google Sheet se delete ho gayi!"); st.rerun()
        else: st.error("Naya Apps Script URL nahi mila!")

# --- PURCHASE (DELETE FIXED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); q = st.number_input("Qty"); p = st.number_input("Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); st.rerun()
    
    st.subheader("Recent Purchases")
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE (Directly from Sheet)"):
        if delete_data("Inventory"):
            st.success("Entry Google Sheet se delete ho gayi!"); st.rerun()
        else: st.error("Naya Apps Script URL nahi mila!")

# --- PET REGISTER & OTHERS (SAME) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    p_df = load_data("PetRecords")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Name"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "Indie", "Other"])
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine")
        if st.form_submit_button("SAVE"): save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); st.rerun()
    st.table(p_df.tail(5))

elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    cat = st.selectbox("Cat", ["Rent", "Electricity", "Other"]); amt = st.number_input("Amt")
    if st.button("Save"): save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(load_data("Expenses").tail(5))

elif menu == "⚙️ Admin Settings":
    st.subheader("👤 Create ID (Admin Sync coming soon)"); st.text_input("User"); st.text_input("Pass")
    st.divider()
    st.subheader("🏢 Company Dues")
    d_df = load_data("Dues")
    with st.form("due_f"):
        comp = st.text_input("Company"); amt = st.number_input("Due")
        if st.form_submit_button("SAVE"): save_data("Dues", [comp, amt, str(datetime.now().date())]); st.rerun()
    st.table(d_df)
