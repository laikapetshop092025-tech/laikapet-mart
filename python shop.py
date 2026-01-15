import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import os

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
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
st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>👋 Welcome <br> Laika Pet Mart</h3>", unsafe_allow_html=True)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", use_container_width=True)

menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (CASH & ONLINE LIVE BALANCE) ---
if menu == "📊 Dashboard":
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Real-Time Balance</h2>", unsafe_allow_html=True)
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    b_df = load_data("Balances") # Purana Paisa yahan se aayega

    # 1. Purana (Opening) Balance nikaalna
    op_cash = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    op_online = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0

    # 2. Sales se kitna paisa aaya
    sale_cash = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    sale_online = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0

    # 3. Expenses (Dukan ke kharche minus karna) - filhaal cash se minus karte hain
    total_exp = pd.to_numeric(e_df.iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0

    # Final Current Balance
    curr_cash = (op_cash + sale_cash) - total_exp
    curr_online = op_online + sale_online

    st.markdown("### 💰 Current Money Status")
    col_c, col_o = st.columns(2)
    with col_c: st.success(f"*Galla (Cash in Hand)*\n## ₹{curr_cash:,.2f}")
    with col_o: st.info(f"*Bank (Online Balance)*\n## ₹{curr_online:,.2f}")
    
    st.divider()
    today_str = datetime.now().strftime('%d %B, %Y')
    st.markdown(f"#### 📅 Today's Date: {today_str}")

# --- 5. BILLING (PAYMENT MODE SELECTOR) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Quantity", 0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        with c3: mode = st.selectbox("Payment Received In", ["Cash", "Online"])
        pr = st.number_input("Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, mode])
            time.sleep(1); st.rerun()
    st.table(load_data("Sales").tail(5))

# --- 6. ADMIN SETTINGS (Dukan ka purana Paisa add karo) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin & Opening Balance")
    
    st.subheader("🏁 Set Your Current Cash/Online (Ek baar karein)")
    with st.form("opening_bal"):
        b_type = st.selectbox("Kahan Paisa Add Karna Hai?", ["Cash", "Online"])
        b_amt = st.number_input("Amount Jo Abhi Mere Paas Hai")
        if st.form_submit_button("SET OPENING BALANCE"):
            save_data("Balances", [b_type, b_amt, str(datetime.now().date())])
            st.success(f"{b_type} Balance Updated!"); time.sleep(1); st.rerun()
    
    st.divider()
    st.subheader("🏢 Company Udhaar (Dues)")
    with st.form("due"):
        comp = st.text_input("Company Name")
        amt = st.number_input("Udhaar (+) / Payment (-)")
        if st.form_submit_button("SAVE DUES"):
            save_data("Dues", [comp, amt, str(datetime.now().date())])
            time.sleep(1); st.rerun()

# --- BAAKI CODE (AS IT IS) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1); u = st.selectbox("Unit", ["Pcs", "Kg"]); p = st.number_input("Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, u, p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Inventory").tail(5))

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            t_p = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            t_s = 0
            if not s_df.empty:
                sold_data = s_df[s_df.iloc[:, 1] == item]
                for val in sold_data.iloc[:, 2]:
                    try: t_s += float(str(val).split()[0])
                    except: continue
            stock_list.append({"Product": item, "Available": t_p - t_s, "Unit": i_df[i_df.iloc[:, 0] == item].iloc[:, 2].iloc[-1]})
        st.table(pd.DataFrame(stock_list))

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    cat = st.selectbox("Category", ["Rent", "Salary", "Pet Food", "Other"]); amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(5))

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Persian Cat", "Indie Dog", "Other"]
    with st.form("pet"):
        cn = st.text_input("Customer Name"); ph = st.text_input("Phone"); br = st.selectbox("Breed", breeds)
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, "N/A", "N/A", str(datetime.now().date())]); time.sleep(1); st.rerun()
