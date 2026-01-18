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
    
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    # Safe Purchase Calculation
    pc = 0; po = 0; total_stock_val = 0
    if not i_df.empty and len(i_df.columns) >= 6:
        pc = (pd.to_numeric(i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 1], errors='coerce') * pd.to_numeric(i_df[i_df.iloc[:, 5] == "Cash"].iloc[:, 3], errors='coerce')).sum()
        po = (pd.to_numeric(i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 1], errors='coerce') * pd.to_numeric(i_df[i_df.iloc[:, 5] == "Online"].iloc[:, 3], errors='coerce')).sum()
        total_stock_val = (pd.to_numeric(i_df.iloc[:, 1], errors='coerce') * pd.to_numeric(i_df.iloc[:, 3], errors='coerce')).sum()
    
    kjc = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty else 0
    kjo = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty else 0
    spc = pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum() * -1 if not d_df.empty else 0
    spo = pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum() * -1 if not d_df.empty else 0
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 24%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{bc + sc + kjc - ec - pc - spc:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 24%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h2 style="margin: 0;">₹{bo + so + kjo - eo - po - spo:,.2f}</h2>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 24%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h2 style="margin: 0;">₹{total_u:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 24%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h2 style="margin: 0;">₹{total_stock_val:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    st.divider(); st.subheader(f"📈 Today's Report ({today_dt})")
    s_today = s_df[s_df['Date'].dt.date == today_dt] if not s_df.empty else pd.DataFrame()
    ts_d = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum()
    te_d = pd.to_numeric(e_df[e_df['Date'].dt.date == today_dt].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    tprof_d = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum() if len(s_today.columns)>7 else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts_d}"); c2.metric("Today Expense", f"₹{te_d}"); c3.metric("Today Profit", f"₹{tprof_d}")

    # Sales Graph
    if not s_df.empty:
        fig = px.line(s_df.groupby(s_df['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index().tail(7), x='Date', y=s_df.columns[3], title="Sales Trend")
        st.plotly_chart(fig, use_container_width=True)

    # Monthly Text Summary
    st.subheader(f"🗓️ Monthly Summary ({curr_m_name})")
    s_mon = s_df[s_df['Date'].dt.month == curr_m] if not s_df.empty else pd.DataFrame()
    st.write(f"🔹 *Monthly Sale:* ₹{pd.to_numeric(s_mon.iloc[:, 3], errors='coerce').sum()}")
    st.write(f"✅ *Monthly Profit:* ₹{pd.to_numeric(s_mon.iloc[:, 7], errors='coerce').sum() if len(s_mon.columns)>7 else 0}")

# --- 5. BAAKI SECTIONS (REMAINS WORD TO WORD SAME) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Name"); c_ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); p = st.number_input("Price", 1.0)
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(c_ph, na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?"); rf = st.checkbox("Referral")
        if st.button("➕ Add"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            pts = int(((q*p)/100)*2); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": q, "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        for i, item in enumerate(st.session_state.bill_cart):
            col1, col2 = st.columns([4, 1]); col1.write(f"{item['Item']} x {item['Qty']}")
            if col2.button("🗑️", key=f"del_b_{i}"): st.session_state.bill_cart.pop(i); st.rerun()
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Qty']*item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.success("Saved!"); st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    p_from = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
    with st.expander("📥 Add Items"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); r = st.number_input("Rate")
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": q, "Rate": r})
            st.rerun()
    if st.session_state.pur_cart:
        for i, item in enumerate(st.session_state.pur_cart):
            col1, col2 = st.columns([4, 1]); col1.write(f"{item['Item']} x {item['Qty']}")
            if col2.button("🗑️", key=f"del_p_{i}"): st.session_state.pur_cart.pop(i); st.rerun()
        if st.button("💾 Final Save"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Pcs", item['Rate'], str(today_dt), p_from])
            st.session_state.pur_cart = []; st.success("Updated!"); st.rerun()

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    if not i_df.empty:
        stock_sum = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum'}).reset_index()
        for i, row in stock_sum.iterrows():
            if row.iloc[1] < 2: st.error(f"🚨 {row.iloc[0]}: {row.iloc[1]} Left (Refill!)")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Indie", "Other"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner Name"); oph = c2.text_input("Phone Number")
        br = c1.selectbox("Breed", breeds); age = c2.selectbox("Age (Months)", [str(i) for i in range(1, 121)])
        vd = st.date_input("Vax Date")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, oph, br, age, str(vd), str(vd+timedelta(365)), str(today_dt)])
            st.success("Registered!"); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"🐶 {row.iloc[0]} | Next Vax: {row.iloc[5]}")
            if c2.button("❌", key=f"pdel_{i}"): delete_row("PetRecords", i); st.rerun()

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("khata"):
        name = st.text_input("Name"); amt = st.number_input("Amount")
        t = st.selectbox("Action", ["Udhaar (+)", "Jama (-)"])
        m = st.selectbox("Mode (If Jama)", ["Cash", "Online", "N/A"])
        if st.form_submit_button("Save"):
            f_amt = amt if "+" in t else -amt
            save_data("CustomerKhata", [name, f_amt, str(today_dt), m]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        st.table(summary[summary.iloc[:, 1] != 0])
        for i, row in k_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"📒 {row.iloc[0]} | ₹{row.iloc[1]}")
            if c2.button("❌", key=f"kdel_{i}"): delete_row("CustomerKhata", i); st.rerun()

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        comp = st.text_input("Supplier"); amt = st.number_input("Amount")
        t = st.selectbox("Action", ["Maal Liya (+)", "Payment Diya (-)"])
        m = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
        if st.form_submit_button("Save"):
            f_amt = amt if "+" in t else -amt
            save_data("Dues", [comp, f_amt, str(today_dt), m]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        st.table(summary)
        for i, row in d_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"🏢 {row.iloc[0]} | ₹{row.iloc[1]}")
            if c2.button("❌", key=f"ddel_{i}"): delete_row("Dues", i); st.rerun()
