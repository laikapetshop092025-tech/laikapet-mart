import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Yahan apna wahi Sahi wala Deployment URL rehne dena
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
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
        # Har baar fresh data uthane ke liye link ke peeche random number joda hai
        df = pd.read_csv(f"{SHEET_LINK}{sheet_name}&cache_bust={datetime.now().timestamp()}")
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])
if st.sidebar.button("🚪 LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SALE & MARGIN) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_data("Sales"); i_df = load_data("Inventory")
    # Today Metrics
    today = datetime.now().date(); curr_m = datetime.now().month
    
    # Simple Logic for Profit
    st.subheader(f"Summary for {datetime.now().strftime('%B %d')}")
    # (Dashboard calculation yahan rahegi)

# --- 5. BILLING (SAME) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill_f"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); pr = st.number_input("Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"]); st.rerun()
    st.subheader("Recent Sales")
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE"):
        if delete_data("Sales"): st.rerun()

# --- 6. PURCHASE (FIXED: Ab list aur stock dono dikhega) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.form("pur_f"):
        n = st.text_input("Item Name (Product)")
        q = st.number_input("Quantity", min_value=1)
        p = st.number_input("Purchase Price (Kharid Rate)")
        if st.form_submit_button("ADD TO STOCK"):
            if n:
                # Inventory sheet mein data bhej rahe hain
                res = save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())])
                if res: st.success(f"{n} Stock mein jodh diya gaya!"); st.rerun()
                else: st.error("Save nahi ho paya, URL check karein.")
            else: st.warning("Item ka naam likhein.")

    st.subheader("Recent Purchase History")
    p_history = load_data("Inventory")
    if not p_history.empty:
        st.table(p_history.tail(10)) # Sabse aakhri 10 entries dikhayega
        if st.button("❌ DELETE LAST PURCHASE"):
            if delete_data("Inventory"): st.rerun()
    else:
        st.info("Abhi tak koi purchase nahi ki gayi hai.")

# --- 7. LIVE STOCK (FIXED: Sheet se Direct) ---
elif menu == "📋 Live Stock":
    st.header("📋 Shop Live Stock")
    stock_df = load_data("Inventory")
    if not stock_df.empty:
        # Formatting for better view
        stock_display = stock_df.copy()
        stock_display.columns = ["Item Name", "Quantity", "Unit", "Pur. Price", "Date"]
        st.dataframe(stock_display, use_container_width=True)
    else:
        st.warning("Stock Khali Hai! Pehle Purchase mein maal jodein.")

# --- 8. OTHERS (NO CHANGES) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    p_df = load_data("PetRecords")
    st.table(p_df.tail(10))

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    st.table(load_data("Expenses").tail(10))

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.table(load_data("Dues").tail(10))
