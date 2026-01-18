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
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce', dayfirst=True).dt.date
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
    
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 else 0
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns)>3 else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns)>3 else 0
    
    total_stock_val = 0
    if not i_df.empty:
        total_stock_val = (pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum()
    
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h3 style="margin: 0;">₹{bc + sc - ec:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h3 style="margin: 0;">₹{bo + so - eo:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Mix Total</p> <h3 style="margin: 0;">₹{bc+bo+sc+so-ec-eo:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Today & Monthly Reports
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Today's Report")
        s_t = s_df[s_df['Date'] == today_dt] if not s_df.empty else pd.DataFrame()
        ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum()
        tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if len(s_t.columns)>7 else 0
        st.metric("Today Sale", f"₹{ts_d}"); st.metric("Today Profit", f"₹{tprof_d}")
    with c2:
        st.subheader("🗓️ Monthly Summary")
        s_m = s_df[pd.to_datetime(s_df['Date']).dt.month == curr_m] if not s_df.empty else pd.DataFrame()
        ts_mon = pd.to_numeric(s_m.iloc[:, 3], errors='coerce').sum()
        st.write(f"🔹 *Monthly Total Sale:* ₹{ts_mon}")

# --- 5. BILLING (POINTS + RECORD) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Customer Name"); c_ph = st.text_input("Phone Number"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"]); p = st.number_input("Price", 1.0)
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?")
        if st.button("➕ Add to Bill"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)*2); pts = -pts_bal if rd else pts
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()
    if not s_df.empty: st.divider(); st.subheader("Recent Sales"); st.dataframe(s_df.tail(10))

# --- 6. PURCHASE (WINDOW + RECORD) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add New Items", expanded=True):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt"]); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": f"{q} {u}", "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), "Cash"])
            st.session_state.pur_cart = []; st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty: st.divider(); st.subheader("Purchase History"); st.dataframe(i_df.tail(10))

# --- 7. LIVE STOCK (ALERT + TOTAL) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    if not i_df.empty:
        total_val = (pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum()
        st.subheader(f"💰 Total Stock Value: ₹{total_val:,.2f}")
        for _, row in i_df.iterrows():
            qty_val = float(str(row.iloc[1]).split()[0])
            if qty_val < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]}")

# --- 8. EXPENSES (WINDOW + RECORD) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Other"]); amt = st.number_input("Amount"); m = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, m]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty: st.divider(); st.subheader("Expense List"); st.dataframe(e_df)

# --- 9. PET REGISTER (WINDOW + RECORD) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        on = st.text_input("Owner Name"); oph = st.text_input("Phone Number"); br = st.selectbox("Breed", ["Labrador", "GSD", "Pug", "Indie", "Other"])
        if st.form_submit_button("Save Pet"): save_data("PetRecords", [on, oph, br, str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.divider(); st.subheader("Registered Pets"); st.dataframe(p_df)

# --- 10. CUSTOMER KHATA (WINDOW + RECORD) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amount"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        if st.form_submit_button("Save"): save_data("CustomerKhata", [n, a if "+" in t else -a, str(today_dt), "N/A"]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty: st.divider(); st.subheader("Khata List"); st.dataframe(k_df)

# --- 11. SUPPLIER DUES (WINDOW + RECORD) ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amount"); t = st.selectbox("Type", ["Maal (+)", "Payment (-)"])
        if st.form_submit_button("Save"): save_data("Dues", [s, a if "+" in t else -a, str(today_dt), "N/A"]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.divider(); st.subheader("Supplier Ledger"); st.dataframe(d_df)
