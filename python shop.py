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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month

# --- 4. DASHBOARD (RESTORED + AUTO BALANCE & PROFIT) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>🌈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    # Auto-Balance Calculation
    base_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    base_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    exp_cash = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    exp_online = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 20px; border-radius: 10px; border-left: 10px solid #D32F2F; width: 32%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{base_cash + sale_cash - exp_cash:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 10px solid #1976D2; width: 32%;">
            <p style="color: #1976D2; margin: 0;">🏦 Bank (Online)</p> <h2 style="margin: 0;">₹{base_online + sale_online - exp_online:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; border-left: 10px solid #388E3C; width: 32%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Balance</p> <h2 style="margin: 0;">₹{base_cash + sale_cash - exp_cash + base_online + sale_online - exp_online:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def get_stats(df_s, f_type="today"):
        m = (df_s['Date'].dt.date == today_dt) if f_type == "today" else (df_s['Date'].dt.month == curr_m)
        ts = pd.to_numeric(df_s[m].iloc[:, 3], errors='coerce').sum() if not df_s.empty else 0
        tp = pd.to_numeric(df_s[m].iloc[:, 7], errors='coerce').sum() if (not df_s.empty and len(df_s.columns) > 7) else 0
        return ts, tp

    st.divider()
    ts, tp = get_stats(s_df, "today")
    st.subheader(f"📅 Today's Report")
    c1, c2 = st.columns(2)
    c1.metric("Sale Today", f"₹{ts}"); c2.metric("Profit Today", f"₹{tp}")

    st.divider()
    ms, mp = get_stats(s_df, "month")
    st.subheader(f"🗓️ Monthly Report")
    m1, m2 = st.columns(2)
    m1.metric("Monthly Sale", f"₹{ms}"); m2.metric("Monthly Profit", f"₹{mp}")

# --- 5. BILLING (RESTORED + SMART POINTS) ---
elif menu == "🧾 Billing":
    st.header("🧾 New Bill")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        p_rate = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Qty", 0.1); unit = st.selectbox("Unit", ["Kg", "Pcs", "Packet"])
        with c2: pr = st.number_input("Price", 1.0); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        with c3: ph = st.text_input("Phone")
        
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(ph, na=False)].iloc[:, 6], errors='coerce').sum() if (ph and not s_df.empty) else 0
        st.write(f"🌟 Customer Points: *{pts_bal}*")
        redeem = st.checkbox(f"Redeem {pts_bal} Points?")

        if st.form_submit_button("SAVE BILL"):
            total = q * pr; profit = (pr - p_rate) * q
            is_we = datetime.now().date().weekday() >= 5
            pts_add = int((total/100) * (5 if is_we else 2))
            if redeem: pts_add = -pts_bal
            save_data("Sales", [str(today_dt), it, f"{q} {unit}", total, mode, ph, pts_add, profit])
            st.success("Bill Saved!"); time.sleep(1); st.rerun()

# --- 6. PURCHASE (RESTORED FULL LIST) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Inventory")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Packet"]); p = st.number_input("Purchase Rate")
        if st.form_submit_button("Add to Stock"):
            save_data("Inventory", [n, q, u, p, str(today_dt)]); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.subheader("Recent Purchase List")
        for i, row in i_df.tail(15).iterrows():
            c1, c2 = st.columns([8, 1])
            c1.write(f"📦 {row.iloc[0]} - {row.iloc[1]} {row.iloc[2]} @ ₹{row.iloc[3]}")
            if c2.button("❌", key=f"i_{i}"): delete_row("Inventory", i); st.rerun()

# --- 7. LIVE STOCK (RESTORED ALERTS) ---
elif menu == "📋 Live Stock":
    st.header("📋 Stock Alerts")
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
        
        for _, r in stock.iterrows():
            if r['Rem'] <= 2: st.error(f"⚠️ {r['Item']}: {r['Rem']} {r['Unit']} Left!")
            else: st.info(f"✅ {r['Item']}: {r['Rem']} {r['Unit']} Left")

# --- 8. CUSTOMER KHATA (RESTORED) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Udhaar Khata")
    with st.form("kh"):
        name = st.text_input("Customer Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("Save Entry"):
            f_amt = amt if "Baki" in t else -amt; save_data("CustomerKhata", [name, f_amt, str(today_dt)]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] != 0: st.warning(f"👤 {row.iloc[0]}: ₹{row.iloc[1]} Balance")
        st.divider()
        for i, row in k_df.tail(10).iterrows():
            c1, c2 = st.columns([8, 1])
            c1.write(f"📅 {row.iloc[2]} | {row.iloc[0]}: ₹{row.iloc[1]}")
            if c2.button("❌", key=f"k_{i}"): delete_row("CustomerKhata", i); st.rerun()

# --- 9. ADMIN SETTINGS (RESTORED PLUS/MINUS) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Supplier Dues (Plus/Minus)")
    with st.form("due"):
        comp = st.text_input("Company Name"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amount")
        if st.form_submit_button("Save Due"):
            f_amt = amt if "+" in type else -amt; save_data("Dues", [comp, f_amt, str(today_dt)]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows(): st.error(f"🏢 {row.iloc[0]}: ₹{row.iloc[1]} Pending")

# (Expenses, Pet Register, Loyalty Club sections remain the same as your stable version)
