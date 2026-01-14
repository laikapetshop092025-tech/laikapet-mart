import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# CSS for Classic Look
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Proof) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT LOGIC (10 Minutes) ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else:
        st.session_state.last_activity = time.time()

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = u_id
                st.rerun()
            else:
                st.error("Ghalat ID/Password!")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. DASHBOARD (Waisa hi jaisa pehle tha) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    
    # Safely calculating metrics to avoid KeyErrors
    total_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    total_expense = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    total_purchase = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    net_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - total_expense

    # Displaying in classic columns
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(total_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(total_purchase)}")
    c3.metric("NET PROFIT", f"₹{int(net_profit)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(total_expense)}")

    st.write("---")
    st.subheader("📋 Recent Business Activity")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("*Recent Sales*")
        if st.session_state.sales: st.table(pd.DataFrame(st.session_state.sales).tail(5))
    with col_b:
        st.write("*Recent Expenses*")
        if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses).tail(5))

    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Sales Report", csv, "Sales_Report.csv", "text/csv")

# --- 7. PET SALES REGISTER (With All Details) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Contact Number")
            breed = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Pug", "Indie", "Other"])
        with c2:
            age = st.text_input("Pet Age")
            weight = st.text_input("Weight (kg)")
            vaccine = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Breed": breed, "Age": age, "Weight": weight, "Next Vaccine": vaccine})
            st.rerun()
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 8. BILLING TERMINAL (Revert Stock Logic) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & History")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            qty = st.number_input("Quantity", min_value=0.1)
            price = st.number_input("Selling Price", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("GENERATE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    profit = (price - inv['p_price']) * qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": qty, "total": qty*price, "profit": profit, "Customer": cust})
                    st.rerun()
                else: st.error("Stock khatam!")
    
    st.write("---")
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        ca.write(f"*{s.get('Item')}* | ₹{s.get('total')} | Cust: {s.get('Customer')}")
        if cb.button("🗑️ Delete Bill", key=f"s_{idx}"):
            if s['Item'] in st.session_state.inventory:
                st.session_state.inventory[s['Item']]['qty'] += s['Qty']
            st.session_state.sales.pop(idx); st.rerun()

# --- 9. PURCHASE (Stock Fix) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form"):
        n = st.text_input("Item Name")
        r = st.number_input("Purchase Price", min_value=1)
        q = st.number_input("Quantity", min_value=1)
        u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
            st.rerun()
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

# --- 10. EXPENSES & ADMIN ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    e_name = st.text_input("Expense Name")
    e_amt = st.number_input("Amount", min_value=1)
    if st.button("Add Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Item": e_name, "Amount": e_amt})
        st.rerun()
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    new_u = st.text_input("New Username")
    new_p = st.text_input("New Password")
    if st.button("Create Staff Account"):
        st.session_state.users[new_u] = new_p
        st.success(f"User {new_u} added!")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v.get('unit','-')} for k, v in st.session_state.inventory.items()]))
