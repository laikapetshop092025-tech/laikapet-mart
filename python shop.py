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

# --- 3. SIDEBAR ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# --- 4. DASHBOARD (ALL PURANA LOGIC + 5 BOXES) ---
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
    
    pc = 0; po = 0; total_stock_val = 0
    if not i_df.empty:
        i_df['qty'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df['qty'] * i_df['rate']).sum()
        pc = (i_df[i_df.iloc[:, 5] == "Cash"]['qty'] * i_df[i_df.iloc[:, 5] == "Cash"]['rate']).sum() if len(i_df.columns)>5 else 0
        po = (i_df[i_df.iloc[:, 5] == "Online"]['qty'] * i_df[i_df.iloc[:, 5] == "Online"]['rate']).sum() if len(i_df.columns)>5 else 0

    kjc = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty else 0
    kjo = pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum() * -1 if not k_df.empty else 0
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h3 style="margin: 0;">₹{bc + sc + kjc - ec - pc:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h3 style="margin: 0;">₹{bo + so + kjo - eo - po:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Cash+Online</p> <h3 style="margin: 0;">₹{bc+bo+sc+so+kjc+kjo-ec-eo-pc-po:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    

    # TODAY & MONTHLY REPORT (4 metrics each)
    for title, d_filter in [("📈 Today's Report", today_dt), (f"🗓️ Monthly Summary ({curr_m_name})", "monthly")]:
        st.divider(); st.subheader(title)
        s_sub = s_df[s_df['Date'] == today_dt] if d_filter != "monthly" else s_df[pd.to_datetime(s_df['Date']).dt.month == curr_m]
        i_sub = i_df[i_df['Date'] == today_dt] if d_filter != "monthly" else i_df[pd.to_datetime(i_df['Date']).dt.month == curr_m]
        e_sub = e_df[e_df['Date'] == today_dt] if d_filter != "monthly" else e_df[pd.to_datetime(e_df['Date']).dt.month == curr_m]
        
        sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum()
        pur = (pd.to_numeric(i_sub.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_sub.iloc[:, 3], errors='coerce').fillna(0)).sum()
        exp = pd.to_numeric(e_sub.iloc[:, 2], errors='coerce').sum()
        prof = pd.to_numeric(s_sub.iloc[:, 7], errors='coerce').sum() if len(s_sub.columns)>7 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sale", f"₹{sale}"); c2.metric("Purchase", f"₹{pur}"); c3.metric("Expense", f"₹{exp}"); c4.metric("Profit", f"₹{prof}")

# --- 5. BILLING (REDEEM + REFERRAL + UNITS) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Customer Name"); c_ph = st.text_input("Phone Number"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"]); p = st.number_input("Price", 1.0)
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
        rd = st.checkbox(f"Redeem {pts_bal} Points?"); rf = st.checkbox("Referral Bonus (+10 Pts)")
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)* (5 if is_weekend else 2)); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    if st.session_state.bill_cart:
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            st.session_state.bill_cart = []; st.rerun()

# --- 6. PURCHASE (UNITS + MODE) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add Item", expanded=True):
        n = st.text_input("Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        r = st.number_input("Rate"); m = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
        if st.button("➕ Add Item"):
            st.session_state.pur_cart.append({"Item": n, "Qty": f"{q} {u}", "Rate": r, "Mode": m})
            st.rerun()
    if st.session_state.pur_cart:
        if st.button("💾 Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], "Stock", item['Rate'], str(today_dt), item['Mode']])
            st.session_state.pur_cart = []; st.rerun()

# --- 7. LIVE STOCK (ALERT + TOTAL AMT) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        total_v = (pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)).sum()
        st.subheader(f"💰 Total Stock Value: ₹{total_v:,.2f}")
        for _, row in i_df.iterrows():
            qty_val = float(str(row.iloc[1]).split()[0])
            if qty_val < 2: st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]} Left)")
            else: st.info(f"✅ {row.iloc[0]}: {row.iloc[1]} Left")

# --- 8. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Other"]); amt = st.number_input("Amount"); m = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"):
            save_data("Expenses", [str(today_dt), cat, amt, m]); st.rerun()

# --- 9. PET REGISTER (AGE + WT + AUTO-VACCINE) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner Name"); oph = c2.text_input("Phone Number")
        br = c1.selectbox("Breed", ["Labrador", "GSD", "Pug", "Shih Tzu", "Other"])
        age = c2.number_input("Age (Months)", 1); wt = c1.number_input("Weight (Kg)", 0.1)
        vd = c2.date_input("Last Vaccine Date")
        if st.form_submit_button("Save Pet"):
            next_v = vd + timedelta(days=365)
            save_data("PetRecords", [on, oph, br, age, wt, str(vd), str(next_v), str(today_dt)])
            st.success(f"Registered! Next Vaccine: {next_v}"); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty: st.dataframe(p_df, use_container_width=True)

# --- 10. CUSTOMER KHATA (ZERO BALANCE LOGIC) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amount"); t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"]); m = st.selectbox("Mode", ["Cash", "Online", "N/A"])
        if st.form_submit_button("Save Entry"):
            save_data("CustomerKhata", [n, a if "+" in t else -a, str(today_dt), m]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        summary = summary[summary.iloc[:, 1] != 0] # Sirf unhe dikhao jinhe paise dene hain
        st.subheader("📋 Active Balances"); st.table(summary)

# --- 11. SUPPLIER DUES ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amount"); t = st.selectbox("Action", ["Maal Liya (+)", "Payment Di (-)"]); m = st.selectbox("Mode", ["Cash", "Online", "Pocket"])
        if st.form_submit_button("Save"):
            save_data("Dues", [s, a if "+" in t else -a, str(today_dt), m]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty: st.dataframe(d_df, use_container_width=True)
