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
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True).dt.date
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce', dayfirst=True).dt.date
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# --- 4. DASHBOARD (FIXED REPORTS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial Boxes Calculations (Original Safe Logic)
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns)>4 else 0
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns)>3 else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns)>3 else 0
    
    pc = 0; po = 0; total_stock_val = 0
    if not i_df.empty:
        i_df.iloc[:, 1] = pd.to_numeric(i_df.iloc[:, 1], errors='coerce').fillna(0)
        i_df.iloc[:, 3] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df.iloc[:, 1] * i_df.iloc[:, 3]).sum()
        if len(i_df.columns) > 5:
            pc = (i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 1] * i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 3]).sum()
            po = (i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 1] * i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 3]).sum()

    kjc = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty and len(k_df.columns)>3 else 0
    kjo = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty and len(k_df.columns)>3 else 0
    spc = pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum() * -1 if not d_df.empty and len(d_df.columns)>3 else 0
    spo = pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum() * -1 if not d_df.empty and len(d_df.columns)>3 else 0
    
    g_cash = bc + sc + kjc - ec - pc - spc
    g_bank = bo + so + kjo - eo - po - spo
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h3 style="margin: 0;">₹{g_cash:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h3 style="margin: 0;">₹{g_bank:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Mix Balance</p> <h3 style="margin: 0;">₹{g_cash + g_bank:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- TODAY'S REPORT ---
    st.divider(); st.subheader(f"📈 Today's Report ({today_dt})")
    s_t = s_df[s_df['Date'] == today_dt] if not s_df.empty else pd.DataFrame()
    i_t = i_df[i_df['Date'] == today_dt] if not i_df.empty else pd.DataFrame()
    e_t = e_df[e_df['Date'] == today_dt] if not e_df.empty else pd.DataFrame()
    
    ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum()
    tp_d = (pd.to_numeric(i_t.iloc[:, 1], errors='coerce') * pd.to_numeric(i_t.iloc[:, 3], errors='coerce')).sum()
    te_d = pd.to_numeric(e_t.iloc[:, 2], errors='coerce').sum()
    tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if len(s_t.columns)>7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sale", f"₹{ts_d}"); c2.metric("Total Purchase", f"₹{tp_d}"); c3.metric("Total Expense", f"₹{te_d}"); c4.metric("Total Profit", f"₹{tprof_d}")

    # --- MONTHLY SUMMARY ---
    st.divider(); st.subheader(f"🗓️ Monthly Summary ({curr_m_name})")
    s_m = s_df[pd.to_datetime(s_df['Date']).dt.month == curr_m] if not s_df.empty else pd.DataFrame()
    i_m = i_df[pd.to_datetime(i_df['Date']).dt.month == curr_m] if not i_df.empty else pd.DataFrame()
    e_m = e_df[pd.to_datetime(e_df['Date']).dt.month == curr_m] if not e_df.empty else pd.DataFrame()
    
    ts_mon = pd.to_numeric(s_m.iloc[:, 3], errors='coerce').sum()
    tp_mon = (pd.to_numeric(i_m.iloc[:, 1], errors='coerce') * pd.to_numeric(i_m.iloc[:, 3], errors='coerce')).sum()
    te_mon = pd.to_numeric(e_m.iloc[:, 2], errors='coerce').sum()
    tprof_mon = pd.to_numeric(s_m.iloc[:, 7], errors='coerce').sum() if len(s_m.columns)>7 else 0

    st.write(f"🔹 *Monthly Sale:* ₹{ts_mon} | 🔹 *Monthly Purchase:* ₹{tp_mon}")
    st.write(f"🔹 *Monthly Expense:* ₹{te_mon} | ✅ *Monthly Profit:* ₹{tprof_mon}")

# --- 5. BILLING (POINTS & MODE RESTORED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Name"); c_ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); p = st.number_input("Price", 1.0)
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?"); rf = st.checkbox("Referral Bonus?")
        if st.button("➕ Add"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            pts = int(((q*p)/100)* (5 if is_weekend else 2)); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": q, "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        for i, item in enumerate(st.session_state.bill_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"*{item['Item']}* x {item['Qty']}")
            if c2.button("🗑️", key=f"b_{i}"): st.session_state.bill_cart.pop(i); st.rerun()
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Qty']*item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

# --- 6. LIVE STOCK (ALERT RESTORED) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    if not i_df.empty:
        stock_sum = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[3]: 'last'}).reset_index()
        for _, row in stock_sum.iterrows():
            if row.iloc[1] < 2: 
                st.error(f"🚨 ALERT LOW STOCK: {row.iloc[0]} ({row.iloc[1]} Left) - Refill!")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

# --- BAAKI ORIGINAL SECTIONS ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    p_from = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
    with st.expander("📥 Add Item"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": q, "Rate": r}); st.rerun()
    if st.session_state.pur_cart:
        for i, item in enumerate(st.session_state.pur_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"*{item['Item']}* x {item['Qty']}")
            if c2.button("🗑️", key=f"p_{i}"): st.session_state.pur_cart.pop(i); st.rerun()
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart: save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), p_from])
            st.session_state.pur_cart = []; st.rerun()

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Indie", "Other"]
    with st.form("pet"):
        on = st.text_input("Owner Name"); oph = st.text_input("Phone Number")
        br = st.selectbox("Breed", breeds); age = st.selectbox("Age (Months)", [str(i) for i in range(1, 121)])
        vd = st.date_input("Vax Date")
        if st.form_submit_button("Save"): save_data("PetRecords", [on, oph, br, age, str(vd), str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.dataframe(p_df)

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"]); m = st.selectbox("Mode", ["Cash", "Online", "N/A"])
        if st.form_submit_button("Save"): save_data("CustomerKhata", [name, amt if "+" in t else -amt, str(today_dt), m]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty: st.table(k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index())

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        comp = st.text_input("Supplier"); amt = st.number_input("Amount"); t = st.selectbox("Action", ["Maal (+)", "Payment (-)"]); m = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
        if st.form_submit_button("Save"): save_data("Dues", [comp, amt if "+" in t else -amt, str(today_dt), m]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.table(d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index())
