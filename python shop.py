import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & URLS ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Yahan apna Apps Script URL dalein jo aapne Step 1 mein copy kiya tha
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
        return pd.read_csv(SHEET_BASE_URL + sheet_name)
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
        else:
            st.error("Galat Password!")
    st.stop()

# --- 3. SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "💰 Expenses", "📋 Live Stock", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (Expense + Profit Shamil Hai) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    # Profit logic: Sale - Expenses (Aap isme purchase cost bhi jod sakte hain)
    t_profit = t_sale - t_exp 

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")
    
    st.subheader("Recent Sales")
    st.table(s_df.tail(5))

# --- 5. BILLING (Pcs/Kg + Online/Offline) ---
elif menu == "🧾 Billing":
    st.header("🧾 Generate New Bill")
    with st.form("bill_form"):
        it = st.text_input("Product Name")
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Quantity", min_value=0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        with c3: price = st.number_input("Rate", min_value=1)
        mode = st.selectbox("Payment Mode", ["Online", "Offline/Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{qty} {unit}", qty*price, mode])
            st.success("Bill Saved Successfully!")

# --- 6. PURCHASE (Stock Entry) ---
elif menu == "📦 Purchase":
    st.header("📦 Add New Stock")
    with st.form("pur_form"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price", min_value=1)
        if st.form_submit_button("ADD TO INVENTORY"):
            save_data("Inventory", [n, q, u, p])
            st.success(f"{n} added to Stock!")

# --- 7. EXPENSES (Naya: Expenses Section) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Management")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Pet Food/Supplies", "Other"])
        amt = st.number_input("Amount", min_value=1)
        desc = st.text_input("Description (Optional)")
        if st.form_submit_button("SAVE EXPENSE"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt, desc])
            st.success("Expense Recorded!")
    
    st.subheader("Recent Expenses")
    st.table(load_data("Expenses").tail(10))

# --- 8. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Customer & Pet Records")
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Indie", "Other"])
        with c2:
            age = st.text_input("Dog Age"); wt = st.text_input("Dog Weight (Kg)"); vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE PET RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Pet Record Saved!")

# --- 9. ADMIN SETTINGS (Dues + New ID Create) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    
    # Section 1: Udhaar (Dues)
    st.subheader("🏢 Company Udhaar (Dues)")
    with st.expander("Record New Due"):
        comp = st.text_input("Company Name")
        d_amt = st.number_input("Due Amount", min_value=1)
        if st.button("Save Due"):
            save_data("Dues", [comp, d_amt, str(datetime.now().date())])
            st.success("Due Recorded!")
    
    st.table(load_data("Dues"))

    st.divider()

    # Section 2: New ID Create (Naya: Staff Management)
    st.subheader("👤 Staff Management")
    with st.expander("Create New Staff ID"):
        new_user = st.text_input("New Username")
        new_pass = st.text_input("Set Password", type="password")
        role = st.selectbox("Role", ["Staff", "Manager"])
        if st.button("CREATE ID"):
            # Hum ise 'Users' naam ki sheet mein save karenge
            save_data("Users", [new_user, new_pass, role])
            st.success(f"ID Created for {new_user}!")

# --- 10. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_data("Inventory"))
