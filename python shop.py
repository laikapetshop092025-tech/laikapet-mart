import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse
import plotly.express as px

# --- 1. SETUP & CONNECTION (Unchanged) ---
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
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, -1], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password", key="login_pass").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR (LOGOUT RESTORED) ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])

st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# --- 4. DASHBOARD (WELCOME MESSAGE & ALL STATS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>Hisaab-Kitaab Dashboard</h4>", unsafe_allow_html=True)
    
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    
    base_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    base_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    exp_cash = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    exp_online = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 20px; border-radius: 10px; border-left: 10px solid #D32F2F; width: 32%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{base_cash + sale_cash - exp_cash:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 10px solid #1976D2; width: 32%;">
            <p style="color: #1976D2; margin: 0;">🏦 Bank (Online)</p> <h2 style="margin: 0;">₹{base_online + sale_online - exp_online:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 20px; border-radius: 10px; border-left: 10px solid #388E3C; width: 32%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Balance</p> <h2 style="margin: 0;">₹{base_cash + sale_cash - exp_cash + base_online + sale_online - exp_online:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def get_stats(df_s, df_i, df_e, f_type="today"):
        m_s = (df_s['Date'].dt.date == today_dt) if (not df_s.empty and f_type == "today") else (df_s['Date'].dt.month == datetime.now().month if not df_s.empty else False)
        m_i = (df_i['Date'].dt.date == today_dt) if (not df_i.empty and f_type == "today") else (df_i['Date'].dt.month == datetime.now().month if not df_i.empty else False)
        m_e = (df_e['Date'].dt.date == today_dt) if (not df_e.empty and f_type == "today") else (df_e['Date'].dt.month == datetime.now().month if not df_e.empty else False)
        ts = pd.to_numeric(df_s[m_s].iloc[:, 3], errors='coerce').sum() if not df_s.empty else 0
        tp = pd.to_numeric(df_i[m_i].iloc[:, 1] * df_i[m_i].iloc[:, 3], errors='coerce').sum() if not df_i.empty else 0
        te = pd.to_numeric(df_e[m_e].iloc[:, 2], errors='coerce').sum() if not df_e.empty else 0
        tpr = pd.to_numeric(df_s[m_s].iloc[:, 7], errors='coerce').sum() if (not df_s.empty and len(df_s.columns) > 7) else 0
        return ts, tp, te, tpr

    ts, tp, te, tpr = get_stats(s_df, i_df, e_df, "today")
    st.divider(); st.subheader(f"📅 Today's Report ({today_dt})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{ts}"); c2.metric("Purchase", f"₹{tp}"); c3.metric("Expense", f"₹{te}"); c4.metric("Profit", f"₹{tpr}")

    ms, mp, me, mpr = get_stats(s_df, i_df, e_df, "month")
    st.divider(); st.subheader(f"🗓️ Monthly Report ({curr_m_name})")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sale", f"₹{ms}"); m2.metric("Purchase", f"₹{mp}"); m3.metric("Expense", f"₹{me}"); m4.metric("Profit", f"₹{mpr}")

    if not s_df.empty:
        st.divider(); st.subheader("📈 Weekly Sales Analysis")
        fig = px.line(s_df.groupby(s_df['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index(), x='Date', y=s_df.columns[3])
        st.plotly_chart(fig, use_container_width=True)

# --- 5. BILLING (WHATSAPP FEATURE RESTORED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Generate Bill")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        pur_rate = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Qty", 0.1); unit = st.selectbox("Unit", ["Kg", "Pcs", "Packet"])
        with c2: pr = st.number_input("Selling Price", 1.0); mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        with c3: ph = st.text_input("Customer Phone")
        pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].str.contains(ph, na=False)].iloc[:, 6], errors='coerce').sum() if (ph and not s_df.empty) else 0
        st.write(f"🌟 Available Points: *{pts_bal}*")
        redeem = st.checkbox(f"Redeem {pts_bal} Points?")
        is_ref = st.checkbox("Referral Bonus (+10 Points)")
        
        if st.form_submit_button("SAVE BILL"):
            total = q * pr; profit = (pr - pur_rate) * q
            pts_add = int((total/100) * (5 if is_weekend else 2))
            if is_ref: pts_add += 10
            if redeem: pts_add = -pts_bal
            if save_data("Sales", [str(today_dt), it, f"{q} {unit}", total, mode, ph, pts_add, profit]):
                st.success("Bill Saved!")
                # WhatsApp Link Generation
                msg = f"🐾 LAIKA PET MART 🐾\nNamaste! Dhanyavad shopping ke liye.\nItem: {it}\nTotal: ₹{total}\nPoints Added: {pts_add}\nVisit Again! ❤️"
                wa_url = f"https://wa.me/91{ph}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📲 Send WhatsApp Bill to Customer]({wa_url})")
                time.sleep(2); st.rerun()

