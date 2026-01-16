[1:30 pm, 16/1/2026] Laika pet Shop: import streamlit as st
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
        r…
[1:36 pm, 16/1/2026] Laika pet Shop: import streamlit as st
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
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "🎖️ Loyalty Club", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "⚙️ Admin Settings"])

st.sidebar.divider()
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()

# --- 4. DASHBOARD (AS REQUESTED) ---
if menu == "📊 Dashboard":
    st.header("📈 Dashboard")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); i_df = load_data("Inventory")
    curr_m = datetime.now().month
    
    # Balances
    c_bal = pd.to_numeric(b_df[b_df.iloc[:,0]=="Cash"].iloc[:,1], errors='coerce').sum() if not b_df.empty else 0
    o_bal = pd.to_numeric(b_df[b_df.iloc[:,0]=="Online"].iloc[:,1], errors='coerce').sum() if not b_df.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Cash Balance", f"₹{c_bal:,.2f}")
    col2.metric("Online Balance", f"₹{o_bal:,.2f}")

    if not s_df.empty:
        st.subheader("7 Days Sale Trend")
        last_7 = s_df[s_df['Date'] >= pd.to_datetime(today_dt - timedelta(days=7))]
        chart = last_7.groupby(last_7['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index()
        st.plotly_chart(px.line(chart, x='Date', y=s_df.columns[3]), use_container_width=True)

    st.subheader(f"Monthly Stats ({datetime.now().strftime('%B')})")
    m_sale = s_df[s_df['Date'].dt.month == curr_m].iloc[:,3].sum() if not s_df.empty else 0
    st.metric("Total Monthly Sale", f"₹{m_sale:,.2f}")

# --- 5. BILLING (WITH AUTO POINTS) ---
elif menu == "🧾 Billing":
    st.header("🧾 New Bill")
    inv_df = load_data("Inventory")
    with st.form("bill_form"):
        prod = st.selectbox("Product", inv_df.iloc[:,0].unique() if not inv_df.empty else ["No Stock"])
        amt = st.number_input("Amount", 1)
        ph = st.text_input("Customer Phone")
        mode = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
        if st.form_submit_button("Save Bill"):
            points = int(amt / 100)
            save_data("Sales", [str(today_dt), prod, "1 Pcs", amt, mode, ph, points])
            st.success(f"Bill Saved! {points} Points added.")
            time.sleep(1); st.rerun()

# --- 6. LOYALTY CLUB (NEW TAB) ---
elif menu == "🎖️ Loyalty Club":
    st.header("🎖️ Customer Loyalty Points")
    s_df = load_data("Sales")
    search_ph = st.text_input("Enter Customer Phone to check Points")
    if search_ph:
        cust_sales = s_df[s_df.iloc[:, 5].astype(str) == search_ph]
        total_pts = pd.to_numeric(cust_sales.iloc[:, 6], errors='coerce').sum()
        st.info(f"Customer {search_ph} ke paas total *{total_pts} Points* hain.")
        
        st.divider()
        st.subheader("Redeem Points")
        r_amt = st.number_input("Points to Redeem", 1)
        if st.button("Redeem Now"):
            save_data("Sales", [str(today_dt), "Points Redeemed", "0", 0, "Redeem", search_ph, -r_amt])
            st.success("Points Redeemed Successfully!")
            time.sleep(1); st.rerun()

# --- 7. EXPENSES (RESTORED LIST) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.text_input("Category")
        amt = st.number_input("Amount")
        mode = st.selectbox("Paid Via", ["Cash", "Online"])
        if st.form_submit_button("Save Expense"):
            save_data("Expenses", [str(today_dt), cat, amt, mode])
            st.rerun()
    
    e_df = load_data("Expenses")
    if not e_df.empty:
        st.subheader("Expense History")
        for i, row in e_df.tail(10).iterrows():
            c1, c2 = st.columns([8, 1])
            c1.write(f"💸 {row.iloc[1]} - ₹{row.iloc[2]}")
            if c2.button("❌", key=f"e_{i}"): delete_row("Expenses", i); st.rerun()

# --- 8. PET REGISTER (DROPDOWN + FULL DETAILS) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        name = st.text_input("Owner Name")
        breed = st.selectbox("Breed", ["Labrador", "GSD", "Pug", "Indie", "Other"])
        age = st.selectbox("Age", [f"{i} Months" for i in range(1,12)] + [f"{i} Years" for i in range(1,15)])
        wt = st.text_input("Weight")
        if st.form_submit_button("Save Pet"):
            save_data("PetRecords", [name, "Phone", breed, age, wt, str(today_dt)])
            st.rerun()

# --- 9. LIVE STOCK (DOWNLOAD BUTTON) ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.dataframe(i_df)
        csv = i_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Stock List", csv, "stock.csv", "text/csv")

# --- OTHER SECTIONS (KEPT AS IS) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    # ... (Purana Purchase Code)

elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    # ... (Purana Khata Code)

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("Supplier/Company Udhaar")
    # ... (Purana Admin Dues Code)
