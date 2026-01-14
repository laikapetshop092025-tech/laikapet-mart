import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

st.markdown("""
    <div style='text-align: center;'>
        <h1 style='color: #4A90E2; margin-bottom: 0;'>🐾 LAIKA PET MART</h1>
        <p style='font-size: 18px; color: grey;'>Pet Shop Management System</p>
    </div>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("<h3 style='text-align: center;'>🔐 Login to Portal</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Username (Admin: Laika)")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
            else:
                st.error("Galat ID ya Password!")
    st.stop()

# --- 4. SIDEBAR MENU ---
st.sidebar.title(f"👤 User: {st.session_state.current_user}")
menu = st.sidebar.radio("Menu", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses", 
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Updated as per your request) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    
    # Calculations
    today = datetime.now().date()
    total_revenue = sum(s.get('total', 0) for s in st.session_state.sales)
    total_expenses = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    total_purchase_val = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    
    # Daily Profit Calculation
    daily_sales = [s for s in st.session_state.sales if s.get('Date') == today]
    daily_profit = sum(s.get('profit', 0) for s in daily_sales)
    
    # Net Profit (Total Profit from sales - Total Expenses)
    total_gross_profit = sum(s.get('profit', 0) for s in st.session_state.sales)
    net_profit = total_gross_profit - total_expenses

    # Row 1: Key Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE (Bikri)", f"₹{int(total_revenue)}")
    c2.metric("TOTAL PURCHASE (Stock Value)", f"₹{int(total_purchase_val)}")
    c3.metric("EXPENSES (Nikale Paise)", f"₹{int(total_expenses)}", delta_color="inverse")

    # Row 2: Profit Metrics
    st.write("---")
    c4, c5, c6 = st.columns(3)
    c4.metric("TODAY'S PROFIT", f"₹{int(daily_profit)}")
    c5.metric("NET PROFIT (Final Bachat)", f"₹{int(net_profit)}")
    c6.metric("PETS SOLD", len(st.session_state.pet_records))

    # CSV Download
    if st.session_state.sales:
        st.write("---")
        df_s = pd.DataFrame(st.session_state.sales)
        st.download_button("📥 Download Full Sales Report", df_s.to_csv(index=False).encode('utf-8'), "Sales_Report.csv", "text/csv")

# --- BAAKI CODE BINA KISI CHANGE KE ---

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Entry")
    with st.form("pet_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone Number")
        with c2:
            age = st.text_input("Age"); weight = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Age": age, "Weight": weight, "Due": dv})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            c1, c2, c3 = st.columns(3)
            with c1: u_sel = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01, step=0.1)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1, step=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE & SHOW BILL"):
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "Unit": u_sel, "total": total, "profit": profit})
                    st.success(f"Bill Generated! Total: ₹{total}")
                    st.markdown(f"*INVOICE*\nCustomer: {cust}\nTotal: ₹{total}")
                else: st.error("Stock Kam Hai!")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Entry")
    with st.form("pur_f", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u}
            st.success("Stock Added!")

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
        if st.button("Create Account"): 
            st.session_state.users[u] = p; st.success("New Staff Account Created!")
