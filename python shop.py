import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

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
        # Ensure Date column is handled correctly to avoid KeyError
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        elif not df.empty and len(df.columns) >= 5:
            df.rename(columns={df.columns[4]: 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR ---
st.sidebar.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>👋 Welcome <br> Laika Pet Mart</h3>", unsafe_allow_html=True)
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

st.sidebar.divider()
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (TODAY + MONTHLY) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    today_dt = datetime.now().date(); curr_m = datetime.now().month
    curr_m_name = datetime.now().strftime('%B')

    op_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    op_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    exp_cash = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    exp_online = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    col_c, col_o, col_t = st.columns(3)
    with col_c: st.success(f"*Galla (Cash)*\n## ₹{(op_cash + sale_cash) - exp_cash:,.2f}")
    with col_o: st.info(f"*Bank (Online)*\n## ₹{(op_online + sale_online) - exp_online:,.2f}")
    with col_t: st.info(f"*Total Balance*\n## ₹{(op_cash + sale_cash - exp_cash) + (op_online + sale_online - exp_online):,.2f}")

    st.divider()

    def get_stats(sales_df, inv_df, exp_df, filter_type="today"):
        if sales_df.empty or 'Date' not in sales_df.columns: ts = 0
        else:
            mask = (sales_df['Date'].dt.date == today_dt) if filter_type == "today" else (sales_df['Date'].dt.month == curr_m)
            ts = pd.to_numeric(sales_df[mask].iloc[:, 3], errors='coerce').sum()
            
        if inv_df.empty or 'Date' not in inv_df.columns: tp = 0
        else:
            mask = (inv_df['Date'].dt.date == today_dt) if filter_type == "today" else (inv_df['Date'].dt.month == curr_m)
            tp = pd.to_numeric(inv_df[mask].iloc[:, 1] * inv_df[mask].iloc[:, 3], errors='coerce').sum()
            
        if exp_df.empty or 'Date' not in exp_df.columns: te = 0
        else:
            mask = (exp_df['Date'].dt.date == today_dt) if filter_type == "today" else (exp_df['Date'].dt.month == curr_m)
            te = pd.to_numeric(exp_df[mask].iloc[:, 2], errors='coerce').sum()
            
        return ts, tp, te, (ts - tp)

    ts, tp, te, tpr = get_stats(s_df, i_df, e_df, "today")
    st.markdown(f"#### 📅 Today: {today_dt.strftime('%d %B, %Y')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{ts:,.2f}"); c2.metric("Purchase", f"₹{tp:,.2f}"); c3.metric("Expense", f"₹{te:,.2f}"); c4.metric("Profit", f"₹{tpr:,.2f}")

# --- 5. BILLING (WITH DELETE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c3: mode = st.selectbox("Payment Mode", ["Cash", "Online"])
        pr = st.number_input("Price")
        cust_ph = st.text_input("Customer WhatsApp (91...)")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, mode]); time.sleep(1); st.rerun()
    s_df = load_data("Sales")
    if not s_df.empty:
        for i, row in s_df.tail(10).iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"*{row.iloc[1]}* | ₹{row.iloc[3]}")
            with col2:
                msg = f"🐾 LAIKA PET MART 🐾\nItem: {row.iloc[1]}\nTotal: ₹{row.iloc[3]}"
                st.markdown(f"[📲 Bill](https://wa.me/{cust_ph}?text={urllib.parse.quote(msg)})")
            with col3:
                if st.button("❌", key=f"s_{i}"): delete_row("Sales", i); st.rerun()

# --- 6. LIVE STOCK (RED ALERT FOR <= 2) ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Stock Quantity")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        purchased_v = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[2]: 'last'}).reset_index()
        purchased_v.columns = ['Item', 'Qty_In', 'Unit']
        if not s_df.empty:
            s_df['Sold_Qty'] = s_df.iloc[:, 2].str.extract('(\d+\.?\d*)').astype(float)
            sold_v = s_df.groupby(s_df.columns[1])['Sold_Qty'].sum().reset_index()
            sold_v.columns = ['Item', 'Qty_Out']
            stock_v = pd.merge(purchased_v, sold_v, on='Item', how='left').fillna(0)
            stock_v['Remaining'] = stock_v['Qty_In'] - stock_v['Qty_Out']
            
            # Re-order logic
            low_stock = stock_v[stock_v['Remaining'] <= 2]
            if not low_stock.empty:
                st.warning("⚠️ Items to Re-order:")
                order_list = "\n".join([f"- {row['Item']}" for _, row in low_stock.iterrows()])
                st.download_button("📥 Download Order List", order_list)

        for _, row in stock_v.iterrows():
            if row['Remaining'] <= 2:
                st.error(f"📦 *{row['Item']}*: {row['Remaining']} {row['Unit']} (STOCK BAHUT KAM HAI!)")
            else:
                st.info(f"📦 *{row['Item']}*: {row['Remaining']} {row['Unit']} bacha hai")

# --- 7. PET REGISTER (FIXED NameError & SyntaxError) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        c1_pet, c2_pet = st.columns(2) # Renamed to avoid name conflicts
        with c1_pet: cn = st.text_input("Customer Name"); ph = st.text_input("Phone"); br = st.text_input("Breed")
        with c2_pet: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    
    pet_df = load_data("PetRecords")
    if not pet_df.empty:
        for index, row in pet_df.iterrows():
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a: st.write(f"*{row.iloc[0]}* - {row.iloc[5]}")
            with col_b:
                msg = f"Namaste {row.iloc[0]}! Laika Pet Mart se vaccination reminder."
                wa_link = f"https://wa.me/{row.iloc[1]}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[🟢 WA Reminder]({wa_link})", unsafe_allow_html=True) 
            with col_c:
                if st.button("❌", key=f"p_{index}"): delete_row("PetRecords", index); st.rerun()
