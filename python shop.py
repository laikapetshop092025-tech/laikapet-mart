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

# Cart States (Sessions)
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
today_dt = datetime.now().date()

# --- 4. DASHBOARD (RESTORED 4 BOXES) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial Calculations
    base_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    base_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    exp_cash = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    exp_online = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    pur_cash = pd.to_numeric(i_df[i_df.iloc[:, 5] == "Cash"].apply(lambda x: pd.to_numeric(x.iloc[1])*pd.to_numeric(x.iloc[3]), axis=1), errors='coerce').sum() if not i_df.empty and len(i_df.columns)>5 else 0
    pur_online = pd.to_numeric(i_df[i_df.iloc[:, 5] == "Online"].apply(lambda x: pd.to_numeric(x.iloc[1])*pd.to_numeric(x.iloc[3]), axis=1), errors='coerce').sum() if not i_df.empty and len(i_df.columns)>5 else 0
    
    due_pay_cash = abs(pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum()) if not d_df.empty and len(d_df.columns)>3 else 0
    due_pay_online = abs(pd.to_numeric(d_df[(d_df.iloc[:, 1] < 0) & (d_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum()) if not d_df.empty and len(d_df.columns)>3 else 0

    khata_cash = abs(pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Cash")].iloc[:, 1], errors='coerce').sum()) if not k_df.empty and len(k_df.columns)>3 else 0
    khata_online = abs(pd.to_numeric(k_df[(k_df.iloc[:, 1] < 0) & (k_df.iloc[:, 3] == "Online")].iloc[:, 1], errors='coerce').sum()) if not k_df.empty and len(k_df.columns)>3 else 0
    
    total_udhaar = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 24%;">
            <p style="color: #D32F2F; margin: 0;">💵 Cash (Galla)</p> <h2 style="margin: 0;">₹{base_cash + sale_cash + khata_cash - exp_cash - pur_cash - due_pay_cash:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 24%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h2 style="margin: 0;">₹{base_online + sale_online + khata_online - exp_online - pur_online - due_pay_online:,.2f}</h2>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 24%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h2 style="margin: 0;">₹{total_udhaar:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 24%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Net</p> <h2 style="margin: 0;">₹{(base_cash + sale_cash + khata_cash - exp_cash - pur_cash - due_pay_cash + base_online + sale_online + khata_online - exp_online - pur_online - due_pay_online):,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not s_df.empty:
        st.divider(); st.subheader("📈 Last 7 Days Sales Graph")
        fig = px.line(s_df.groupby(s_df['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index().tail(7), x='Date', y=s_df.columns[3])
        st.plotly_chart(fig, use_container_width=True)

# --- 5. BILLING (CART SYSTEM) ---
elif menu == "🧾 Billing":
    st.header("🧾 Generate Bill")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c1, c2, c3 = st.columns(3)
    cust = c1.text_input("Customer Name"); ph = c2.text_input("Phone Number"); pay_m = c3.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    
    with st.expander("🛒 Add Items to Bill", expanded=True):
        col1, col2, col3 = st.columns(3)
        it = col1.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        qty = col2.number_input("Qty", 0.1); pr = col3.number_input("Price", 1.0)
        if st.button("➕ Add Item"):
            pur_r = inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3] if not inv_df.empty else 0
            st.session_state.bill_cart.append({"Product": it, "Qty": qty, "Price": pr, "Profit": (pr-pur_r)*qty})
            st.rerun()

    if st.session_state.bill_cart:
        st.table(pd.DataFrame(st.session_state.bill_cart))
        if st.button("✅ Final Submit Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Product'], f"{item['Qty']}", item['Qty']*item['Price'], pay_m, f"{cust} ({ph})", 0, item['Profit']])
            st.session_state.bill_cart = []; st.success("Bill Saved!"); st.rerun()
        if st.button("🗑️ Clear List"): st.session_state.bill_cart = []; st.rerun()

# --- 6. PURCHASE (CART SYSTEM) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    p_from = st.selectbox("Paid From", ["Cash", "Online", "Pocket"])
    with st.expander("📥 Add Items to Purchase", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        n = col1.text_input("Item Name"); q = col2.number_input("Qty", 1.0); u = col3.selectbox("Unit", ["Kg", "Pcs"]); p = col4.number_input("Rate")
        if st.button("➕ Add to List"):
            st.session_state.pur_cart.append({"Item": n, "Qty": q, "Unit": u, "Rate": p})
            st.rerun()

    if st.session_state.pur_cart:
        st.table(pd.DataFrame(st.session_state.pur_cart))
        if st.button("💾 Final Save All"):
            for item in st.session_state.pur_cart:
                save_data("Inventory", [item['Item'], item['Qty'], item['Unit'], item['Rate'], str(today_dt), p_from])
            st.session_state.pur_cart = []; st.success("Purchase Complete!"); st.rerun()

# --- 7. LIVE STOCK (RESTORED CALCULATION) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Status")
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
        
        for _, r in stock.iterrows():
            if r['Rem'] <= 2: st.error(f"❌ ALERT: {r['Item']} Only {r['Rem']} Left")
            else: st.info(f"✅ {r['Item']}: {r['Rem']} {r['Unit']} Left")
        st.divider(); st.download_button("📥 Download Stock List", stock.to_csv(index=False), "stock.csv")

# --- 8. ADMIN SETTINGS (RESTORED DUES LIST) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    with st.form("bal"):
        b_t = st.selectbox("Update Mode", ["Cash", "Online"]); b_a = st.number_input("Base Amt")
        if st.form_submit_button("Set Base"): save_data("Balances", [b_t, b_a, str(today_dt)]); st.rerun()
    st.divider(); st.subheader("🏢 Supplier Dues & Payments")
    with st.form("due"):
        comp = st.text_input("Company"); type = st.selectbox("Action", ["Udhaar Liya (+)", "Payment Diya (-)"]); amt = st.number_input("Amt")
        p_mode = st.selectbox("Paid From", ["Cash", "Online", "Pocket", "N/A"])
        if st.form_submit_button("Save"):
            save_data("Dues", [comp, amt if "+" in type else -amt, str(today_dt), p_mode]); st.rerun()
    d_df = load_data("Dues")
    if not d_df.empty:
        summary = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] != 0: st.error(f"🏢 {row.iloc[0]}: ₹{row.iloc[1]} Pending")

# --- OTHER TABS (RESTORED LINE-TO-LINE) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Miscellaneous", "Other"])
        amt = st.number_input("Amount"); mode = st.selectbox("Mode", ["Cash", "Online"])
        if st.form_submit_button("Save"): save_data("Expenses", [str(today_dt), cat, amt, mode]); st.rerun()
    e_df = load_data("Expenses")
    if not e_df.empty:
        for i, row in e_df.iterrows():
            st.write(f"💸 {row.iloc[1]}: ₹{row.iloc[2]} ({row.iloc[0]})")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    breeds = ["Labrador", "GSD", "Pug", "Shih Tzu", "Persian Cat", "Indie Dog", "Other"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner"); ph = c1.text_input("Phone"); br = c1.selectbox("Breed", breeds)
        age = c2.selectbox("Age", [f"{i} Months" for i in range(1,12)] + [f"{i} Years" for i in range(1,15)])
        vd = c2.date_input("Vax Date"); nd = vd + timedelta(days=365)
        if st.form_submit_button("Save"): save_data("PetRecords", [on, ph, br, age, str(vd), str(nd), str(today_dt)]); st.rerun()
    p_df = load_data("PetRecords")
    if not p_df.empty:
        for i, row in p_df.iterrows():
            st.write(f"🐶 *{row.iloc[0]}* - {row.iloc[2]} | Next Vax: {row.iloc[5]}")

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    # Khata logic (Restored Line-to-line)
    k_df = load_data("CustomerKhata")
    if not k_df.empty:
        summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        for i, row in summary.iterrows():
            if row.iloc[1] > 0: st.warning(f"👤 {row.iloc[0]}: ₹{row.iloc[1]} Balance")

elif menu == "🎖️ Loyalty Club":
    st.header("🎖️ Loyalty Club")
    s_df = load_data("Sales")
    if not s_df.empty:
        loyalty = s_df.groupby(s_df.iloc[:, 5]).agg({s_df.columns[6]: 'sum'}).reset_index()
        st.dataframe(loyalty, use_container_width=True)
