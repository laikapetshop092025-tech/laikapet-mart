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
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
is_weekend = datetime.now().weekday() >= 5

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    # Financial Boxes
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    total_stock_val = (pd.to_numeric(i_df.iloc[:, 1], errors='coerce').fillna(0) * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum() if not i_df.empty else 0
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 45%;">
            <p style="color: #D32F2F; margin: 0;">💵 Total Balance (Cash+Bank)</p> <h2 style="margin: 0;">₹{bc + bo:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 45%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h2 style="margin: 0;">₹{total_stock_val:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. BILLING (UNIT + 2 REDEEM OPTIONS) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_ph = st.text_input("Customer Phone")
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Pcs", "Kg", "Pkt", "Grams"])
        p = st.number_input("Price", 1.0)
        
        # 2 Redeem Options logic
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(c_ph, na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?"); rf = st.checkbox("Referral (+10 Pts)")
        
        if st.button("➕ Add to Bill"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            pts = int(((q*p)/100)* (5 if is_weekend else 2))
            pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    # Cart Display and Save
    if st.session_state.bill_cart:
        for i, item in enumerate(st.session_state.bill_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"*{item['Item']}* ({item['Qty']})")
            if c2.button("🗑️", key=f"b_{i}"): st.session_state.bill_cart.pop(i); st.rerun()
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], "Cash", c_ph, item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

# --- 6. PURCHASE (UNIT ADDED) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add Items", expanded=True):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Pcs", "Kg", "Pkt", "Grams"]); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": f"{q} {u}", "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        for i, item in enumerate(st.session_state.pur_cart):
            c1, c2 = st.columns([4, 1]); c1.write(f"*{item['Item']}* ({item['Qty']})")
            if c2.button("🗑️", key=f"p_{i}"): st.session_state.pur_cart.pop(i); st.rerun()
        if st.button("💾 Final Save"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), "Cash"])
            st.session_state.pur_cart = []; st.rerun()

# --- 7. LIVE STOCK (ALERT LOGIC) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.iterrows():
            try: qty_val = float(str(row.iloc[1]).split()[0])
            except: qty_val = 0
            if qty_val < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]}")

# --- 8. PET REGISTER (RESTORED HISTORY) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Indie", "Other"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner Name"); br = c2.selectbox("Breed", breeds)
        age = c1.selectbox("Age (Months)", [str(i) for i in range(1, 121)])
        vd = st.date_input("Vax Date")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, br, age, str(vd), str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        st.divider(); st.subheader("Registered Pets"); st.dataframe(p_df)

# --- 9. CUSTOMER KHATA (ADDED) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("khata"):
        name = st.text_input("Customer Name"); amt = st.number_input("Amount")
        act = st.selectbox("Action", ["Udhaar (+)", "Jama (-)"]); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save Entry"):
            final_amt = amt if "+" in act else -amt
            save_data("CustomerKhata", [name, final_amt, str(today_dt), mode]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty: st.dataframe(k_df)

# --- 10. SUPPLIER DUES (ADDED) ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("dues"):
        supp = st.text_input("Supplier Name"); amt = st.number_input("Amount")
        act = st.selectbox("Action", ["Maal Liya (+)", "Payment Di (-)"]); mode = st.selectbox("Paid Via", ["Cash", "Online"])
        if st.form_submit_button("Save Record"):
            final_amt = amt if "+" in act else -amt
            save_data("Dues", [supp, final_amt, str(today_dt), mode]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.dataframe(d_df)
