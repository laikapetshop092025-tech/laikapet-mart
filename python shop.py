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
        elif not df.empty and len(df.columns) >= 5:
            df.rename(columns={df.columns[4]: 'Date'}, inplace=True)
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
st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>👋 Welcome <br> Laika Pet Mart</h3>")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

st.sidebar.divider()
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    today_dt = datetime.now().date(); curr_m = datetime.now().month
    curr_m_name = datetime.now().strftime('%B')

    # Balances
    op_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    op_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    exp_cash = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    exp_online = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    curr_cash = (op_cash + sale_cash) - exp_cash
    curr_online = (op_online + sale_online) - exp_online
    total_net_balance = curr_cash + curr_online

    st.markdown("### 💰 Real-Time Money Status")
    col_c, col_o, col_t = st.columns(3)
    with col_c: st.success(f"*Galla (Cash)*\n## ₹{curr_cash:,.2f}")
    with col_o: st.info(f"*Bank (Online)*\n## ₹{curr_online:,.2f}")
    with col_t: st.info(f"*Total Balance*\n## ₹{total_net_balance:,.2f}")
    
    st.divider()

    def get_stats(sales_df, inv_df, exp_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today_dt] if not sales_df.empty and 'Date' in sales_df.columns else pd.DataFrame()
            i_sub = inv_df[inv_df['Date'].dt.date == today_dt] if not inv_df.empty and 'Date' in inv_df.columns else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.date == today_dt] if not exp_df.empty and 'Date' in exp_df.columns else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty and 'Date' in sales_df.columns else pd.DataFrame()
            i_sub = inv_df[inv_df['Date'].dt.month == curr_m] if not inv_df.empty and 'Date' in inv_df.columns else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.month == curr_m] if not exp_df.empty and 'Date' in exp_df.columns else pd.DataFrame()
        
        t_sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum() if not s_sub.empty else 0
        t_pur = pd.to_numeric(i_sub.iloc[:, 1] * i_sub.iloc[:, 3], errors='coerce').sum() if not i_sub.empty else 0
        t_exp = pd.to_numeric(e_sub.iloc[:, 2], errors='coerce').sum() if not e_sub.empty else 0
        return t_sale, t_pur, t_exp, (t_sale - t_pur)

    ts, tp, te, tpr = get_stats(s_df, i_df, e_df, "today")
    ms, mp, me, mpr = get_stats(s_df, i_df, e_df, "month")
    
    # Today stats with Profit (S-P)
    st.markdown(f"#### 📅 Date: {today_dt.strftime('%d %B, %Y')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today Sale", f"₹{ts:,.2f}")
    c2.metric("Today Purchase", f"₹{tp:,.2f}")
    c3.metric("Today Expense", f"₹{te:,.2f}")
    c4.metric("Profit (S-P)", f"₹{tpr:,.2f}")

    st.divider()
    # Monthly stats with Profit (S-P)
    st.markdown(f"#### 🗓️ Month: {curr_m_name} {datetime.now().year}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly Sale", f"₹{ms:,.2f}")
    m2.metric("Monthly Purchase", f"₹{mp:,.2f}")
    m3.metric("Monthly Expense", f"₹{me:,.2f}")
    m4.metric("Monthly Profit (S-P)", f"₹{mpr:,.2f}")

# --- BAAKI TABS (SAB FIXED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c3: mode = st.selectbox("Payment Mode", ["Cash", "Online"])
        pr = st.number_input("Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, mode]); time.sleep(1); st.rerun()
    st.table(load_data("Sales").tail(10))
    if st.button("❌ DELETE LAST SALE"):
        if delete_data("Sales"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Pcs", "Kg"])
        with c2: p = st.number_input("Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, u, p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Inventory").tail(10))
    if st.button("❌ DELETE LAST PURCHASE"):
        if delete_data("Inventory"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Miscellaneous", "Other"])
        amt = st.number_input("Amount", min_value=0.0); mode = st.selectbox("Paid From", ["Cash", "Online"])
        if st.form_submit_button("Save Expense"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt, mode]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(10))
    if st.button("❌ DELETE LAST EXPENSE"):
        if delete_data("Expenses"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        inv_grouped = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[2]: 'last'}).reset_index()
        inv_grouped.columns = ['Item Name', 'Total Purchased', 'Unit']
        st.table(inv_grouped)

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    dog_breeds = ["Labrador", "German Shepherd", "Beagle", "Pug", "Indie Dog", "Shih Tzu"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Name"); ph = st.text_input("Phone"); br = st.selectbox("Breed", dog_breeds + ["Other"])
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    pet_df = load_data("PetRecords")
    if not pet_df.empty: pet_df = pet_df[pet_df.iloc[:, 0] != "Aman"]
    st.table(pet_df.tail(10))
    if st.button("❌ DELETE LAST PET"):
        if delete_data("PetRecords"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("opening_bal"):
        b_type = st.selectbox("Update Balance", ["Cash", "Online"]); b_amt = st.number_input("Enter Amount")
        if st.form_submit_button("SET BALANCE"):
            save_data("Balances", [b_type, b_amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.divider()
    with st.form("due"):
        comp = st.text_input("Company Name"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amount")
        if st.form_submit_button("SAVE"):
            final_amt = amt if "+" in type else -amt
            save_data("Dues", [comp, final_amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    dues_df = load_data("Dues")
    if not dues_df.empty: dues_df = dues_df[dues_df.iloc[:, 0] != "Baba Pet Shop"]
    st.table(dues_df.tail(10))
    if st.button("❌ DELETE LAST COMPANY ENTRY"):
        if delete_data("Dues"): st.success("Deleted!"); time.sleep(1); st.rerun()
