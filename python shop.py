import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Proof Logic) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("### 🔐 Admin Login")
    u = st.text_input("Username (Laika)")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- 4. SIDEBAR WELCOME ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Total Sale, Purchase, Profit) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur_val = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    c2.metric("STOCK VALUE", f"₹{int(t_pur_val)}")
    c3.metric("EXPENSES", f"₹{int(t_exp)}")
    st.write("---")
    st.metric("NET PROFIT (Final Bachat)", f"₹{int(t_prof)}")

# --- 6. PET SALES REGISTER (Fixed Error) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breed_list = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Pitbull", "Indie", "Persian Cat", "Other"]
    with st.form("pet_form_fixed", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone Number"); br = st.selectbox("Breed", breed_list)
        with col2:
            age = st.text_input("Age"); wt = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": br, "Age": age, "Weight": wt, "Due": dv})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING TERMINAL (Summary + Delete) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & Sales Summary")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("billing_fixed"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE"):
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "Unit": u_sell, "total": total, "profit": profit, "Customer": cust})
                    st.success(f"Bill Generated! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")
    
    st.write("---")
    st.subheader("📋 Recent Sales Summary")
    if st.session_state.sales:
        st.table(pd.DataFrame(st.session_state.sales).tail(10))

# --- 8. PURCHASE (Date & History Fix) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Management")
    with st.form("pur_fixed", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        with col2:
            rate = st.number_input("Purchase Price", min_value=1); q = st.number_input("Qty", min_value=1)
            dt = st.date_input("Purchase Date", datetime.now().date())
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u, 'Date': dt}
            st.success(f"{n} Updated!")
    
    st.write("---")
    st.subheader("📋 Purchase History")
    if st.session_state.inventory:
        data = [{"Item": k, "Date": v.get('Date', 'Old'), "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# --- 9. EXPENSES (With Dropdowns) ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Tracker")
    # Dropdown Options
    exp_types = ["Rent", "Electricity Bill", "Staff Salary", "Pet Food/Maintenance", "Tea/Snacks", "Other"]
    with st.form("exp_dropdown"):
        cat = st.selectbox("Select Expense Type", exp_types)
        detail = st.text_input("Extra Detail (Optional)")
        amt = st.number_input("Amount (₹)", min_value=1)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Detail": detail, "Amount": amt})
            st.success("Expense Recorded!")
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

# --- LIVE STOCK & ADMIN ---
elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        nu = st.text_input("New ID"); np = st.text_input("New Password")
        if st.button("Create Account"): st.session_state.users[nu] = np; st.success("Created!")
