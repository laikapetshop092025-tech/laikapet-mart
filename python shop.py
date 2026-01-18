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
        # Photo Error Fix: Column checks
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True).dt.date
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

# --- 4. DASHBOARD (RESTORED PURANA LOGIC) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial Boxes logic with Safety Checks (IndexError fix)
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    
    total_stock_val = 0
    if not i_df.empty:
        # Stock Value calculation
        qty_col = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_col = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (qty_col * rate_col).sum()
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 31%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla Balance (Cash)</p> <h2 style="margin: 0;">₹{bc:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 31%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online Balance (Bank)</p> <h2 style="margin: 0;">₹{bo:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 31%;">
            <p style="color: #388E3C; margin: 0;">📦 Total Stock Value</p> <h2 style="margin: 0;">₹{total_stock_val:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Today's 4 Metrics (Sale, Purchase, Expense, Profit)
    st.divider(); st.subheader(f"📈 Today's Report")
    s_t = s_df[s_df['Date'] == today_dt] if not s_df.empty else pd.DataFrame()
    e_t = e_df[e_df['Date'] == today_dt] if not e_df.empty else pd.DataFrame()
    i_t = i_df[i_df['Date'] == today_dt] if not i_df.empty else pd.DataFrame()
    
    ts_d = pd.to_numeric(s_t.iloc[:, 3], errors='coerce').sum() if not s_t.empty else 0
    te_d = pd.to_numeric(e_t.iloc[:, 2], errors='coerce').sum() if not e_t.empty else 0
    tp_d = (pd.to_numeric(i_t.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_t.iloc[:, 3], errors='coerce').fillna(0)).sum() if not i_t.empty else 0
    tprof_d = pd.to_numeric(s_t.iloc[:, 7], errors='coerce').sum() if not s_t.empty and len(s_t.columns)>7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today Sale", f"₹{ts_d}"); c2.metric("Today Purchase", f"₹{tp_d}"); c3.metric("Today Expense", f"₹{te_d}"); c4.metric("Today Profit", f"₹{tprof_d}")

# --- 5. PURCHASE WINDOW (RESTORED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry Window")
    with st.expander("📥 Add New Items to Stock", expanded=True):
        n = st.text_input("Item Name"); q = st.number_input("Quantity", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        r = st.number_input("Purchase Rate"); p_m = st.selectbox("Paid From", ["Cash", "Online"])
        if st.button("➕ Add to List"):
            st.session_state.pur_cart.append({"Item": n, "Qty": f"{q} {u}", "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        if st.button("💾 Final Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), p_m])
            st.session_state.pur_cart = []; st.rerun()

# --- 6. CUSTOMER KHATA (BOX RESTORED) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata Entry")
    with st.form("khata_form"):
        name = st.text_input("Customer Name"); amt = st.number_input("Amount")
        act = st.selectbox("Action", ["Udhaar (+)", "Jama (-)"])
        if st.form_submit_button("Save Entry"):
            final_amt = amt if "+" in act else -amt
            save_data("CustomerKhata", [name, final_amt, str(today_dt), "N/A"])
            st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty: st.dataframe(k_df, use_container_width=True)

# --- 7. SUPPLIER DUES (BOX RESTORED) ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues Detail")
    with st.form("supp_form"):
        supp = st.text_input("Supplier Name"); amt = st.number_input("Amount")
        act = st.selectbox("Action", ["Maal Liya (+)", "Payment Di (-)"])
        if st.form_submit_button("Save Record"):
            final_amt = amt if "+" in act else -amt
            save_data("Dues", [supp, final_amt, str(today_dt), "N/A"])
            st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.dataframe(d_df, use_container_width=True)

# --- 8. LIVE STOCK (ALERTS & TOTAL) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    if not i_df.empty:
        # Total Amount calculation
        total_val = (pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum()
        st.subheader(f"💰 Total Stock Amount: ₹{total_val:,.2f}")
        for _, row in i_df.iterrows():
            qty_val = float(str(row.iloc[1]).split()[0])
            # Stock alert logic
            if qty_val < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]}")

# --- 9. BAAKI LOGICS (BILLING & EXPENSE & PET) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_ph = st.text_input("Customer Phone")
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); p = st.number_input("Price", 1.0)
        # Redeem Points logic
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?"); rf = st.checkbox("Referral (+10 Pts)")
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)*2); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": q, "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], "Cash", c_ph, item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Other"]); amt = st.number_input("Amount"); m = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"):
            save_data("Expenses", [str(today_dt), cat, amt, m]); st.rerun()

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        on = st.text_input("Owner Name"); oph = st.text_input("Phone"); br = st.text_input("Breed")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, oph, br, str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.dataframe(p_df, use_container_width=True)
