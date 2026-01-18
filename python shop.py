import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import plotly.express as px

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
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce', dayfirst=True)
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

# --- 3. SIDEBAR & LOGOUT ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')

# --- 4. DASHBOARD (FIXED FOR PHOTO ERRORS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial Calculation (Galla/Bank)
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sc = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 and "Cash" in str(s_df.iloc[:, 4]) else 0
    so = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 and "Online" in str(s_df.iloc[:, 4]) else 0
    
    # Today's Reports (SAFE CALCULATION FOR PHOTO ERRORS)
    st.divider(); st.subheader(f"📈 Today's Report ({today_dt})")
    s_t = s_df[s_df['Date'].dt.date == today_dt] if not s_df.empty else pd.DataFrame()
    i_t = i_df[i_df['Date'].dt.date == today_dt] if not i_df.empty else pd.DataFrame()
    e_t = e_df[e_df['Date'].dt.date == today_dt] if not e_df.empty else pd.DataFrame()

    ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum() if not s_t.empty and len(s_t.columns)>3 else 0
    tp_d = (pd.to_numeric(i_t.iloc[:, 1], errors='coerce') * pd.to_numeric(i_t.iloc[:, 3], errors='coerce')).sum() if not i_t.empty and len(i_t.columns)>3 else 0
    te_d = pd.to_numeric(e_t.iloc[:, 2], errors='coerce').sum() if not e_t.empty and len(e_t.columns)>2 else 0
    tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if not s_t.empty and len(s_t.columns)>7 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{ts_d}"); c2.metric("Purchase", f"₹{tp_d}"); c3.metric("Expense", f"₹{te_d}"); c4.metric("Profit", f"₹{tprof_d}")

    # Monthly Summary (SAFE CALCULATION)
    st.divider(); st.subheader(f"🗓️ Monthly Summary ({curr_m_name})")
    s_m = s_df[s_df['Date'].dt.month == curr_m] if not s_df.empty else pd.DataFrame()
    i_m = i_df[i_df['Date'].dt.month == curr_m] if not i_df.empty else pd.DataFrame()
    e_m = e_df[e_df['Date'].dt.month == curr_m] if not e_df.empty else pd.DataFrame()

    ts_mon = pd.to_numeric(s_m.iloc[:, 3], errors='coerce').sum() if not s_m.empty and len(s_m.columns)>3 else 0
    tp_mon = (pd.to_numeric(i_m.iloc[:, 1], errors='coerce') * pd.to_numeric(i_m.iloc[:, 3], errors='coerce')).sum() if not i_m.empty and len(i_m.columns)>3 else 0
    te_mon = pd.to_numeric(e_m.iloc[:, 2], errors='coerce').sum() if not e_m.empty and len(e_m.columns)>2 else 0
    tprof_mon = pd.to_numeric(s_m.iloc[:, 7], errors='coerce').sum() if not s_m.empty and len(s_m.columns)>7 else 0

    st.write(f"🔹 *Monthly Total Sale:* ₹{ts_mon} | 🔹 *Monthly Total Purchase:* ₹{tp_mon}")
    st.write(f"🔹 *Monthly Total Expense:* ₹{te_mon} | ✅ *Monthly Net Profit:* ₹{tprof_mon}")

# --- BAAKI ALL TABS (WORD-TO-WORD SAME) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Name"); c_ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); p = st.number_input("Price", 1.0)
        if st.button("➕ Add"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": q, "Price": p, "Profit": (p-pur_r)*q})
            st.rerun()
    if st.session_state.bill_cart:
        for i, item in enumerate(st.session_state.bill_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"{item['Item']} x {item['Qty']}")
            if c2.button("🗑️", key=f"b_{i}"): st.session_state.bill_cart.pop(i); st.rerun()
        if st.button("✅ Save"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Qty']*item['Price'], pay_m, f"{c_name}({c_ph})", 0, item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    p_from = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
    with st.expander("📥 Add Item"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": q, "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        for i, item in enumerate(st.session_state.pur_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"{item['Item']} x {item['Qty']}")
            if c2.button("🗑️", key=f"p_{i}"): st.session_state.pur_cart.pop(i); st.rerun()
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Pcs", item['Rate'], str(today_dt), p_from])
            st.session_state.pur_cart = []; st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        stock_sum = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[3]: 'last'}).reset_index()
        total_v = (stock_sum.iloc[:, 1] * stock_sum.iloc[:, 2]).sum()
        st.subheader(f"💰 Total Stock Value: ₹{total_v:,.2f}")
        for i, row in stock_sum.iterrows(): st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Indie", "Other"]
    with st.form("pet"):
        on = st.text_input("Owner Name"); oph = st.text_input("Phone Number")
        br = st.selectbox("Breed", breeds); age = st.selectbox("Age (Months)", [str(i) for i in range(1, 121)])
        vd = st.date_input("Vax Date")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, oph, br, age, str(vd), str(vd+timedelta(365)), str(today_dt)]); st.rerun()

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amount"); t = st.selectbox("Action", ["Udhaar (+)", "Jama (-)"]); m = st.selectbox("Mode", ["Cash", "Online", "N/A"])
        if st.form_submit_button("Save"):
            save_data("CustomerKhata", [name, amt if "+" in t else -amt, str(today_dt), m]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        st.table(summary[summary.iloc[:, 1] != 0])

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        comp = st.text_input("Supplier"); amt = st.number_input("Amount"); t = st.selectbox("Action", ["Maal (+)", "Payment (-)"]); m = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
        if st.form_submit_button("Save"):
            save_data("Dues", [comp, amt if "+" in t else -amt, str(today_dt), m]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        st.table(summary)