# --- 6. LIVE STOCK (DOWNLOAD BUTTON RESTORED) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
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
            st.error("⚠️ Low Stock Alert!")
            st.download_button("📥 Download Order List", low.to_csv(index=False), "order.csv")
        for _, r in stock.iterrows():
            if r['Rem'] <= 2: st.error(f"📦 {r['Item']}: {r['Rem']} {r['Unit']} Left")
            else: st.info(f"✅ {r['Item']}: {r['Rem']} {r['Unit']} Left")

# --- 7. PET REGISTER (DROP-DOWNS RESTORED) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: on = st.text_input("Owner"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Lab", "GSD", "Pug", "Other"])
        with c2: age = st.selectbox("Age", [f"{i} Months" for i in range(1,12)] + [f"{i} Years" for i in range(1,15)]); wt = st.text_input("Weight")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [on, ph, br, age, wt, str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"🐶 *{row.iloc[0]}* - {row.iloc[2]}")
            if c2.button("❌", key=f"pr_{i}"): delete_row("PetRecords", i); st.rerun()

# --- 8. CUSTOMER KHATA (MINUS LOGIC) ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        name = st.text_input("Name"); amt = st.number_input("Amount"); t = st.selectbox("Type", ["Baki (Udhaar)", "Jama (Payment)"])
        if st.form_submit_button("Save"):
            f_amt = -amt if "Jama" in t else amt
            save_data("CustomerKhata", [name, f_amt, str(today_dt)]); st.rerun()
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] > 0: st.warning(f"👤 {row.iloc[0]}: ₹{row.iloc[1]} Baki")
            elif row.iloc[1] < 0: st.success(f"👤 {row.iloc[0]}: ₹{abs(row.iloc[1])} Advance")

# --- PURANA LISTS (PURCHASE, EXPENSE, LOYALTY, ADMIN) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs"]); p = st.number_input("Rate")
        if st.form_submit_button("Add"): save_data("Inventory", [n, q, u, p, str(today_dt)]); st.rerun()
    i_df = load_data("Inventory")
    if not i_df.empty:
        for i, row in i_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"📦 {row.iloc[0]} - {row.iloc[1]} {row.iloc[2]} @ ₹{row.iloc[3]}")
            if c2.button("❌", key=f"i_{i}"): delete_row("Inventory", i); st.rerun()

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Other"])
        amt = st.number_input("Amount"); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.iterrows():
            c1, c2 = st.columns([8, 1]); c1.write(f"💸 {row.iloc[1]}: ₹{row.iloc[2]} ({row.iloc[3]})")
            if c2.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

elif menu == "🎖️ Loyalty Club":
    st.header("🎖️ Loyalty Club")
    s_df = load_data("Sales")
    if not s_df.empty:
        loyalty = s_df.groupby(s_df.iloc[:, 5]).agg({s_df.columns[6]: 'sum'}).reset_index()
        st.dataframe(loyalty[loyalty.iloc[:, 1] > 0], use_container_width=True)

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Mode", ["Cash", "Online"]); b_a = st.number_input("Amount")
        if st.form_submit_button("Set Base"): save_data("Balances", [b_t, b_a, str(today_dt)]); st.rerun()
    st.divider(); st.subheader("🏢 Supplier Dues")
    with st.form("due"):
        comp = st.text_input("Company"); type = st.selectbox("Type", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amt")
        if st.form_submit_button("Save Due"):
            f_amt = amt if "+" in type else -amt; save_data("Dues", [comp, f_amt, str(today_dt)]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows(): st.error(f"🏢 {row.iloc[0]}: ₹{row.iloc[1]} Pending")
