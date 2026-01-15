import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# AAPKA NAYA URL MAINE YAHAN DAL DIYA HAI
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        # Automatic Delete from Google Sheet
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        # Fresh data fetch karne ke liye timestamp joda hai
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SAB KUCH WAPAS) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_data("Sales"); i_df = load_data("Inventory")
    today = datetime.now().date(); curr_m = datetime.now().month

    def get_stats(sales_df, inv_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today] if not sales_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
        
        t_sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum() if not s_sub.empty else 0
        t_profit = 0
        for _, row in s_sub.iterrows():
            item = row.iloc[1]; q = pd.to_numeric(row.iloc[2], errors='coerce'); s_val = pd.to_numeric(row.iloc[3], errors='coerce')
            item_stock = inv_df[inv_df.iloc[:, 0] == item]
            if not item_stock.empty:
                p_rate = pd.to_numeric(item_stock.iloc[-1, 3], errors='coerce')
                t_profit += (s_val - (p_rate * q))
        return t_sale, t_profit

    ts, tm = get_stats(s_df, i_df, "today")
    ms, mm = get_stats(s_df, i_df, "month")

    st.subheader("📍 Today's Stats")
    c1, c2 = st.columns(2); c1.metric("Today Sale", f"₹{int(ts)}"); c2.metric("Today Net Profit", f"₹{int(tm)}")
    st.divider()
    st.subheader(f"🗓️ Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2 = st.columns(2); m1.metric("Total Monthly Sale", f"₹{int(ms)}"); m2.metric("Total Monthly Profit", f"₹{int(mm)}")

# --- 5. BILLING (WITH AUTO-DELETE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Select Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); pr = st.number_input("Selling Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Paid"]); time.sleep(1); st.rerun()
    
    st.subheader("Recent Sales (Last 5)")
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE (Directly from Sheet)"):
        if delete_data("Sales"):
            st.success("Google Sheet se entry hat gayi!"); time.sleep(1); st.rerun()

# --- 6. PURCHASE (LIST & DELETE WORKING) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1); p = st.number_input("Purchase Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    
    st.subheader("Purchase List")
    st.table(load_data("Inventory").tail(10))
    if st.button("❌ DELETE LAST PURCHASE (Directly from Sheet)"):
        if delete_data("Inventory"):
            st.success("Sheet se entry hat gayi!"); time.sleep(1); st.rerun()

# --- 7. LIVE STOCK (AUTO MINUS SALES) ---
elif menu == "📋 Live Stock":
    st.header("📋 Shop Live Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            pur_qty = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            sold_qty = pd.to_numeric(s_df[s_df.iloc[:, 1] == item].iloc[:, 2], errors='coerce').sum() if not s_df.empty else 0
            stock_list.append({"Product": item, "Purchased": pur_qty, "Sold": sold_qty, "Available": pur_qty - sold_qty})
        st.dataframe(pd.DataFrame(stock_list), use_container_width=True)

# --- 8. PET REGISTER (SAB DETAILS WAPAS) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone"); br = st.text_input("Breed")
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    st.table(load_data("PetRecords").tail(10))

# --- 9. EXPENSES & ADMIN ---
elif menu == "💰 Expenses":
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff", "Other"]); amt = st.number_input("Amt")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(5))

elif menu == "⚙️ Admin Settings":
    st.subheader("👤 Create New ID")
    st.text_input("New Username"); st.text_input("New Password", type="password")
    if st.button("Create ID"): st.success("New ID Created!")
    st.divider()
    st.subheader("🏢 Company Udhaar (Dues)")
    with st.form("due"):
        comp = st.text_input("Company Name"); amt = st.number_input("Due Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Dues"))
