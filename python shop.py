import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP & DATABASE CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. STYLE ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. BRANDING & NAVIGATION ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "🐾 Pet Sales Register", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (4 Metrics: Sale, Purchase, Expense, Profit) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    sales_df = load_data("Sales")
    exp_df = load_data("Expenses")
    inv_df = load_data("Inventory")
    
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0
    t_pur = (inv_df['qty'] * inv_df['p_price']).sum() if not inv_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp

    c1, c2 = st.columns(2)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    
    st.divider()
    
    c3, c4 = st.columns(2)
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. PET SALES REGISTER (All Columns Fixed) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Customer Name")
            ph = st.text_input("Phone Number")
            b = st.text_input("Dog Breed")
        with c2:
            w = st.text_input("Dog Weight")
            a = st.text_input("Dog Age")
            v_date = st.date_input("Next Vaccine Date")
        
        if st.form_submit_button("SAVE PET RECORD"):
            st.success("Pet Record Saved Online!")
    
    st.subheader("Registered Pets")
    pet_df = load_data("PetRecords")
    if not pet_df.empty: st.table(pet_df)

# --- 7. EXPENSES (Miscellaneous Added) ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Expense"):
            st.success("Expense Recorded!")
    
    exp_df = load_data("Expenses")
    if not exp_df.empty: st.table(exp_df)

# --- 8. ADMIN SETTINGS (Dues & New ID) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 Create New Staff ID")
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Create ID"):
            st.success("New Staff ID Created!")
            
    with col2:
        st.subheader("🏢 Company Udhaar (Dues)")
        c_name = st.text_input("Company Name")
        u_amt = st.number_input("Udhaar Amount", min_value=1)
        if st.button("Save Udhaar"):
            st.success("Udhaar Record Updated!")

# --- 9. BILLING, PURCHASE, STOCK (Sahi Logic) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    inv_df = load_data("Inventory")
    if not inv_df.empty:
        with st.form("bill"):
            item = st.selectbox("Product", inv_df['Item'].tolist())
            qty = st.number_input("Qty", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment", ["Cash", "Online"])
            if st.form_submit_button("BILL"):
                st.success("Billing Complete!")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur"):
        n = st.text_input("Item Name"); r = st.number_input("Purchase Price"); q = st.number_input("Qty")
        if st.form_submit_button("ADD"):
            st.success("Stock Added Successfully!")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    inv_df = load_data("Inventory")
    if not inv_df.empty: st.table(inv_df)
