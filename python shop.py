import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 1. DATA INITIALIZATION (Sab kuch save karne ke liye) ---
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- 2. LOGIN LOGIC ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Galt ID ya Password!")
    st.stop()

# --- 3. SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing (Items)", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (Ab yahan sab dikhega) ---
if menu == "📊 Dashboard":
    st.title("Dukan Ka Dashboard")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_pets = len(st.session_state.pet_records)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales (Items)", f"Rs. {t_sales}")
    col2.metric("Pets Sold", t_pets)
    col3.metric("Live Inventory Items", len(st.session_state.inventory))

# --- 5. PET SALES REGISTER (Pet + Vaccine Data) ---
elif menu == "🐾 Pet Sales Register":
    st.title("Janwar Bikri aur Vaccine Data")
    with st.form("pet_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name")
        c_phone = st.text_input("Phone Number")
        pet_detail = st.text_input("Pet Breed/Name")
        next_vac = st.date_input("Agli Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("Save Pet Record"):
            st.session_state.pet_records.append({"Date": datetime.now(), "Customer": c_name, "Phone": c_phone, "Pet": pet_detail, "Next Due": next_vac})
            st.success("Pet Record Saved!")
    st.table(pd.DataFrame(st.session_state.pet_records))

# --- 6. PURCHASE (Stock Bharne ke liye) ---
elif menu == "📦 Purchase":
    st.title("Stock Entry")
    with st.form("p_form", clear_on_submit=True):
        n = st.text_input("Item Name")
        b = st.number_input("Buy Rate", min_value=0.0)
        s = st.number_input("Sell Rate", min_value=0.0)
        q = st.number_input("Qty", min_value=0.0)
        if st.form_submit_button("Add Stock"):
            st.session_state.inventory[n] = {'p_price': b, 's_price': s, 'qty': q}
            st.success(f"{n} Stock mein jud gaya!")

# --- 7. LIVE STOCK (Stock dekhne ke liye) ---
elif menu == "📋 Live Stock":
    st.title("Current Inventory")
    if st.session_state.inventory:
        st.table(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'))
    else:
        st.info("Stock khali hai. Purchase mein entry karein.")

# --- 8. BILLING ---
elif menu == "🧾 Billing (Items)":
    st.title("Billing")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein saaman add karein!")
    else:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
        qty = st.number_input("Qty", min_value=0.1)
        if st.form_submit_button("Bill Banayein"):
            # Bill logic here
            st.success("Bill Generated!")
