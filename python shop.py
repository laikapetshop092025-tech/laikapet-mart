import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Safe logic) ---
# Ensuring all keys exist so software never crashes
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
    if st.button("LOGIN", use_container_width=True):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- 4. SIDEBAR & REPORTS ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses", 
    "⚙️ Admin Settings"
])

st.sidebar.write("---")
if st.session_state.sales:
    # Standard CSV download (No extra library needed)
    csv_data = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📊 Download Sales Report", csv_data, f"Sales_{datetime.now().date()}.csv", "text/csv")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    today_dt = datetime.now().date()
    t_rev = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_rev)}")
    c2.metric("STOCK VALUE", f"₹{int(t_pur)}")
    c3.metric("EXPENSES", f"₹{int(t_exp)}")
    st.write("---")
    st.metric("NET PROFIT (Final Bachat)", f"₹{int(t_prof)}")

# --- 6. PET SALES REGISTER (Fixed Errors) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_f_vFinal"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone"); breed = st.selectbox("Breed", breeds)
        with c2:
            age = st.text_input("Age"); weight = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed, "Age": age, "Weight": weight, "Due": dv})
            st.rerun()
    if st.session_state.pet_records:
        st.write("### Registered Pets")
        for i, p in enumerate(st.session_state.pet_records):
            ca, cb = st.columns([4, 1])
            ca.write(f"*{p.get('Customer', 'N/A')}* | {p.get('Breed', 'N/A')} | Vaccine: {p.get('Due', 'N/A')}")
            if cb.button("Delete", key=f"p_{i}"):
                st.session_state.pet_records.pop(i); st.rerun()

# --- 7. BILLING TERMINAL (Auto-Stock Revert & History Fix) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_f_vFinal"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            c1, c2, c3 = st.columns(3)
            with c1: u_sel = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1)
            cust_name = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE"):
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    # Explicit dictionary creation to avoid NameError
                    sale_entry = {"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "Unit": u_sel, "total": total, "profit": profit, "Customer": cust_name}
                    st.session_state.sales.append(sale_entry)
                    st.rerun()
                else: st.error("Stock Kam Hai!")

    st.write("---")
    st.subheader("📋 Recent Sales (Delete to Revert Stock)")
    # Using safe .get() to avoid KeyErrors in history
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        item_name = s.get('Item', 'Unknown')
        total_val = s.get('total', 0)
        qty_val = s.get('Qty', 0)
        ca.write(f"*{item_name}* | Qty: {qty_val} | Total: ₹{total_val} | Cust: {s.get('Customer','')}")
        if cb.button("🗑️ Delete Bill", key=f"s_{idx}"):
            if item_name in st.session_state.inventory:
                st.session_state.inventory[item_name]['qty'] += qty_val
            st.session_state.sales.pop(idx); st.rerun()

# --- 8. PURCHASE & 9. LIVE STOCK ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Management")
    with st.form("pur_f_vFinal"):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        rate = st.number_input("Purchase Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.rerun()
    st.write("---")
    for item, v in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {v.get('qty',0)} {v.get('unit','Unit')} | Price: ₹{v.get('p_price',0)}")
        if cb.button("Delete Item", key=f"inv_{item}"):
            del st.session_state.inventory[item]; st.rerun()

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

# --- 10. EXPENSES (Categorized) ---
elif menu == "💰 Expenses":
    st.title("💰 Business Expenses")
    exp_cats = ["Rent", "Electricity Bill", "Staff Salary", "Tea/Snacks", "Other"]
    with st.form("exp_f_vFinal"):
        cat = st.selectbox("Category", exp_cats); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
            st.rerun()
    for i, ex in enumerate(st.session_state.expenses):
        ca, cb = st.columns([4, 1])
        ca.write(f"{ex.get('Date')} | *{ex.get('Category')}* | ₹{ex.get('Amount')}")
        if cb.button("Delete", key=f"ex_{i}"):
            st.session_state.expenses.pop(i); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        nu = st.text_input("New ID"); np = st.text_input("New Password")
        if st.button("Create"): st.session_state.users[nu] = np; st.success("Done!")
