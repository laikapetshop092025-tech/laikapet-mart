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
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- 4. SIDEBAR ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Waisa hi jaisa pichli bar tha) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    today = datetime.now().date()
    
    # Calculations
    total_revenue = sum(s.get('total', 0) for s in st.session_state.sales)
    total_expenses = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    total_purchase_val = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    daily_profit = sum(s.get('profit', 0) for s in st.session_state.sales if s.get('Date') == today)
    net_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - total_expenses

    # Metrics Display
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE (Bikri)", f"₹{int(total_revenue)}")
    c2.metric("TOTAL PURCHASE (Stock)", f"₹{int(total_purchase_val)}")
    c3.metric("EXPENSES (Nikale Paise)", f"₹{int(total_expenses)}")
    
    st.write("---")
    c4, c5, c6 = st.columns(3)
    c4.metric("TODAY'S PROFIT", f"₹{int(daily_profit)}")
    c5.metric("NET PROFIT (Bachat)", f"₹{int(net_profit)}")
    c6.metric("PETS SOLD", len(st.session_state.pet_records))

    # DATA SAFETY SECTION
    st.write("---")
    st.subheader("💾 Data Backup (Hamesha ke liye safe rakhein)")
    st.info("Bhai, din khatam hone par niche diye button se apna record download kar liya karein, taaki reboot hone par data na khoye.")
    
    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sales Report (Excel)", csv, "sales_backup.csv", "text/csv")

# --- BAAKI CODE (NO CHANGE) ---

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Entry")
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Customer Name"); phone = st.text_input("Phone")
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Date": today, "Customer": name, "Phone": phone, "Age": age, "Weight": wt, "Due": dv})
            st.success("Record Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("GENERATE BILL"):
                if q_sell <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv['p_price']) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": total, "profit": profit, "Customer": cust})
                    st.success(f"Bill Generated! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("purchase_form"):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Purchase Price", min_value=1); q = st.number_input("Quantity", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.success("Stock Added!")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

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
