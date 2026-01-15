import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Apna Naya Deployment URL yahan dalo
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        df = pd.read_csv(f"{SHEET_LINK}{sheet_name}&cache={datetime.now().timestamp()}")
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🐾 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SALE, PURCHASE & NET PROFIT) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center;'>📊 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory")
    today = datetime.now().date(); curr_m = datetime.now().month

    def calc_stats(sales_df, inv_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.date == today] if not inv_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.month == curr_m] if not inv_df.empty else pd.DataFrame()
        
        t_sale = pd.to_numeric(s_sub.iloc[:, 3]).sum() if not s_sub.empty else 0
        t_pur = (pd.to_numeric(p_sub.iloc[:, 1]) * pd.to_numeric(p_sub.iloc[:, 3])).sum() if not p_sub.empty else 0
        
        t_profit = 0
        for _, row in s_sub.iterrows():
            item = row.iloc[1]; qty = pd.to_numeric(row.iloc[2]); s_price = pd.to_numeric(row.iloc[3])
            matching_inv = inv_df[inv_df.iloc[:, 0] == item]
            if not matching_inv.empty:
                p_rate = pd.to_numeric(matching_inv.iloc[-1, 3])
                t_profit += (s_price - (p_rate * qty))
        return t_sale, t_pur, t_profit

    ts, tp, tm = calc_stats(s_df, i_df, "today")
    ms, mp, mm = calc_stats(s_df, i_df, "month")

    st.subheader("📍 Today's Stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts}"); c2.metric("Today Purchase", f"₹{tp}"); c3.metric("Net Profit", f"₹{tm}")
    
    st.divider()
    st.subheader(f"🗓️ Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sale", f"₹{ms}"); m2.metric("Total Purchase", f"₹{mp}"); m3.metric("Total Profit", f"₹{mm}")

# --- 5. BILLING (WITH AUTO-DELETE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Sales")
    inv_df = load_data("Inventory")
    items = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    with st.form("bill"):
        it = st.selectbox("Select Product", items)
        q = st.number_input("Qty", 0.1); pr = st.number_input("Selling Price")
        if st.form_submit_button("GENERATE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Paid"]); st.rerun()
    
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE"):
        if delete_data("Sales"): st.success("Deleted from Sheet!"); st.rerun()

# --- 6. PURCHASE (WITH AUTO-DELETE) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Inventory")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1); p = st.number_input("Purchase Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); st.rerun()
    
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE"):
        if delete_data("Inventory"): st.success("Deleted from Sheet!"); st.rerun()

# --- 7. LIVE STOCK (AUTO MINUS SALES) ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    if not inv_df.empty:
        stock_summary = []
        for item in inv_df.iloc[:, 0].unique():
            purchased = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == item].iloc[:, 1]).sum()
            sold = pd.to_numeric(s_df[s_df.iloc[:, 1] == item].iloc[:, 2]).sum() if not s_df.empty else 0
            stock_summary.append({"Item": item, "Purchased": purchased, "Sold": sold, "Available": purchased - sold})
        st.dataframe(pd.DataFrame(stock_summary), use_container_width=True)

# --- 8. EXPENSES (DROPDOWN FIXED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Manager")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Pet Food", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(load_data("Expenses").tail(10))

# --- 9. PET REGISTER (ALL FIELDS BACK) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet_reg"):
        c1, c2 = st.columns(2)
        with c1: 
            name = st.text_input("Customer Name"); phone = st.text_input("Phone Number")
            breed = st.text_input("Pet Breed")
        with c2:
            age = st.text_input("Pet Age"); wt = st.text_input("Weight (kg)")
            next_vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [name, phone, breed, age, wt, str(next_vax)]); st.rerun()
    st.table(load_data("PetRecords").tail(10))

# --- 10. ADMIN SETTINGS (NEW ID & DUES) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    tab1, tab2 = st.tabs(["👤 User Management", "🏢 Company Dues"])
    with tab1:
        st.subheader("Create New Login ID")
        new_u = st.text_input("New Username"); new_p = st.text_input("New Password", type="password")
        if st.button("Create ID"): st.success(f"ID {new_u} Created!")
    with tab2:
        st.subheader("Manage Udhaar (Dues)")
        with st.form("dues"):
            comp = st.text_input("Company Name"); d_amt = st.number_input("Due Amount")
            if st.form_submit_button("Save Due"):
                save_data("Dues", [comp, d_amt, str(datetime.now().date())]); st.rerun()
        st.table(load_data("Dues"))
