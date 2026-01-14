import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & URLS ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Google Apps Script URL (Wahi wala paste karein jo aapne banaya tha)
SCRIPT_URL = "AAPKA_WEB_APP_URL_YAHAN_DALEIN" 
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

# Data Save karne ka function
def save_data(sheet_name, data_list):
    try:
        requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return True
    except:
        return False

# Data Load karne ka function
def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_BASE_URL + sheet_name)
        return df
    except:
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.subheader("🔐 LAIKA PET MART LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "💰 Expenses", "📋 Live Stock", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = t_sale - t_exp 

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. BILLING (Live Stock se Item uthayega) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory") # Stock se list uthayega
    sales_df = load_data("Sales")
    
    with st.form("bill_form"):
        # Dropdown mein wahi items aayenge jo Purchase mein dale hain
        items_list = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", items_list)
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Quantity", min_value=0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        with c3: price = st.number_input("Selling Price (Rate)", min_value=1)
        mode = st.selectbox("Payment Mode", ["Online", "Offline/Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{qty} {unit}", qty*price, mode])
            st.success("Bill Saved!")
            st.rerun()
    
    st.subheader("📋 Recent Sales List")
    st.table(sales_df.tail(10)) # Sales ki history niche dikhayega

# --- 6. PURCHASE (Stock Entry + History List) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory")
    
    with st.form("pur_form"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Quantity", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price (Per Unit)", min_value=1)
        if st.form_submit_button("ADD TO STOCK"):
            save_data("Inventory", [n, q, u, p, str(datetime.now().date())])
            st.success(f"{n} added to Inventory!")
            st.rerun()
            
    st.subheader("📋 Purchase History (Stock Entry List)")
    st.table(inv_df.tail(10)) # Kharidari ki list niche dikhayega

# --- 7. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Management")
    e_df = load_data("Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE EXPENSE"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt])
            st.success("Expense Recorded!")
            st.rerun()
    st.table(e_df.tail(10))

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    # Ye Purchase waali sheet ka poora data dikhayega
    st.table(load_data("Inventory"))

# --- 9. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone")
        with c2: br = st.text_input("Breed"); age = st.text_input("Age"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, str(vax)])
            st.success("Saved!"); st.rerun()
    st.table(p_df.tail(10))

# --- 10. ADMIN SETTINGS (Udhaar + New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    
    # Udhaar Section
    st.subheader("🏢 Company Udhaar (Dues)")
    d_df = load_data("Dues")
    comp = st.text_input("Company Name")
    d_amt = st.number_input("Due Amount", min_value=1)
    if st.button("Save Due"):
        save_data("Dues", [comp, d_amt, str(datetime.now().date())])
        st.success("Due Recorded!"); st.rerun()
    st.table(d_df)

    st.divider()

    # New ID Section
    st.subheader("👤 Create New Staff ID")
    new_u = st.text_input("New Username")
    new_p = st.text_input("Set Password", type="password")
    if st.button("CREATE ID"):
        save_data("Users", [new_u, new_p, "Staff"])
        st.success(f"ID Created for {new_u}!")
