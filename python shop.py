import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- SETTINGS: Website ka naam aur page ki choudaai set karna ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATABASE: Saara data (Users, Stock, Sales) save karne ki jagah ---
if 'shop_name' not in st.session_state: st.session_state.shop_name = "LAIKA PET MART"
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN: Bina ID-Password ke koi andar na aa sake ---
if not st.session_state.logged_in:
    st.title(f"🔐 {st.session_state.shop_name} - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"): # Enter dabane par ye check karega
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Galt ID ya Password!")
    st.stop()

# --- SIDEBAR: Ulte haath wala Menu jahan se button dabate hain ---
st.sidebar.title(f"🐾 {st.session_state.shop_name}")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# Logout Button: App se bahar nikalne ke liye
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD: Sirf 4 main hisab dikhane ke liye ---
if menu == "📊 Dashboard":
    st.title(f"📊 {st.session_state.shop_name} Dashboard")
    # Hisab lagane ka logic
    total_sales = sum(s['total'] for s in st.session_state.sales)
    total_purchase = sum(v['p_price'] * v['qty'] for v in st.session_state.inventory.values())
    total_expenses = sum(e['Amount'] for e in st.session_state.expenses)
    net_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - total_expenses
    pets_sold = len(st.session_state.pet_records)

    # Screen par 4 dabbe (Metrics) dikhana
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"Rs. {total_sales}")
    col2.metric("TOTAL PURCHASE", f"Rs. {total_purchase}")
    col3.metric("NET PROFIT", f"Rs. {net_profit}")
    col4.metric("PETS SOLD", f"{pets_sold}")

# --- 2. PET SALES REGISTER: Janwar aur Vaccine ki entry ---
elif menu == "🐾 Pet Sales Register":
    st.title("Janwar Bikri aur Vaccine Data")
    with st.form("pet_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name")
        c_phone = st.text_input("Phone Number")
        pet_detail = st.text_input("Pet Breed/Name")
        next_vac = st.date_input("Agli Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("Save Pet Record"): # Enter se data save hoga
            st.session_state.pet_records.append({"Date": datetime.now(), "Customer": c_name, "Phone": c_phone, "Pet": pet_detail, "Next Due": next_vac})
            st.success("Pet Record Saved!")
    st.table(pd.DataFrame(st.session_state.pet_records)) # Purani list dikhana

# --- 3. PURCHASE: Stock bharne ke liye (Sirf Khareed Rate) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("Stock Entry")
    with st.form("p_form", clear_on_submit=True):
        n = st.text_input("Item Name")
        b = st.number_input("Purchase Price (Khareed Rate)", min_value=0.0)
        q = st.number_input("Quantity / Weight", min_value=0.0)
        if st.form_submit_button("Add Stock"):
            if n:
                if n in st.session_state.inventory:
                    st.session_state.inventory[n]['qty'] += q
                else:
                    st.session_state.inventory[n] = {'p_price': b, 'qty': q}
                st.success(f"{n} Stock mein jud gaya!")

# --- 4. ADMIN SETTINGS: Dukan ka naam aur Staff ID badalne ke liye ---
elif menu == "⚙️ Admin Settings":
    st.title("Admin Authority Panel")
    if st.session_state.current_user == "Laika": # Sirf aapko authority milegi
        new_shop = st.text_input("Dukan ka Naam Badlein", value=st.session_state.shop_name)
        if st.button("Update Name"): st.session_state.shop_name = new_shop
        
        st.subheader("Staff ki ID banayein")
        s_id = st.text_input("Staff Username")
        s_pass = st.text_input("Staff Password", type="password")
        if st.button("Create Staff ID"):
            st.session_state.users[s_id] = s_pass
            st.success(f"Staff ID '{s_id}' ban gayi!")
    else:
        st.warning("Aapko ye settings badalne ka haq nahi hai.")
