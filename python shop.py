import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import os

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
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
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR ---
st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>👋 Welcome <br> Laika Pet Mart</h3>", unsafe_allow_html=True)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", use_container_width=True)
if os.path.exists("logo.png"): st.sidebar.image("logo.png", use_container_width=True)

menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (NO CHANGES AS REQUESTED) ---
if menu == "📊 Dashboard":
    today_str = datetime.now().strftime('%d %B, %Y')
    month_name = datetime.now().strftime('%B %Y')
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    today_dt = datetime.now().date(); curr_m = datetime.now().month
    op_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    op_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    total_exp_all = pd.to_numeric(e_df.iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    curr_cash = (op_cash + sale_cash) - total_exp_all
    curr_online = op_online + sale_online
    st.markdown("### 💰 Real-Time Money Status")
    col_c, col_o = st.columns(2)
    with col_c: st.success(f"*Galla (Cash in Hand)*\n## ₹{curr_cash:,.2f}")
    with col_o: st.info(f"*Bank (Online Balance)*\n## ₹{curr_online:,.2f}")
    st.divider()
    def get_stats(sales_df, inv_df, exp_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today_dt] if not sales_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.date == today_dt] if not exp_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.month == curr_m] if not exp_df.empty else pd.DataFrame()
        t_sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum() if not s_sub.empty else 0
        t_exp = pd.to_numeric(e_sub.iloc[:, 2], errors='coerce').sum() if not e_sub.empty else 0
        t_margin = 0
        if not s_sub.empty and not inv_df.empty:
            for _, row in s_sub.iterrows():
                try:
                    item = row.iloc[1]; q_val = float(str(row.iloc[2]).split()[0]); s_val = float(row.iloc[3])
                    item_stock = inv_df[inv_df.iloc[:, 0] == item]
                    if not item_stock.empty:
                        p_rate = float(item_stock.iloc[-1, 3])
                        t_margin += (s_val - (p_rate * q_val))
                except: continue
        return t_sale, t_margin, t_exp
    ts, tm, te = get_stats(s_df, i_df, e_df, "today")
    ms, mm, me = get_stats(s_df, i_df, e_df, "month")
    st.markdown(f"#### 📅 Today: <span style='color: #FF4B4B;'>{today_str}</span>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts:,.2f}"); c2.metric("Margin Profit", f"₹{tm:,.2f}"); c3.metric("Today Expense", f"₹{te:,.2f}")
    st.divider()
    st.markdown(f"#### 🗓️ Monthly Summary: <span style='color: #1E88E5;'>{month_name}</span>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sale", f"₹{ms:,.2f}"); m2.metric("Net Margin", f"₹{mm:,.2f}"); m3.metric("Total Expense", f"₹{me:,.2f}")

# --- 5. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c3: mode = st.selectbox("Payment Mode", ["Cash", "Online"])
        pr = st.number_input("Selling Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, mode])
            time.sleep(1); st.rerun()
    st.subheader("Recent Sales List")
    st.table(load_data("Sales").tail(10))
    if st.button("❌ DELETE LAST SALE ENTRY"):
        if delete_data("Sales"): st.success("Sale Deleted!"); time.sleep(1); st.rerun()

# --- 6. PURCHASE (LIST & DELETE ADDED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name")
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 1.0)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c3: p = st.number_input("Purchase Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, unit, p, str(datetime.now().date())])
            time.sleep(1); st.rerun()
    st.subheader("Stock Purchase List")
    st.table(load_data("Inventory").tail(10))
    if st.button("❌ DELETE LAST PURCHASE ENTRY"):
        if delete_data("Inventory"): st.success("Purchase Entry Deleted!"); time.sleep(1); st.rerun()

# --- 7. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            t_p = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            t_s = 0
            if not s_df.empty:
                sold_data = s_df[s_df.iloc[:, 1] == item]
                for val in sold_data.iloc[:, 2]:
                    try: t_s += float(str(val).split()[0])
                    except: continue
            stock_list.append({"Product": item, "Available": t_p - t_s, "Unit": i_df[i_df.iloc[:, 0] == item].iloc[:, 2].iloc[-1]})
        st.table(pd.DataFrame(stock_list))

# --- 8. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Other"]); amt = st.number_input("Amount")
        if st.form_submit_button("Save Expense"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(5))
    if st.button("❌ DELETE LAST EXPENSE"):
        if delete_data("Expenses"): st.success("Deleted!"); time.sleep(1); st.rerun()

# --- 9. PET REGISTER (ALL FIELDS BACK + DELETE) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    dog_breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie Dog", "Husky", "Boxer", "Pitbull", "Shih Tzu"]
    cat_breeds = ["Persian Cat", "Siamese Cat", "Indie Cat", "Bengal Cat", "Maine Coon"]
    with st.form("pet"):
        col1, col2 = st.columns(2)
        with col1:
            cn = st.text_input("Customer Name")
            ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", dog_breeds + cat_breeds + ["Other"])
        with col2:
            age = st.text_input("Pet Age")
            wt = st.text_input("Weight (Kg)")
            vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE PET RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)])
            time.sleep(1); st.rerun()
    st.subheader("Registered Pets List")
    st.table(load_data("PetRecords").tail(10))
    if st.button("❌ DELETE LAST PET ENTRY"):
        if delete_data("PetRecords"): st.success("Pet Record Deleted!"); time.sleep(1); st.rerun()

# --- 10. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("opening_bal"):
        b_type = st.selectbox("Update Balance", ["Cash", "Online"]); b_amt = st.number_input("Enter Amount")
        if st.form_submit_button("SET BALANCE"):
            save_data("Balances", [b_type, b_amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.divider()
    with st.form("due"):
        comp = st.text_input("Company Name"); amt = st.number_input("Udhaar (+) / Payment (-)")
        if st.form_submit_button("SAVE DUES"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Dues").tail(5))
