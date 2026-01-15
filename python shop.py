import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Apna naya Deployment URL yahan dalo
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
SHEET_LINK = "https://script.google.com/macros/s/AKfycbzSbcrX5iGnAxOqUuHaXRGv6zpSvg9XhYznxvE2tIrYO-ybkbrP0KwcJI6iy85ACV3P/exec"

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        # Google Sheet ko automatic delete command bhejna
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

# --- 2. LOGIN / LOGOUT ---
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

# --- 3. MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SAB KUCH PERFECT) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center;'>📊 Business Performance</h2>", unsafe_allow_html=True)
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
    c1, c2 = st.columns(2); c1.metric("Today Sale", f"₹{int(ts)}"); c2.metric("Today Margin Profit", f"₹{int(tm)}")
    st.divider()
    st.subheader(f"🗓️ Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2 = st.columns(2); m1.metric("Total Sale", f"₹{int(ms)}"); m2.metric("Total Margin Profit", f"₹{int(mm)}")

# --- 5. BILLING (WITH AUTO-DELETE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory")
    it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    with st.form("bill"):
        it = st.selectbox("Product", it_list); q = st.number_input("Qty", 0.1); pr = st.number_input("Selling Price")
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"]); st.rerun()
    
    st.subheader("Recent Sales")
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE (From Sheet)"):
        if delete_data("Sales"): st.success("Entry Google Sheet se automatic delete ho gayi!"); st.rerun()

# --- 6. PURCHASE (WITH AUTO-DELETE) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1); p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); st.rerun()
    
    st.subheader("Recent Purchases")
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE (From Sheet)"):
        if delete_data("Inventory"): st.success("Purchase entry delete ho gayi!"); st.rerun()

# --- 7. LIVE STOCK (AUTO STOCK MINUS) ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            pur_qty = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            sold_qty = pd.to_numeric(s_df[s_df.iloc[:, 1] == item].iloc[:, 2], errors='coerce').sum() if not s_df.empty else 0
            stock_list.append({"Item Name": item, "Purchased": pur_qty, "Sold": sold_qty, "Available": pur_qty - sold_qty})
        st.dataframe(pd.DataFrame(stock_list), use_container_width=True)

# --- 8. PET REGISTER (SAB FIELDS WAPAS) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie Dog/Cat", "Other"])
        with c2: age = st.text_input("Pet Age"); wt = st.text_input("Weight (Kg)"); vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); st.rerun()
    st.table(load_data("PetRecords").tail(10))

# --- 9. EXPENSES & ADMIN ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Manager")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Other"]); amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(load_data("Expenses").tail(5))

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("👤 Create New ID")
    new_u = st.text_input("Username"); new_p = st.text_input("Password", type="password")
    if st.button("CREATE ID"): st.success(f"ID {new_u} Created!")
    st.divider()
    st.subheader("🏢 Company Udhaar (Dues)")
    d_df = load_data("Dues")
    with st.form("due"):
        comp = st.text_input("Company Name"); amt = st.number_input("Due Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); st.rerun()
    st.table(d_df)
