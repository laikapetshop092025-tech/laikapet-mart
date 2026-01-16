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
        # Fix for KeyError: Automatic Date detection
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "🎖️ Loyalty Club", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "⚙️ Admin Settings"])

if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month

# --- 4. DASHBOARD (TODAY + MONTHLY + GRAPH) ---
if menu == "📊 Dashboard":
    st.header("📈 Dashboard")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    c_bal = pd.to_numeric(b_df[b_df.iloc[:,0]=="Cash"].iloc[:,1], errors='coerce').sum() if not b_df.empty else 0
    o_bal = pd.to_numeric(b_df[b_df.iloc[:,0]=="Online"].iloc[:,1], errors='coerce').sum() if not b_df.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Cash Balance", f"₹{c_bal:,.2f}")
    col2.metric("Online Balance", f"₹{o_bal:,.2f}")
    col3.metric("Total", f"₹{c_bal + o_bal:,.2f}")

    if not s_df.empty and 'Date' in s_df.columns:
        st.divider()
        st.subheader("7 Days Sale Trend")
        last_7 = s_df[s_df['Date'] >= pd.to_datetime(today_dt - timedelta(days=7))]
        chart = last_7.groupby(last_7['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index()
        st.plotly_chart(px.line(chart, x='Date', y=s_df.columns[3], markers=True), use_container_width=True)

    st.divider()
    st.subheader(f"Monthly Stats ({datetime.now().strftime('%B')})")
    m_sale = s_df[s_df['Date'].dt.month == curr_m].iloc[:,3].sum() if not s_df.empty else 0
    st.metric("Total Monthly Sale", f"₹{m_sale:,.2f}")

# --- 5. BILLING (WITH POINTS) ---
elif menu == "🧾 Billing":
    st.header("🧾 New Bill")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:,0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", 1.0); pr = st.number_input("Price", 1.0)
        with c2: ph = st.text_input("Customer Phone"); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        if st.form_submit_button("Save Bill"):
            pts = int((q*pr)/100)
            save_data("Sales", [str(today_dt), it, f"{q} Pcs", q*pr, mode, ph, pts])
            st.success("Bill Saved!"); time.sleep(1); st.rerun()
    
    s_df = load_data("Sales")
    if not s_df.empty:
        for i, row in s_df.tail(10).iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"*{row.iloc[1]}* | ₹{row.iloc[3]}")
            with col2:
                msg = f"Namaste! Laika Pet Mart Bill: ₹{row.iloc[3]}. Points: {row.iloc[6]}"
                st.markdown(f"[🟢 WA Bill](https://wa.me/{row.iloc[5]}?text={urllib.parse.quote(msg)})")
            with col3:
                if st.button("❌", key=f"s_{i}"): delete_row("Sales", i); st.rerun()

# --- 6. PET REGISTER (FIXED) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Owner"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Lab", "GSD", "Pug", "Indie", "Other"])
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vax Date")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [name, ph, br, age, wt, str(vax)])
            st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            col1, col2, col3 = st.columns([5, 3, 1])
            with col1: st.write(f"🐶 *{row.iloc[0]}* | Age: {row.iloc[3]} | Wt: {row.iloc[4]}")
            with col2:
                wa_l = f"https://wa.me/{row.iloc[1]}?text=Reminder"
                st.markdown(f"[🟢 WA]({wa_l})")
            with col3:
                if st.button("❌", key=f"p_{i}"): delete_row("PetRecords", i); st.rerun()

# --- 7. EXPENSES (RESTORED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.text_input("Category"); amt = st.number_input("Amount"); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"):
            save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"💸 {row.iloc[1]} - ₹{row.iloc[2]}")
            if col2.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

# --- BAAKI SAB (Purchase, Khata, Admin) KEPT ORIGINAL ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item"); q = st.number_input("Qty"); p = st.number_input("Price")
        if st.form_submit_button("Add"):
            save_data("Inventory", [n, q, "Pcs", p, str(today_dt)]); st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.dataframe(i_df)

elif menu == "📒 Customer Khata":
    st.header("📒 Khata")
    # Purana Khata Code yahan rahega...

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin")
    # Purana Admin Dues Code yahan rahega...
