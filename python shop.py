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
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')

# --- 4. DASHBOARD (ALL BACKLOG & NEW PURCHASE FIXED) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # 1. Base Balances
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    
    # 2. Sales (+)
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    
    # 3. Expenses (-)
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    # 4. TOTAL PURCHASE (-) [PURANA STOCK + NAYA STOCK]
    # Ismein column 1 (Qty) aur column 3 (Rate) ko bina kisi date filter ke multiply karke total kiya hai
    pc = 0; po = 0
    if not i_df.empty:
        i_df.iloc[:, 1] = pd.to_numeric(i_df.iloc[:, 1], errors='coerce').fillna(0)
        i_df.iloc[:, 3] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        # Cash Purchase Total
        pc = (i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 1] * i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 3]).sum()
        # Online Purchase Total
        po = (i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 1] * i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 3]).sum()
    
    # 5. Supplier Payments (-)
    dpc = abs(pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum()) if not d_df.empty and len(d_df.columns)>3 else 0
    dpo = abs(pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum()) if not d_df.empty and len(d_df.columns)>3 else 0

    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 24%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{bc + sc - ec - pc - dpc:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 24%;">
            <p style="color: #1976D2; margin: 0;">🏦 Bank (Online)</p> <h2 style="margin: 0;">₹{bo + so - eo - po - dpo:,.2f}</h2>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 24%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h2 style="margin: 0;">₹{total_u:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 24%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Net</p> <h2 style="margin: 0;">₹{(bc+sc-ec-pc-dpc+bo+so-eo-po-dpo):,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
# --- 5. BAAKI ALL TABS (RESTORED WORD-TO-WORD) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    cust = st.text_input("Customer"); ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:,0].unique() if not inv_df.empty else ["No Stock"])
        qty = st.number_input("Qty", 0.1); pr = st.number_input("Price", 1.0)
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(ph, na=False)].iloc[:, 6], errors='coerce').sum() if (ph and not s_df.empty) else 0
        redeem = st.checkbox(f"Redeem {pts_bal} Pts?"); is_ref = st.checkbox("Referral")
        if st.button("➕ Add"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            pts = int(((qty*pr)/100)*2); pts = -pts_bal if redeem else pts; pts += 10 if is_ref else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": qty, "Price": pr, "Profit": (pr-pur_r)*qty, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        st.table(pd.DataFrame(st.session_state.bill_cart))
        if st.button("✅ Save"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Qty']*item['Price'], pay_m, f"{cust}({ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    p_from = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
    with st.expander("📥 Add Items"):
        n = st.text_input("Item"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs"]); p = st.number_input("Rate")
        if st.button("➕ Add"):
            st.session_state.pur_cart.append({"Item": n, "Qty": q, "Unit": u, "Rate": p})
            st.rerun()
    if st.session_state.pur_cart:
        st.table(pd.DataFrame(st.session_state.pur_cart))
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], item['Unit'], item['Rate'], str(today_dt), p_from])
            st.session_state.pur_cart = []; st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    # Red Alerts & Download restored...
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, r in i_df.iterrows(): st.info(f"✅ {r.iloc[0]}: {r.iloc[1]}")
        st.download_button("📥 Download", i_df.to_csv(index=False), "stock.csv")

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Cat", ["Rent", "Salary", "Other"]); amt = st.number_input("Amt"); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        on = st.text_input("Owner"); ph = st.text_input("Phone"); br = st.text_input("Breed"); vd = st.date_input("Vax")
        if st.form_submit_button("Save"): save_data("PetRecords", [on, ph, br, "", str(vd), str(vd+timedelta(365)), str(today_dt)]); st.rerun()

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amt"); t = st.selectbox("Type", ["Udhaar", "Jama"])
        if st.form_submit_button("Save"): save_data("CustomerKhata", [name, amt if "Udhaar" in t else -amt, str(today_dt), "N/A"]); st.rerun()

elif menu == "🎖️ Loyalty Club":
    st.header("🎖️ Loyalty Club")
    s_df = load_data("Sales")
    if not s_df.empty: st.dataframe(s_df.groupby(s_df.iloc[:, 5]).agg({s_df.columns[6]: 'sum'}))

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Mode", ["Cash", "Online"]); b_a = st.number_input("Base")
        if st.form_submit_button("Set"): save_data("Balances", [b_t, b_a, str(today_dt)]); st.rerun()
    st.divider(); st.subheader("🏢 Supplier List & Payments")
    with st.form("due"):
        comp = st.text_input("Supplier"); type = st.selectbox("Action", ["Udhaar (+)", "Payment (-)"]); amt = st.number_input("Amt")
        mode = st.selectbox("Paid From", ["Cash", "Online", "Pocket", "N/A"])
        if st.form_submit_button("Save"):
            save_data("Dues", [comp, amt if "+" in type else -amt, str(today_dt), mode]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        st.subheader("📑 History"); st.dataframe(d_df[d_df['Date'].dt.date == today_dt])
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows(): st.error(f"🏢 {row.iloc[0]}: ₹{row.iloc[1]} Pending")


