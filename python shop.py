import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATA INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h2>", unsafe_allow_html=True)
    u = st.text_input("Username"); p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True; st.session_state.current_user = u; st.rerun()
    st.stop()

# --- 4. WELCOME ADMIN & SIDEBAR ---
# Sidebar mein welcome message
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    c2.metric("NET PROFIT", f"₹{int(t_prof)}")
    c3.metric("EXPENSES", f"₹{int(t_exp)}")

# --- 6. BILLING TERMINAL (Summary Fix) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_v3"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Dukan mein bacha: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01, step=0.1)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1, step=1)
            
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE & SHOW BILL"):
                today_date = datetime.now().date()
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    # Summary ke liye saara data save karna
                    st.session_state.sales.append({"Date": today_date, "Item": item, "Qty": q_sell, "Unit": u_sell, "total": total, "profit": profit, "Customer": cust})
                    st.success(f"Bill Generated! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")
    
    st.write("---")
    st.subheader("📅 Aaj ki Sales Summary")
    if st.session_state.sales:
        st.table(pd.DataFrame(st.session_state.sales).tail(10)) # Last 10 bills dikhayega

# --- 7. PURCHASE (Date Column Added) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock with Date")
    with st.form("pur_v3", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        p_date = st.date_input("Purchase Date", datetime.now().date())
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u, 'Date': p_date}
            st.success(f"{n} added on {p_date}")

    st.write("---")
    st.subheader("📋 Purchase History")
    if st.session_state.inventory:
        history = [{"Item": k, "Date": v.get('Date', 'Old'), "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(history))

# --- BAAKI CODE (PET REGISTER, LIVE STOCK, EXPENSES, ADMIN) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Entry")
    with st.form("pet_v3"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Customer Name"); phone = st.text_input("Phone")
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Age": age, "Weight": wt, "Due": dv})
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        r = st.text_input("Reason"); a = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        u = st.text_input("New ID"); p = st.text_input("New Password")
        if st.button("Create"): st.session_state.users[u] = p; st.success("Created!")
