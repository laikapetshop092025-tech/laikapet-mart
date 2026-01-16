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
        # Fix for KeyError: Automatic Date detection
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])

if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')

# --- 4. DASHBOARD (COLOURFUL & STABLE) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>🌈 Business Dashboard</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    op_c = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    op_o = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 20px; border-radius: 10px; border-left: 10px solid #D32F2F; width: 32%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{op_c:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 10px solid #1976D2; width: 32%;">
            <p style="color: #1976D2; margin: 0;">🏦 Bank (Online)</p> <h2 style="margin: 0;">₹{op_o:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; border-left: 10px solid #388E3C; width: 32%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Balance</p> <h2 style="margin: 0;">₹{op_c + op_o:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def get_stats(df_s, df_i, df_e, f_type="today"):
        if df_s.empty or 'Date' not in df_s.columns: ts = 0
        else:
            mask = (df_s['Date'].dt.date == today_dt) if f_type == "today" else (df_s['Date'].dt.month == curr_m)
            ts = pd.to_numeric(df_s[mask].iloc[:, 3], errors='coerce').sum()
        if df_i.empty or 'Date' not in df_i.columns: tp = 0
        else:
            mask = (df_i['Date'].dt.date == today_dt) if f_type == "today" else (df_i['Date'].dt.month == curr_m)
            tp = pd.to_numeric(df_i[mask].iloc[:, 1] * df_i[mask].iloc[:, 3], errors='coerce').sum()
        return ts, tp, (ts - tp)

    st.divider()
    ts, tp, tpr = get_stats(s_df, i_df, e_df, "today")
    st.subheader(f"📅 Today Hisaab")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{ts:,.2f}"); c2.metric("Today Purchase", f"₹{tp:,.2f}"); c3.metric("Today Profit", f"₹{tpr:,.2f}")

    if not s_df.empty and 'Date' in s_df.columns:
        st.divider()
        st.subheader("📈 7 Days Sale Trend")
        last_7 = s_df[s_df['Date'] >= pd.to_datetime(today_dt - timedelta(days=7))]
        chart = last_7.groupby(last_7['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index()
        st.plotly_chart(px.line(chart, x='Date', y=s_df.columns[3], markers=True), use_container_width=True)

    st.divider()
    ms, mp, mpr = get_stats(s_df, i_df, e_df, "month")
    st.subheader(f"🗓️ Monthly Stats: {curr_m_name}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Month Sale", f"₹{ms:,.2f}"); m2.metric("Month Purchase", f"₹{mp:,.2f}"); m3.metric("Month Profit", f"₹{mpr:,.2f}")

# --- 5. BILLING (PDF STYLE WA LINK) ---
elif menu == "🧾 Billing":
    st.header("🧾 New Bill")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Qty", 0.1); unit = st.selectbox("Unit", ["Kg", "Pcs", "Packet"])
        with c2: pr = st.number_input("Price", 1.0); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        with c3: c_name = st.text_input("Name"); ph = st.text_input("Phone (91...)")
        if st.form_submit_button("SAVE BILL"):
            pts = int((q * pr) / 100)
            save_data("Sales", [str(today_dt), it, f"{q} {unit}", q*pr, mode, f"{c_name} ({ph})", pts])
            st.success("Bill Saved!"); time.sleep(1); st.rerun()
    s_df = load_data("Sales")
    if not s_df.empty:
        for i, row in s_df.tail(10).iterrows():
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1: st.write(f"*{row.iloc[1]}* | ₹{row.iloc[3]} - {row.iloc[5]}")
            with col2:
                receipt = f"🐾 LAIKA PET MART 🐾\n*Customer:* {row.iloc[5]}\n*Item:* {row.iloc[1]}\n*Qty:* {row.iloc[2]}\n*Total:* ₹{row.iloc[3]}\n*Points:* {row.iloc[6]}\nThank You! ❤️"
                st.markdown(f"[📲 WA Bill](https://wa.me/{ph}?text={urllib.parse.quote(receipt)})")
            with col3:
                if st.button("❌", key=f"s_{i}"): delete_row("Sales", i); st.rerun()

# --- 6. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: on = st.text_input("Owner"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Lab", "GSD", "Pug", "Indie", "Other"])
        with c2: age = st.selectbox("Age", [f"{i} Months" for i in range(1,12)] + [f"{i} Years" for i in range(1,15)]); wt = st.text_input("Weight (kg)"); vax = st.date_input("Vax Date")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, ph, br, age, wt, str(vax)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            col1, col2, col3 = st.columns([5, 3, 1])
            with col1: st.write(f"🐶 *{row.iloc[0]}* ({row.iloc[2]}) | Age: {row.iloc[3]}")
            with col2: st.markdown(f"[🟢 WA Reminder](https://wa.me/{row.iloc[1]})")
            if col3.button("❌", key=f"p_{i}"): delete_row("PetRecords", i); st.rerun()

# --- 7. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Stock Status")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        p_v = i_df.groupby(i_df.columns[0]).agg({i_df.columns[1]: 'sum', i_df.columns[2]: 'last'}).reset_index()
        p_v.columns = ['Item', 'In', 'Unit']
        if not s_df.empty:
            s_df['Out'] = s_df.iloc[:, 2].str.extract('(\d+\.?\d*)').astype(float)
            sold = s_df.groupby(s_df.columns[1])['Out'].sum().reset_index()
            stock = pd.merge(p_v, sold, left_on='Item', right_on=s_df.columns[1], how='left').fillna(0)
            stock['Rem'] = stock['In'] - stock['Out']
        else: stock = p_v; stock['Rem'] = stock['In']
        low = stock[stock['Rem'] <= 2]
        if not low.empty:
            st.error("⚠️ Low Stock Alert!"); st.download_button("📥 Order List", low.to_csv(index=False), "order.csv")
        for _, r in stock.iterrows():
            if r['Rem'] <= 2: st.error(f"📦 {r['Item']}: {r['Rem']} {r['Unit']} left!")
            else: st.info(f"📦 {r['Item']}: {r['Rem']} {r['Unit']} left")

# --- 8. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Miscellaneous", "Other"])
        amt = st.number_input("Amount", 0.0); mode = st.selectbox("Paid From", ["Cash", "Online"])
        if st.form_submit_button("Save"):
            save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.tail(10).iterrows():
            c1, c2 = st.columns([8, 1])
            c1.write(f"💸 {row.iloc[1]}: ₹{row.iloc[2]} ({row.iloc[3]})")
            if c2.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

# --- 9. CUSTOMER KHATA ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("Save"):
            f_amt = amt if "Baki" in t else -amt; save_data("CustomerKhata", [name, f_amt, str(today_dt)]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] != 0: st.warning(f"👤 {row.iloc[0]}: ₹{row.iloc[1]} baki hain")
        st.divider()
        for i, row in k_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"📅 {row.iloc[2]} | {row.iloc[0]}: ₹{row.iloc[1]}")
            if col2.button("❌", key=f"k_{i}"): delete_row("CustomerKhata", i); st.rerun()

# --- 10. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Update", ["Cash", "Online"]); b_a = st.number_input("Amt")
        if st.form_submit_button("Set Balance"):
            save_data("Balances", [b_t, b_a, str(today_dt)]); st.rerun()
    st.divider(); st.subheader("🏢 Supplier Udhaar")
    with st.form("due"):
        comp = st.text_input("Company"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amt")
        if st.form_submit_button("Save"):
            f_amt = amt if "+" in type else -amt; save_data("Dues", [comp, f_amt, str(today_dt)]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        for i, row in d_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"🏢 *{row.iloc[0]}*: ₹{row.iloc[1]}")
            if col2.button("❌", key=f"d_{i}"): delete_row("Dues", i); st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Packet"]); p = st.number_input("Rate")
        if st.form_submit_button("Add"):
            save_data("Inventory", [n, q, u, p, str(today_dt)]); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.tail(10).iterrows():
            col1, col2 = st.columns([8, 1])
            with col1: st.write(f"📦 {row.iloc[0]} - {row.iloc[1]} {row.iloc[2]} @ ₹{row.iloc[3]}")
            if col2.button("❌", key=f"i_{i}"): delete_row("Inventory", i); st.rerun()
