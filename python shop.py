import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Errors hatane ke liye) ---
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

# --- 4. SIDEBAR MENU ---
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock Inventory", 
    "💰 Expense Tracker", 
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Total Sale, Purchase, Profit, Expense) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    today = datetime.now().date()
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur_val = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    
    # Simple CSV Download (Excel compatible)
    st.subheader("📥 Reports Download")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        st.download_button("📥 Download Sales CSV", df_s.to_csv(index=False).encode('utf-8'), "Sales_Report.csv", "text/csv")

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur_val)}")
    c3.metric("EXPENSES (Nikale Paise)", f"₹{int(t_exp)}")
    
    st.write("---")
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    st.metric("NET PROFIT (Final Bachat)", f"₹{int(t_prof)}")

# --- 6. PET SALES REGISTER (Age, Weight, Vaccine Fix) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_form_v2", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone Number"); breed = st.selectbox("Breed", breeds)
        with c2:
            age = st.text_input("Age (Months)"); weight = st.text_input("Weight (KG)"); dv = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({"Date": today, "Customer": name, "Phone": phone, "Breed": breed, "Age": age, "Weight": weight, "Due": dv})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING TERMINAL (Dropdown, Unit & Sale Delete) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill & Delete Entry")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_v2"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Dukan mein bacha: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01, step=0.1)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1, step=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE & SHOW BILL"):
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Date": today, "Item": item, "Qty": q_sell, "Unit": u_sell, "total": total, "profit": profit, "Customer": cust})
                    st.success(f"Bill Generated! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")
    
    st.write("---")
    st.subheader("❌ Delete Recent Sales")
    for i, s in enumerate(st.session_state.sales):
        col_a, col_b = st.columns([4, 1])
        # Safe display logic to avoid KeyError
        col_a.write(f"{s.get('Date','N/A')} | {s.get('Item','N/A')} | ₹{s.get('total',0)} | Cust: {s.get('Customer','Cash')}")
        if col_b.button("Delete", key=f"ds_{i}"):
            it = s.get('Item')
            if it in st.session_state.inventory: st.session_state.inventory[it]['qty'] += s.get('Qty', 0)
            st.session_state.sales.pop(i)
            st.rerun()

# --- 8. PURCHASE & 9. LIVE STOCK (Display Fix) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock & Delete Items")
    with st.form("pur_v2", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    st.write("---")
    st.subheader("📋 Current Stock List")
    # FixedValueError and KeyError in Table
    for item, det in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {det.get('qty',0)} {det.get('unit','Unit')} | Rate: ₹{det.get('p_price',0)}")
        if cb.button("Delete", key=f"di_{item}"):
            del st.session_state.inventory[item]
            st.rerun()

elif menu == "📋 Live Stock Inventory":
    st.title("📋 Current Inventory Status")
    if st.session_state.inventory:
        st_data = [{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit'), "Value": v.get('qty',0)*v.get('p_price',0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))

# --- 10. EXPENSES & 11. SETTINGS ---
elif menu == "💰 Expense Tracker":
    st.title("💰 Expenses")
    with st.form("exp_v2"):
        res = st.text_input("Reason"); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.session_state.expenses.append({"Reason": res, "Amount": amt, "Date": today})
    for i, ex in enumerate(st.session_state.expenses):
        ca, cb = st.columns([4, 1])
        ca.write(f"{ex.get('Date')} | {ex.get('Reason')} | ₹{ex.get('Amount')}")
        if cb.button("Delete", key=f"de_{i}"):
            st.session_state.expenses.pop(i); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        nu = st.text_input("New ID"); np = st.text_input("New Password")
        if st.button("Create"): st.session_state.users[nu] = np; st.success("Created!")
