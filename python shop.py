import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    u = st.text_input("Username"); p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True; st.session_state.current_user = u; st.rerun()
    st.stop()

# --- 4. SIDEBAR & EXCEL REPORT ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# --- EXCEL REPORT BUTTON IN SIDEBAR ---
st.sidebar.write("---")
st.sidebar.subheader("📥 Download Reports")
if st.session_state.sales:
    df_sales = pd.DataFrame(st.session_state.sales)
    csv_sales = df_sales.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📊 Download Sales (Excel/CSV)", csv_sales, f"Sales_Report_{datetime.now().date()}.csv", "text/csv")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False; st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    today = datetime.now().date()
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

# --- 6. BILLING TERMINAL (With Auto-Stock Revert) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & Delete Options")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_v4"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
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
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "total": total, "profit": profit, "Customer": cust})
                    st.rerun()
                else: st.error("Stock Kam Hai!")
    
    st.write("---")
    st.subheader("📋 Recent Sales (Delete to Revert Stock)")
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        ca.write(f"*{s['Item']}* | Qty: {s['Qty']} | Total: ₹{s['total']} | Cust: {s.get('Customer','')}")
        if cb.button("🗑️ Delete Bill", key=f"sale_{idx}"):
            # Auto-Stock Revert Logic
            item_name = s['Item']
            if item_name in st.session_state.inventory:
                st.session_state.inventory[item_name]['qty'] += s['Qty']
            st.session_state.sales.pop(idx)
            st.success(f"Sale deleted! Stock for {item_name} reverted.")
            st.rerun()

# --- 7. PURCHASE (With Delete) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Management")
    with st.form("pur_v4", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        rate = st.number_input("Purchase Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.rerun()
    
    st.write("---")
    st.subheader("📋 Inventory List (Remove Item)")
    for item, v in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {v['qty']} {v['unit']} | Price: ₹{v['p_price']}")
        if cb.button("🗑️ Remove", key=f"inv_{item}"):
            del st.session_state.inventory[item]
            st.rerun()

# --- 8. EXPENSES (With Dropdown & Delete) ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Tracker")
    exp_types = ["Rent", "Electricity Bill", "Staff Salary", "Tea/Snacks", "Other"]
    with st.form("exp_v4"):
        cat = st.selectbox("Category", exp_types); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
            st.rerun()
    
    for i, ex in enumerate(st.session_state.expenses):
        ca, cb = st.columns([4, 1])
        ca.write(f"{ex['Date']} | *{ex['Category']}* | ₹{ex['Amount']}")
        if cb.button("🗑️ Delete", key=f"ex_{i}"):
            st.session_state.expenses.pop(i); st.rerun()

# --- BAAKI CODE (PET REGISTER & LIVE STOCK) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_v4"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Name"); p = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); d = st.date_input("Vaccine")
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Customer": n, "Breed": br, "Due": d})
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        nu = st.text_input("New ID"); np = st.text_input("New Password")
        if st.button("Create"): st.session_state.users[nu] = np; st.success("Done!")
