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
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True).dt.date
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN ---
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

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial boxes logic (Safe Calculation)
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    
    # Today's Report Fix (4 Boxes)
    st.divider(); st.subheader(f"📈 Today's Report ({today_dt})")
    s_t = s_df[s_df['Date'] == today_dt] if not s_df.empty else pd.DataFrame()
    e_t = e_df[e_df['Date'] == today_dt] if not e_df.empty else pd.DataFrame()
    i_t = i_df[i_df['Date'] == today_dt] if not i_df.empty else pd.DataFrame()
    
    ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum()
    te_d = pd.to_numeric(e_t.iloc[:, 2], errors='coerce').sum()
    tp_d = (pd.to_numeric(i_t.iloc[:, 1].str.split().str[0], errors='coerce') * pd.to_numeric(i_t.iloc[:, 3], errors='coerce')).sum()
    tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if len(s_t.columns)>7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{ts_d}"); c2.metric("Purchase", f"₹{tp_d}"); c3.metric("Expense", f"₹{te_d}"); c4.metric("Profit", f"₹{tprof_d}")

    # Monthly Summary (4 Boxes)
    st.divider(); st.subheader("🗓️ Monthly Summary")
    s_m = s_df[pd.to_datetime(s_df['Date']).dt.month == curr_m] if not s_df.empty else pd.DataFrame()
    e_m = e_df[pd.to_datetime(e_df['Date']).dt.month == curr_m] if not e_df.empty else pd.DataFrame()
    i_m = i_df[pd.to_datetime(i_df['Date']).dt.month == curr_m] if not i_df.empty else pd.DataFrame()
    
    ts_mon = pd.to_numeric(s_m.iloc[:, 3], errors='coerce').sum()
    te_mon = pd.to_numeric(e_m.iloc[:, 2], errors='coerce').sum()
    tp_mon = (pd.to_numeric(i_m.iloc[:, 1].str.split().str[0], errors='coerce') * pd.to_numeric(i_m.iloc[:, 3], errors='coerce')).sum()
    tprof_mon = pd.to_numeric(s_m.iloc[:, 7], errors='coerce').sum() if len(s_m.columns)>7 else 0
    
    st.write(f"🔹 *Monthly Sale:* ₹{ts_mon} | 🔹 *Monthly Purchase:* ₹{tp_mon}")
    st.write(f"🔹 *Monthly Expense:* ₹{te_mon} | ✅ *Monthly Profit:* ₹{tprof_mon}")

# --- 5. BILLING (UNIT & REDEEM ADDED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_ph = st.text_input("Customer Phone")
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Packet", "Grams"])
        p = st.number_input("Price", 1.0)
        
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?")
        
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)*2); pts = -pts_bal if rd else pts
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        for i, item in enumerate(st.session_state.bill_cart):
            st.write(f"{item['Item']} ({item['Qty']}) - ₹{item['Price']}")
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], "Cash", c_ph, item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

# --- 6. PURCHASE (UNIT ADDED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.expander("📥 Add Item"):
        n = st.text_input("Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Packet", "Grams"]); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": f"{q} {u}", "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), "Cash"])
            st.session_state.pur_cart = []; st.rerun()

# --- 7. LIVE STOCK (ALERT & TOTAL AMOUNT) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    if not i_df.empty:
        # Total Amount Logic
        total_val = (pd.to_numeric(i_df.iloc[:, 1].str.split().str[0], errors='coerce') * pd.to_numeric(i_df.iloc[:, 3], errors='coerce')).sum()
        st.subheader(f"💰 Total Stock Amount: ₹{total_val:,.2f}")
        
        for i, row in i_df.iterrows():
            qty_val = float(str(row.iloc[1]).split()[0])
            if qty_val < 2: st.error(f"🚨 ALERT LOW STOCK: {row.iloc[0]} ({row.iloc[1]} Left)")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

# --- 8. EXPENSES (RESTORED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Other"]); amt = st.number_input("Amount"); m = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, m]); st.rerun()

# --- BAAKI TABS ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Other"]
    with st.form("pet"):
        on = st.text_input("Owner Name"); br = st.selectbox("Breed", breeds); age = st.number_input("Age")
        if st.form_submit_button("Save Pet"): save_data("PetRecords", [on, br, age, str(today_dt)]); st.rerun()

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amount"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        if st.form_submit_button("Save"): save_data("CustomerKhata", [n, a if "+" in t else -a, str(today_dt)]); st.rerun()

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amount"); t = st.selectbox("Type", ["Maal (+)", "Payment (-)"])
        if st.form_submit_button("Save"): save_data("Dues", [s, a if "+" in t else -a, str(today_dt)]); st.rerun()
