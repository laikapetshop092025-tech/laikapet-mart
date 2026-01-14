import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# CSS for App Look
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT LOGIC (10 Minutes) ---
if st.session_state.logged_in:
    current_time = time.time()
    inactive_limit = 10 * 60  # 10 minutes in seconds
    
    if current_time - st.session_state.last_activity > inactive_limit:
        st.session_state.logged_in = False
        st.warning("You have been logged out due to inactivity.")
        st.rerun()
    else:
        # Update activity time whenever anything happens
        st.session_state.last_activity = current_time

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🔐 Login</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = u_id
                st.session_state.last_activity = time.time()
                st.rerun()
            else:
                st.error("Invalid ID or Password!")
    st.stop()

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", [
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

# --- 6. ADMIN SETTINGS (NEW) ---
if menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("Manage Login Users")
    with st.form("add_user"):
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password")
        if st.form_submit_button("Create User"):
            if new_u:
                st.session_state.users[new_u] = new_p
                st.success(f"User {new_u} added!")
            else: st.error("Username cannot be empty")
    
    st.write("Current Users:", list(st.session_state.users.keys()))

# --- 7. DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_rev = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_rev)}")
    c2.metric("EXPENSES", f"₹{int(t_exp)}")
    c3.metric("NET PROFIT", f"₹{int(t_prof)}")
    
    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sales Excel", csv, "Sales_Report.csv", "text/csv")

# --- 8. BILLING (With Auto-Stock Revert) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            q_sell = st.number_input("Quantity", min_value=0.01)
            r_sell = st.number_input("Rate (₹)", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE"):
                if q_sell <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    profit = (r_sell - inv['p_price']) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "total": q_sell*r_sell, "profit": profit, "Customer": cust})
                    st.rerun()
                else: st.error("Stock Kam Hai!")

    st.write("---")
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        ca.write(f"*{s['Item']}* | ₹{s['total']} | {s['Customer']}")
        if cb.button("🗑️ Delete", key=f"s_{idx}"):
            if s['Item'] in st.session_state.inventory:
                st.session_state.inventory[s['Item']]['qty'] += s['Qty']
            st.session_state.sales.pop(idx); st.rerun()

# --- OTHER SECTIONS (Purchase, Stock, Expenses, Pets) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u}
            st.rerun()

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    cats = ["Rent", "Electricity", "Salary", "Food", "Other"]
    cat = st.selectbox("Category", cats); amt = st.number_input("Amount", min_value=1)
    if st.button("Save"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
        st.rerun()

elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pets")
    # Same Pet Logic as before...
    name = st.text_input("Customer"); breed = st.text_input("Breed")
    if st.button("Save Pet"):
        st.session_state.pet_records.append({"Customer": name, "Breed": breed})
        st.rerun()
    st.write(st.session_state.pet_records)

elif menu == "📋 Live Stock":
    st.title("📋 Stock")
    st.table(pd.DataFrame([{"Item": k, "Qty": v['qty']} for k, v in st.session_state.inventory.items()]))
