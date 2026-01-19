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
curr_m_name = datetime.now().strftime('%B')

# --- 4. DASHBOARD (FIXED ERRORS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory"); k_df = load_data("CustomerKhata")
    
    # Financial Boxes logic with safety check for Photo Errors
    bc = pd.to_numeric(b_df.iloc[:, 1], errors='coerce').sum() if not b_df.empty and len(b_df.columns) > 1 else 0
    bo = pd.to_numeric(b_df.iloc[:, 1], errors='coerce').sum() if not b_df.empty and len(b_df.columns) > 1 else 0
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns) > 4 else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty and len(s_df.columns) > 4 else 0
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns) > 3 else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty and len(e_df.columns) > 3 else 0

    # Purchase deduction logic
    pc = 0; po = 0; total_stock_val = 0
    if not i_df.empty:
        i_df['qty_n'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate_n'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df['qty_n'] * i_df['rate_n']).sum()
        pc = (i_df[i_df.iloc[:, 5] == "Cash"]['qty_n'] * i_df[i_df.iloc[:, 5] == "Cash"]['rate_n']).sum() if len(i_df.columns)>5 else 0
        po = (i_df[i_df.iloc[:, 5] == "Online"]['qty_n'] * i_df[i_df.iloc[:, 5] == "Online"]['rate_n']).sum() if len(i_df.columns)>5 else 0

    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0
    final_cash = bc + sc - ec - pc
    final_bank = bo + so - eo - po

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla Balance</p> <h3 style="margin: 0;">₹{final_cash:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online Balance</p> <h3 style="margin: 0;">₹{final_bank:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Mix Total</p> <h3 style="margin: 0;">₹{final_cash + final_bank:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Today's & Monthly Report (4 metrics each)
    for title, mode in [("📈 Today's Report", "today"), (f"🗓️ {curr_m_name} Summary", "month")]:
        st.divider(); st.subheader(title)
        s_s = s_df[s_df['Date'] == today_dt] if (not s_df.empty and mode=="today") else (s_df[pd.to_datetime(s_df['Date']).dt.month == curr_m] if not s_df.empty else pd.DataFrame())
        i_s = i_df[i_df['Date'] == today_dt] if (not i_df.empty and mode=="today") else (i_df[pd.to_datetime(i_df['Date']).dt.month == curr_m] if not i_df.empty else pd.DataFrame())
        e_s = e_df[e_df['Date'] == today_dt] if (not e_df.empty and mode=="today") else (e_df[pd.to_datetime(e_df['Date']).dt.month == curr_m] if not e_df.empty else pd.DataFrame())
        
        sal = pd.to_numeric(s_s.iloc[:, 3], errors='coerce').sum() if not s_s.empty and len(s_s.columns)>3 else 0
        pur = (pd.to_numeric(i_s.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_s.iloc[:, 3], errors='coerce').fillna(0)).sum() if not i_s.empty and len(i_s.columns)>3 else 0
        ex = pd.to_numeric(e_s.iloc[:, 2], errors='coerce').sum() if not e_s.empty and len(e_s.columns)>2 else 0
        pr = pd.to_numeric(s_s.iloc[:, 7], errors='coerce').sum() if not s_s.empty and len(s_s.columns)>7 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sale", f"₹{sal}"); c2.metric("Purchase", f"₹{pur}"); c3.metric("Expense", f"₹{ex}"); c4.metric("Profit", f"₹{pr}")

# --- BAAKI SECTION MEIN NO CHANGES (LOGIC PRESERVED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Royalty")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Customer Name"); c_ph = st.text_input("Customer Phone")
    pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
    st.info(f"👑 Royalty Points: {pts_bal}")
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

elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add Stock", expanded=True):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt"]); r = st.number_input("Rate"); m = st.selectbox("Mode", ["Cash", "Online", "Hand"])
        if st.button("➕ Save"):
            save_data("Inventory", [n, f"{q} {u}", "Stock", r, str(today_dt), m]); st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        for _, row in i_df.iterrows():
            qty_val = float(str(row.iloc[1]).split()[0])
            if qty_val < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner"); ph = c2.text_input("Phone"); br = c1.text_input("Breed")
        age = c2.number_input("Age(M)", 1); wt = c1.number_input("Wt(Kg)", 0.1); vd = c2.date_input("Last Vax")
        if st.form_submit_button("Save"):
            nv = vd + timedelta(days=365)
            save_data("PetRecords", [on, ph, br, age, wt, str(vd), str(nv), str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.dataframe(p_df, use_container_width=True)

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amt"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        if st.form_submit_button("Save"):
            save_data("CustomerKhata", [n, a if "+" in t else -a, str(today_dt), "N/A"]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        st.table(sum_df[sum_df.iloc[:, 1] != 0])

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amt"); t = st.selectbox("Action", ["Maal (+)", "Payment (-)"])
        if st.form_submit_button("Save"):
            save_data("Dues", [s, a if "+" in t else -a, str(today_dt), "N/A"]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.dataframe(d_df, use_container_width=True)
