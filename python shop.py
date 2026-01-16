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

# --- 4. DASHBOARD (AS IS) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    today_dt = datetime.now().date(); curr_m = datetime.now().month; curr_m_name = datetime.now().strftime('%B')

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

    def get_stats(df_s, df_i, df_e, f_type="today"):
        m_s = (df_s['Date'].dt.date == today_dt) if f_type == "today" else (df_s['Date'].dt.month == curr_m)
        m_i = (df_i['Date'].dt.date == today_dt) if f_type == "today" else (df_i['Date'].dt.month == curr_m)
        m_e = (df_e['Date'].dt.date == today_dt) if f_type == "today" else (df_e['Date'].dt.month == curr_m)
        ts = pd.to_numeric(df_s[m_s].iloc[:, 3], errors='coerce').sum() if not df_s.empty else 0
        tp = pd.to_numeric(df_i[m_i].iloc[:, 1] * df_i[m_i].iloc[:, 3], errors='coerce').sum() if not df_i.empty else 0
        te = pd.to_numeric(df_e[m_e].iloc[:, 2], errors='coerce').sum() if not df_e.empty else 0
        return ts, tp, te, (ts - tp)

    st.divider()
    ts, tp, te, tpr = get_stats(s_df, i_df, e_df, "today")
    st.markdown(f"#### 📅 Today: {today_dt.strftime('%d %B')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{ts:,.2f}"); c2.metric("Purchase", f"₹{tp:,.2f}"); c3.metric("Expense", f"₹{te:,.2f}"); c4.metric("Profit", f"₹{tpr:,.2f}")

    if not s_df.empty:
        st.divider(); st.markdown("#### 📈 Weekly Trend")
        last_7 = s_df[s_df['Date'] >= pd.to_datetime(today_dt - timedelta(days=7))]
        chart_data = last_7.groupby(last_7['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index()
        fig = px.line(chart_data, x='Date', y=s_df.columns[3], markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    ms, mp, me, mpr = get_stats(s_df, i_df, e_df, "month")
    st.markdown(f"#### 🗓️ Month: {curr_m_name}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sale", f"₹{ms:,.2f}"); m2.metric("Purchase", f"₹{mp:,.2f}"); m3.metric("Expense", f"₹{me:,.2f}"); m4.metric("Profit", f"₹{mpr:,.2f}")

# --- 5. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Loyalty")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Qty", 0.1); unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c2: pr = st.number_input("Price"); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        with c3: ph = st.text_input("Customer Phone")
        if st.form_submit_button("SAVE BILL"):
            pts = int((q * pr) / 100)
            save_data("Sales", [str(today_dt), it, f"{q} {unit}", q*pr, mode, ph, pts]); time.sleep(1); st.rerun()
    s_df = load_data("Sales")
    if not s_df.empty:
        for i, row in s_df.tail(10).iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"*{row.iloc[1]}* | ₹{row.iloc[3]} ({row.iloc[4]})")
            with col2:
                msg = f"🐾 LAIKA PET MART\nBill: ₹{row.iloc[3]}\nPoints: {row.iloc[6]}"
                st.markdown(f"[📲 Bill](https://wa.me/{row.iloc[5]}?text={urllib.parse.quote(msg)})")
            with col3:
                if st.button("❌", key=f"s_{i}"): delete_row("Sales", i); st.rerun()

# --- 6. PET REGISTER (DROPDOWNS ADDED) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: 
            cn = st.text_input("Owner Name"); ph = st.text_input("Phone")
            br = st.selectbox("Breed", ["Labrador", "GSD", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Indie", "Other"])
        with c2: 
            age = st.selectbox("Age", [f"{i} Months" for i in range(1, 12)] + [f"{i} Years" for i in range(1, 15)])
            wt = st.text_input("Weight (kg)"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            col1, col2, col3 = st.columns([5, 3, 1])
            with col1: st.write(f"🐶 *{row.iloc[0]}* ({row.iloc[2]}) | Age: {row.iloc[3]} | Wt: {row.iloc[4]}")
            with col2: st.markdown(f"[🟢 WA](https://wa.me/{row.iloc[1]})")
            with col3:
                if st.button("❌", key=f"p_{i}"): delete_row("PetRecords", i); st.rerun()

# --- 7. EXPENSES (LIST RESTORED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Miscellaneous", "Other"])
        amt = st.number_input("Amount", 0.0); mode = st.selectbox("Paid From", ["Cash", "Online"])
        if st.form_submit_button("Save Expense"):
            save_data("Expenses", [str(today_dt), cat, amt, mode]); time.sleep(1); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        st.subheader("Expense History")
        for i, row in e_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"💸 *{row.iloc[1]}*: ₹{row.iloc[2]} ({row.iloc[3]})")
            with col2:
                if st.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

# --- 8. LIVE STOCK (DOWNLOAD BUTTON RESTORED) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Status")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        purchased = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[2]: 'last'}).reset_index()
        purchased.columns = ['Item', 'Qty_In', 'Unit']
        if not s_df.empty:
            s_df['Sold'] = s_df.iloc[:, 2].str.extract('(\d+\.?\d*)').astype(float)
            sold = s_df.groupby(s_df.columns[1])['Sold'].sum().reset_index()
            sold.columns = ['Item', 'Qty_Out']
            stock = pd.merge(purchased, sold, on='Item', how='left').fillna(0)
            stock['Rem'] = stock['Qty_In'] - stock['Qty_Out']
        else: stock = purchased; stock['Rem'] = stock['Qty_In']
        
        low_stock = stock[stock['Rem'] <= 2]
        if not low_stock.empty:
            order_list = "Order List:\n" + "\n".join([f"- {r['Item']}" for _, r in low_stock.iterrows()])
            st.download_button("📥 Download Order List", order_list, file_name="order.txt")

        for _, row in stock.iterrows():
            if row['Rem'] <= 2: st.error(f"📦 *{row['Item']}*: {row['Rem']} {row['Unit']} (STOCK LOW!)")
            else: st.info(f"📦 *{row['Item']}*: {row['Rem']} {row['Unit']} bacha hai")

# --- 9. PURCHASE / CUSTOMER KHATA / ADMIN (AS IS) ---
elif menu == "📦 Purchase":
    st.header("📦 Add Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Pcs", "Kg"])
        with c2: p = st.number_input("Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, u, p, str(today_dt)]); time.sleep(1); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"📦 *{row.iloc[0]}* - {row.iloc[1]} {row.iloc[2]} @ ₹{row.iloc[3]}")
            with col2:
                if st.button("❌", key=f"i_{i}"): delete_row("Inventory", i); st.rerun()

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Udhaar Diary")
    with st.form("k"):
        name = st.text_input("Customer Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("SAVE"):
            f_amt = amt if "Baki" in t else -amt
            save_data("CustomerKhata", [name, f_amt, str(today_dt)]); time.sleep(1); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] != 0: st.warning(f"👤 *{row.iloc[0]}*: ₹{row.iloc[1]} baki hain")

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_type = st.selectbox("Update Balance", ["Cash", "Online"]); b_amt = st.number_input("Amt")
        if st.form_submit_button("SET"):
            save_data("Balances", [b_type, b_amt, str(today_dt)]); time.sleep(1); st.rerun()
    st.divider()
    st.subheader("Company Udhaar (Dues)")
    with st.form("due"):
        comp = st.text_input("Company Name"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amt")
        if st.form_submit_button("SAVE DUES"):
            f_amt = amt if "+" in type else -amt
            save_data("Dues", [comp, f_amt, str(today_dt)]); time.sleep(1); st.rerun()
