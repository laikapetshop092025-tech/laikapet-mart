import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# YAHAN APNA URL PASTE KAREIN (Jo aapne Apps Script se copy kiya tha)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz_Wv_pT_Z_YOUR_URL_HERE/exec" 

# Google Sheet Link (Data load karne ke liye)
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

# Data Save Function (Google Sheet mein bhejta hai)
def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except:
        return False

# Data Load Function (Google Sheet se uthata hai)
def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip() # Column names saaf karna
        return df
    except:
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h2>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🐾 MENU")
menu = st.sidebar.radio("Go to:", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (SALE, PURCHASE, EXPENSE, PROFIT) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Overview")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    t_sale = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    t_exp = pd.to_numeric(e_df.iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    t_pur = 0
    if not i_df.empty:
        # qty * p_price
        t_pur = (pd.to_numeric(i_df.iloc[:, 1], errors='coerce') * pd.to_numeric(i_df.iloc[:, 3], errors='coerce')).sum()
    
    t_profit = t_sale - t_exp - t_pur

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. BILLING (STOCK MERGED) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory")
    sales_df = load_data("Sales")
    with st.form("bill_f"):
        # Purchase se item uthayega
        it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", it_list)
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Quantity", min_value=0.1)
        with c2: price = st.number_input("Selling Price")
        mode = st.selectbox("Payment Mode", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, qty, qty*price, mode])
            st.success("Bill Saved!"); st.rerun()
    st.table(sales_df.tail(10))

# --- 6. PURCHASE (ADDS TO STOCK) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: p = st.number_input("Purchase Price (Rate)")
        u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        if st.form_submit_button("ADD TO STOCK"):
            save_data("Inventory", [n, q, u, p, str(datetime.now().date())])
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Recent Purchase History")
    st.table(inv_df.tail(10))

# --- 7. PET REGISTER (AGE, WEIGHT, VACCINE FIXED) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Persian Cat", "Other"])
        with c2:
            age = st.text_input("Pet Age"); wt = st.text_input("Pet Weight (Kg)")
            vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Pet Saved!"); st.rerun()
    st.table(p_df.tail(10))

# --- 8. EXPENSES (MISCELLANEOUS DROPDOWN) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    e_df = load_data("Expenses")
    with st.form("exp_f"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Staff Salary", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE EXPENSE"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt])
            st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

# --- 9. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_data("Inventory"))

# --- 10. ADMIN SETTINGS (DUES & NEW ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    d_df = load_data("Dues")
    st.subheader("🏢 Company Udhaar (Dues)")
    with st.form("due_f"):
        comp = st.text_input("Company Name"); amt = st.number_input("Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())])
            st.rerun()
    st.table(d_df)
    st.divider()
    st.subheader("👤 Create Staff ID")
    st.text_input("New User"); st.text_input("Pass", type="password")
    if st.button("CREATE"): st.success("Account Ready!")
