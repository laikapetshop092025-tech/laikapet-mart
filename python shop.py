import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- SETTINGS: App ka naam aur layout ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA INITIALIZATION: Data ko gayab hone se bachane ke liye ---
if 'shop_name' not in st.session_state: st.session_state.shop_name = "LAIKA PET MART"
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN: Password system ---
if not st.session_state.logged_in:
    st.title(f"🔐 {st.session_state.shop_name} - LOGIN")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
            else: st.error("Galt ID/Password")
    st.stop()

# --- SIDEBAR: Main Menu ---
st.sidebar.title(f"🐾 {st.session_state.shop_name}")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD: 4 main metrics ---
if menu == "📊 Dashboard":
    st.title("📊 Business Overview")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    # Net Profit = Total Profit (Selling-Buying) - Expenses
    net_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"Rs. {t_sales}")
    col2.metric("PETS SOLD", len(st.session_state.pet_records))
    col3.metric("NET PROFIT", f"Rs. {net_prof}")
    col4.metric("EXPENSES", f"Rs. {t_exp}")

# --- 2. PET SALES: Pet bechna aur Vaccine record ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Sales & Health Record")
    with st.form("pet_sale", clear_on_submit=True):
        c_name = st.text_input("Customer Name")
        c_phone = st.text_input("Phone Number")
        pet = st.text_input("Pet Breed/Age")
        next_v = st.date_input("Agli Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("Save Record (Enter)"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": c_name, "Phone": c_phone, "Pet": pet, "Next Due": next_v})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 3. BILLING: Item bechna aur stock kam karna ---
elif menu == "🧾 Billing":
    st.title("🧾 Billing")
    if not st.session_state.inventory: st.warning("Purchase mein stock daalein!")
    else:
        with st.form("bill_f", clear_on_submit=True):
            it = st.selectbox("Item", list(st.session_state.inventory.keys()))
            qty = st.number_input("Qty", min_value=0.1)
            price = st.number_input("Selling Price", min_value=0.0)
            if st.form_submit_button("Generate Bill"):
                if qty <= st.session_state.inventory[it]['qty']:
                    st.session_state.inventory[it]['qty'] -= qty
                    profit = (price - st.session_state.inventory[it]['p_price']) * qty
                    st.session_state.sales.append({"total": qty*price, "profit": profit, "item": it})
                    st.success("Billed!")
                else: st.error("Stock Kam Hai")

# --- 4. PURCHASE: Stock entry (No selling price here) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Entry")
    with st.form("pur_f", clear_on_submit=True):
        n = st.text_input("Item Name")
        p = st.number_input("Purchase Price (Khareed)", min_value=0.0)
        q = st.number_input("Quantity", min_value=0.0)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': p, 'qty': q}
            st.success("Stock Added!")

# --- 5. LIVE STOCK: Report ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory: st.table(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'))

# --- 6. EXPENSES: Kharcha ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp_f", clear_on_submit=True):
        r = st.text_input("Reason")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. SETTINGS: Admin Authority ---
elif menu == "⚙️ Admin Settings":
    if st.session_state.current_user == "Laika":
        st.title("⚙️ Admin Settings")
        st.session_state.shop_name = st.text_input("Dukan ka Naam", value=st.session_state.shop_name)
        u = st.text_input("New Staff ID")
        p = st.text_input("New Password", type="password")
        if st.button("Create ID"): 
            st.session_state.users[u] = p
            st.success("ID Created!")
    else: st.warning("No Authority")
