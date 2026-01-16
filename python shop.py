import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse
import plotly.express as px

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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "⚙️ Admin Settings"])

st.sidebar.divider()
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (ANALYTICS) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    today_dt = datetime.now().date(); curr_m = datetime.now().month
    curr_m_name = datetime.now().strftime('%B')

    # Cash/Online Logic
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

    def get_stats(sales_df, inv_df, exp_df, filter_type="today"):
        mask_s = (sales_df['Date'].dt.date == today_dt) if filter_type == "today" else (sales_df['Date'].dt.month == curr_m)
        mask_i = (inv_df['Date'].dt.date == today_dt) if filter_type == "today" else (inv_df['Date'].dt.month == curr_m)
        ts = pd.to_numeric(sales_df[mask_s].iloc[:, 3], errors='coerce').sum() if not sales_df.empty else 0
        tp = pd.to_numeric(inv_df[mask_i].iloc[:, 1] * inv_df[mask_i].iloc[:, 3], errors='coerce').sum() if not inv_df.empty else 0
        return ts, tp, (ts - tp)

    ts, tp, tpr = get_stats(s_df, i_df, e_df, "today")
    st.divider()
    st.markdown(f"#### 📅 Today: {today_dt.strftime('%d %B')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts:,.2f}"); c2.metric("Today Purchase", f"₹{tp:,.2f}"); c3.metric("Today Profit", f"₹{tpr:,.2f}")

    # Feature 3: Analytics Graph
    st.divider()
    st.markdown("#### 📊 Sales Trend (Last 7 Days)")
    if not s_df.empty:
        last_7 = s_df[s_df['Date'] >= pd.to_datetime(today_dt - timedelta(days=7))]
        chart_data = last_7.groupby(last_7['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index()
        chart_data.columns = ['Date', 'Sale']
        fig = px.line(chart_data, x='Date', y='Sale', markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# --- 5. BILLING (LOYALTY POINTS) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Loyalty Points")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 0.1); unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c2: pr = st.number_input("Price"); mode = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
        with c3: ph = st.text_input("Customer Phone (91...)")
        if st.form_submit_button("SAVE BILL"):
            pts = int((q * pr) / 100) # Feature 2: Loyalty
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, mode, ph, pts])
            time.sleep(1); st.rerun()
    s_df = load_data("Sales")
    if not s_df.empty:
        for i, row in s_df.tail(10).iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"*{row.iloc[1]}* | ₹{row.iloc[3]} ({row.iloc[4]})")
            with col2:
                msg = f"🐾 LAIKA PET MART\nBill: ₹{row.iloc[3]}\nPoints: {row.iloc[6]}\nMode: {row.iloc[4]}"
                st.markdown(f"[📲 Bill](https://wa.me/{row.iloc[5]}?text={urllib.parse.quote(msg)})")
            with col3:
                if st.button("❌", key=f"s_{i}"): delete_row("Sales", i); st.rerun()

# --- 6. CUSTOMER KHATA (NEW FEATURE 1) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Digital Udhaar Diary")
    with st.form("cust_khata"):
        name = st.text_input("Customer Name"); amt = st.number_input("Amount"); k_type = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("SAVE TO KHATA"):
            f_amt = amt if "Baki" in k_type else -amt
            save_data("CustomerKhata", [name, f_amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    
    khata_df = load_data("CustomerKhata")
    if not khata_df.empty:
        summary = khata_df.groupby(khata_df.columns[0]).agg({khata_df.columns[1]: 'sum'}).reset_index()
        summary.columns = ['Customer', 'Net Udhaar']
        st.subheader("Total Pending Payments")
        for i, row in summary.iterrows():
            if row['Net Udhaar'] != 0:
                c1, c2 = st.columns([8, 2])
                with c1: st.warning(f"👤 *{row['Customer']}*: ₹{row['Net Udhaar']} baki hain")
                with c2: 
                    reminder = f"Namaste {row['Customer']}! Laika Pet Mart se reminder: Aapka ₹{row['Net Udhaar']} baki hai. Please pay kardein."
                    st.markdown(f"[💬 Remind]({urllib.parse.quote(reminder)})")
        
        st.divider(); st.subheader("Recent Entries")
        for i, row in khata_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"📅 {row.iloc[2]} | {row.iloc[0]}: ₹{row.iloc[1]}")
            with col2:
                if st.button("❌", key=f"k_{i}"): delete_row("CustomerKhata", i); st.rerun()

# --- 7. PURCHASE ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); p = st.number_input("Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"📦 *{row.iloc[0]}* - {row.iloc[1]} Pcs @ ₹{row.iloc[3]}")
            with col2:
                if st.button("❌", key=f"i_{i}"): delete_row("Inventory", i); st.rerun()

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        purchased = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum'}).reset_index()
        if not s_df.empty:
            s_df['Sold'] = s_df.iloc[:, 2].str.extract('(\d+)').astype(float)
            sold = s_df.groupby(s_df.columns[1])['Sold'].sum().reset_index()
            stock = pd.merge(purchased, sold, on=i_df.columns[0], how='left').fillna(0)
            stock['Rem'] = stock.iloc[:, 1] - stock.iloc[:, 2]
        else: stock = purchased; stock['Rem'] = stock.iloc[:, 1]
        for _, row in stock.iterrows():
            if row['Rem'] <= 2: st.error(f"📦 *{row.iloc[0]}*: {row['Rem']} bacha hai (LOW!)")
            else: st.info(f"📦 *{row.iloc[0]}*: {row['Rem']} bacha hai")

# --- 9. PET REGISTER (BIRTHDAY BALLOONS) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone"); vax = st.date_input("Vax/Bday")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, "Breed", "Age", "Wt", str(vax)]); time.sleep(1); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        p_df['D'] = pd.to_datetime(p_df.iloc[:, 5], errors='coerce')
        if not p_df[p_df['D'].dt.strftime('%m-%d') == datetime.now().strftime('%m-%d')].empty:
            st.balloons(); st.success("🎉 Special Day Today!")
        for i, row in p_df.iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"🐶 *{row.iloc[0]}* - {row.iloc[5]}")
            with col2: st.markdown(f"[🟢 WA Reminder](https://wa.me/{row.iloc[1]})")
            with col3:
                if st.button("❌", key=f"p_{i}"): delete_row("PetRecords", i); st.rerun()

# --- 10. EXPENSES & ADMIN ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Cat", ["Rent", "Salary", "Bills"]); amt = st.number_input("Amt")
        mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("SAVE"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt, mode]); time.sleep(1); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"💸 {row.iloc[1]}: ₹{row.iloc[2]}")
            with col2:
                if st.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Update", ["Cash", "Online"]); b_a = st.number_input("Amt")
        if st.form_submit_button("SET"):
            save_data("Balances", [b_t, b_a, str(datetime.now().date())]); time.sleep(1); st.rerun()
