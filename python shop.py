import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

if 'bill_cart' not in st.session_state: st.session_state.bill_cart = []
if 'pur_cart' not in st.session_state: st.session_state.pur_cart = []

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def load_data(sheet_name):
    try:
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        # Date detection fix for KeyError
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True).dt.date
            df = df.rename(columns={date_col: 'Date'})
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password")
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month

# --- 4. DASHBOARD (FIXED ERRORS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    # Financial Boxes logic with safety check for Photo Errors
    bc = pd.to_numeric(b_df.iloc[:, 1], errors='coerce').sum() if not b_df.empty and len(b_df.columns) > 1 else 0
    bo = pd.to_numeric(b_df.iloc[:, 1], errors='coerce').sum() if not b_df.empty and len(b_df.columns) > 1 else 0
    
    total_stock_val = 0
    if not i_df.empty and len(i_df.columns) >= 4:
        qty_clean = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        total_stock_val = (qty_clean * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum()
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 20px; border-radius: 10px; border-left: 10px solid #D32F2F; width: 31%;">
            <p style="color: #D32F2F; margin: 0; font-weight: bold;">💵 Galla Balance (Cash)</p> <h2 style="margin: 0;">₹{bc:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 10px solid #1976D2; width: 31%;">
            <p style="color: #1976D2; margin: 0; font-weight: bold;">🏦 Online Balance (Bank)</p> <h2 style="margin: 0;">₹{bo:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; border-left: 10px solid #388E3C; width: 31%;">
            <p style="color: #388E3C; margin: 0; font-weight: bold;">📦 Stock Value</p> <h2 style="margin: 0;">₹{total_stock_val:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Today's Report (Fixing Photo IndexError Line 112/115)
    st.divider(); st.subheader("📈 Today's Report")
    s_t = s_df[s_df['Date'] == today_dt] if not s_df.empty and 'Date' in s_df.columns else pd.DataFrame()
    e_t = e_df[e_df['Date'] == today_dt] if not e_df.empty and 'Date' in e_df.columns else pd.DataFrame()
    
    ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum() if not s_t.empty and len(s_t.columns) > 3 else 0
    te_d = pd.to_numeric(e_t.iloc[:, 2], errors='coerce').sum() if not e_t.empty and len(e_t.columns) > 2 else 0
    tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if not s_t.empty and len(s_t.columns) > 7 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts_d}"); c2.metric("Today Expense", f"₹{te_d}"); c3.metric("Today Profit", f"₹{tprof_d}")

# --- 5. BILLING (ROYALTY CLUB ADDED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Royalty Club")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Customer Name"); c_ph = st.text_input("Customer Phone")
    
    # Royalty Logic: Showing Points
    pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
    if c_ph: st.info(f"👑 Royalty Points: {pts_bal}")

    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"]); p = st.number_input("Price", 1.0)
        rd = st.checkbox(f"Redeem {pts_bal} Points?")
        
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)*2); pts = -pts_bal if rd else pts
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()

    if st.session_state.bill_cart:
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], "Cash", f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

# --- BAAKI SECTION MEIN NO CHANGES (LOGIC PRESERVED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.expander("📥 Add Stock", expanded=True):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); r = st.number_input("Rate")
        if st.button("➕ Save"):
            save_data("Inventory", [n, q, "Stock", r, str(today_dt), "Cash"])
            st.success("Added!"); st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        for _, row in i_df.iterrows():
            qv = float(str(row.iloc[1]).split()[0])
            if qv < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        on = st.text_input("Owner Name"); oph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "GSD", "Pug", "Other"])
        if st.form_submit_button("Save"):
            save_data("PetRecords", [on, oph, br, str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.dataframe(p_df)

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amt"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        if st.form_submit_button("Save"):
            save_data("CustomerKhata", [n, a if "+" in t else -a, str(today_dt)]); st.rerun()

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amt")
        if st.form_submit_button("Save"):
            save_data("Dues", [s, a, str(today_dt)]); st.rerun()
