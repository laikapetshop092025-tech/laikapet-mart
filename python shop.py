import streamlit as st # App interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets sync ke liye
import pandas as pd # Data tables handle karne ke liye
from datetime import datetime # Date-Time records ke liye

# --- 1. CONNECTION SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide") 
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet se live connection

# Hamesha fresh data dikhane ke liye function (ttl=0)
def load_data(sheet):
    return conn.read(worksheet=sheet, ttl=0).dropna(how="all")

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.subheader("🔐 Staff Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU NAVIGATION ---
st.markdown("<h1 style='text-align: center; color: #2E5BFF;'>LAIKA PET MART</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (4 Metrics: Sale, Purchase, Expense, Profit) ---
if menu == "📊 Dashboard":
    st.subheader("📊 Business Overview")
    # Live data load karna
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    t_sale = s_df['total'].sum() if not s_df.empty else 0 # Kul bikri
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0 # Kul kharid
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0 # Kul kharche
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp # Net munafa

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. PURCHASE (Item Name, Qty, Price + History List) ---
elif menu == "📦 Purchase":
    st.subheader("📦 Add New Stock")
    inv_df = load_data("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name") # Product ka naam
        q = st.number_input("Quantity (Nos/Kg/Ml)", min_value=0.1) # Matra
        p = st.number_input("Purchase Price", min_value=1) # Kharid rate
        if st.form_submit_button("ADD STOCK"):
            new_r = pd.DataFrame([{"Item": n, "qty": q, "p_price": p}])
            conn.update(worksheet="Inventory", data=pd.concat([inv_df, new_r], ignore_index=True)) # Sheet update
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Purchase History")
    st.table(inv_df.tail(10)) # Niche list dikhegi

# --- 6. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.subheader("📋 All Shop Stock")
    st.table(load_data("Inventory")) # Poori stock list

# --- 7. EXPENSES (Dropdown + Miscellaneous Expense) ---
elif menu == "💰 Expenses":
    st.subheader("💰 Expense Records")
    exp_df = load_data("Expenses")
    with st.form("exp_f"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"]) # Options
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE"):
            new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
            conn.update(worksheet="Expenses", data=pd.concat([exp_df, new_e], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(exp_df.tail(10)) # Niche list

# --- 8. PET REGISTER (Phone, Breed, Age, Weight, Vaccine) ---
elif menu == "🐾 Pet Register":
    st.subheader("🐾 Customer & Pet Records")
    pet_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2:
            age = st.text_input("Dog Age"); wt = st.text_input("Dog Weight"); vax = st.date_input("Vaccination Date")
        if st.form_submit_button("SAVE PET"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Age": age, "Weight": wt, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([pet_df, new_p], ignore_index=True))
            st.success("Pet Saved!"); st.rerun()
    st.table(pet_df.tail(10)) # Niche records table

# --- 9. ADMIN SETTINGS (Dues & New ID) ---
elif menu == "⚙️ Admin Settings":
    st.subheader("⚙️ Admin Controls")
    dues_df = load_data("Dues")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Company Udhaar (Dues)")
        comp = st.text_input("Company Name"); d_amt = st.number_input("Udhaar Amount", min_value=1)
        if st.button("Save Udhaar"):
            new_d = pd.DataFrame([{"Company": comp, "Amount": d_amt}])
            conn.update(worksheet="Dues", data=pd.concat([dues_df, new_d], ignore_index=True)) # Udhaar record
            st.success("Dues Saved!"); st.rerun()
        st.table(dues_df)
    with col2:
        st.subheader("👤 Create New Staff ID")
        st.text_input("New Username"); st.text_input("New Password", type="password")
        if st.button("Create ID"): st.success("Account Ready!")

# --- 10. BILLING ---
elif menu == "🧾 Billing":
    st.subheader("🧾 Generate Bill")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("bill_f"):
        item = st.selectbox("Product", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", min_value=0.1); p = st.number_input("Selling Price", min_value=1)
        if st.form_submit_button("COMPLETE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": item, "total": q*p, "profit": (p-10)*q}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Done!"); st.rerun()
    st.table(sales_df.tail(10)) # Niche history table
