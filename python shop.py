import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse
import plotly.express as px

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_row(sheet_name, row_index):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete&row={row_index + 2}")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        # Date Safety Check
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, -1], errors='coerce')
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month

# --- 4. DASHBOARD (SALE, PURCHASE, EXPENSE, PROFIT RESTORED) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    # Financial Summary
    st.divider()
    def show_metrics(title, df_s, df_i, df_e, p_type="today"):
        m = (df_s['Date'].dt.date == today_dt) if p_type == "today" else (df_s['Date'].dt.month == curr_m)
        mi = (df_i['Date'].dt.date == today_dt) if p_type == "today" else (df_i['Date'].dt.month == curr_m)
        me = (df_e['Date'].dt.date == today_dt) if p_type == "today" else (df_e['Date'].dt.month == curr_m)
        
        ts = pd.to_numeric(df_s[m].iloc[:, 3], errors='coerce').sum() if not df_s.empty else 0
        tp = pd.to_numeric(df_i[mi].iloc[:, 1] * df_i[mi].iloc[:, 3], errors='coerce').sum() if not df_i.empty else 0
        te = pd.to_numeric(df_e[me].iloc[:, 2], errors='coerce').sum() if not df_e.empty else 0
        tpr = pd.to_numeric(df_s[m].iloc[:, 7], errors='coerce').sum() if not df_s.empty and len(df_s.columns)>7 else 0
        
        st.subheader(f"📈 {title} Report")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sale", f"₹{ts}"); c2.metric("Purchase", f"₹{tp}"); c3.metric("Expense", f"₹{te}"); c4.metric("Profit", f"₹{tpr}")

    show_metrics(f"Today ({today_dt})", s_df, i_df, e_df, "today")
    st.divider()
    show_metrics(f"Monthly ({datetime.now().strftime('%B')})", s_df, i_df, e_df, "month")

# --- 5. BILLING (UNIT & REDEEM RESTORED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Generate Bill")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        pur_rate = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
        c1, c2, c3 = st.columns(3)
        with c1: c_name = st.text_input("Customer Name"); q = st.number_input("Qty", 0.1)
        with c2: ph = st.text_input("Phone Number"); unit = st.selectbox("Unit", ["Kg", "Pcs", "Packet"])
        with c3: 
            pr = st.number_input("Price", 1.0); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
            pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(ph, na=False)].iloc[:, 6], errors='coerce').sum() if (ph and not s_df.empty) else 0
            st.write(f"🌟 Points: *{pts_bal}*")
            redeem = st.checkbox(f"Redeem {pts_bal} Pts?")
            
        if st.form_submit_button("SAVE BILL"):
            total = q * pr; profit = (pr - pur_rate) * q
            pts_add = int((total/100) * 2)
            if redeem: pts_add = -pts_bal
            save_data("Sales", [str(today_dt), it, f"{q} {unit}", total, mode, f"{c_name} ({ph})", pts_add, profit])
            st.success("Success!"); time.sleep(1); st.rerun()

# --- 6. LIVE STOCK (RED ALERT & DOWNLOAD RESTORED) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Alerts")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        p_v = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[2]: 'last'}).reset_index()
        p_v.columns = ['Item', 'In', 'Unit']
        if not s_df.empty:
            s_df['Out'] = s_df.iloc[:, 2].str.extract('(\d+\.?\d*)').astype(float)
            sold = s_df.groupby(s_df.columns[1])['Out'].sum().reset_index()
            stock = pd.merge(p_v, sold, left_on='Item', right_on=s_df.columns[1], how='left').fillna(0)
            stock['Rem'] = stock['In'] - stock['Out']
        else: stock = p_v; stock['Rem'] = stock['In']
        
        low = stock[stock['Rem'] <= 2]
        if not low.empty:
            st.error("⚠️ Low Stock Alert (2 or less left)!")
            st.download_button("📥 Download Order List", low.to_csv(index=False), "order.csv")
        
        for _, r in stock.iterrows():
            if r['Rem'] <= 2: st.error(f"❌ {r['Item']}: {r['Rem']} {r['Unit']} Left")
            else: st.info(f"✅ {r['Item']}: {r['Rem']} {r['Unit']} Left")

# --- 7. PET REGISTER (VAX DATES & DROP-DOWNS RESTORED) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breed_list = ["Labrador", "German Shepherd", "Pug", "Shih Tzu", "Persian Cat", "Indie Dog", "Other"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: on = st.text_input("Owner Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", breed_list)
        with c2: 
            age = st.selectbox("Age", [f"{i} Months" for i in range(1,12)] + [f"{i} Years" for i in range(1,15)])
            v_date = st.date_input("Vaccination Date")
            n_date = v_date + timedelta(days=365)
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, ph, br, age, str(v_date), str(n_date), str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            st.write(f"🐶 *{row.iloc[0]}* | Next Vax: {row.iloc[5]}"); st.button("❌", key=f"p_{i}", on_click=delete_row, args=("PetRecords", i))

# --- 8. EXPENSES, KHATA, PURCHASE & ADMIN (RESTORED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Other"])
        amt = st.number_input("Amount"); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.iterrows():
            st.write(f"💸 {row.iloc[1]}: ₹{row.iloc[2]}"); st.button("❌", key=f"e_{i}", on_click=delete_row, args=("Expenses", i))

elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs"]); p = st.number_input("Rate")
        if st.form_submit_button("Add"): save_data("Inventory", [n, q, u, p, str(today_dt)]); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.iterrows():
            st.write(f"📦 {row.iloc[0]} - {row.iloc[1]} {row.iloc[2]} @ ₹{row.iloc[3]}")

elif menu == "📒 Customer Khata":
    st.header("📒 Udhaar & Payment")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("Save"):
            f_amt = -amt if "Jama" in t else amt; save_data("CustomerKhata", [name, f_amt, str(today_dt)]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows(): st.warning(f"👤 {row.iloc[0]}: ₹{row.iloc[1]} Balance")

elif menu == "🎖️ Loyalty Club":
    st.header("🎖️ Loyalty Club Leaderboard")
    s_df = load_data("Sales")
    if not s_df.empty:
        loyalty = s_df.groupby(s_df.iloc[:, 5]).agg({s_df.columns[6]: 'sum'}).reset_index()
        st.dataframe(loyalty, use_container_width=True)

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Mode", ["Cash", "Online"]); b_a = st.number_input("Set Base Amount")
        if st.form_submit_button("Set Base"): save_data("Balances", [b_t, b_a, str(today_dt)]); st.rerun()
    st.divider(); st.subheader("🏢 Supplier Dues")
    with st.form("due"):
        comp = st.text_input("Company"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amt")
        if st.form_submit_button("Save"):
            f_amt = amt if "+" in type else -amt; save_data("Dues", [comp, f_amt, str(today_dt)]); st.rerun()
