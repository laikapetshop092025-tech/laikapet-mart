import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. PAGE SETUP (PWA Features) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Hide Streamlit Default Menu for App Look
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN LOGIC (FIXED) ---
# Agar logged_in key nahi hai toh false set karo
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Database setup (Saara data yahan initialized hai)
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h2>", unsafe_allow_html=True)
    
    # Simple Login Form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("LOGIN", use_container_width=True)
        
        if submit:
            # Username: Laika | Password: Ayush@092025
            if username == "Laika" and password == "Ayush@092025":
                st.session_state.logged_in = True
                st.session_state.current_user = "Laika"
                st.success("Login Successful! Opening Dashboard...")
                st.rerun() # Refresh karke dashboard par jane ke liye
            else:
                st.error("Ghalat ID ya Password! Phir se koshish karein.")
    st.stop() # Jab tak login na ho, niche ka code mat dikhao

# --- 3. DASHBOARD & NAVIGATION (Sirf Login ke baad dikhega) ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD CODE ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    c2.metric("EXPENSES", f"₹{int(t_exp)}")
    c3.metric("NET PROFIT", f"₹{int(t_prof)}")

    st.write("---")
    st.subheader("📥 Data Backup")
    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("Download Sales Report", csv, "sales.csv", "text/csv")

# --- 5. BILLING TERMINAL (With Auto-Stock Revert) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("billing_v5"):
            item = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            
            c1, c2, c3 = st.columns(3)
            with c1: q_sell = st.number_input("Quantity", min_value=0.01)
            with c2: r_sell = st.number_input("Rate (₹)", min_value=1)
            with c3: cust = st.text_input("Customer Name")
            
            if st.form_submit_button("GENERATE BILL"):
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "total": total, "profit": profit, "Customer": cust})
                    st.rerun()
                else: st.error("Stock Kam Hai!")

    st.write("---")
    st.subheader("📋 Recent Bills (Delete to Revert Stock)")
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        ca.write(f"*{s['Item']}* | Qty: {s['Qty']} | Total: ₹{s['total']} | Cust: {s['Customer']}")
        if cb.button("🗑️ Delete", key=f"s_{idx}"):
            if s['Item'] in st.session_state.inventory:
                st.session_state.inventory[s['Item']]['qty'] += s['Qty']
            st.session_state.sales.pop(idx)
            st.rerun()

# --- 6. PURCHASE (Add Stock) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("purchase_v5"):
        n = st.text_input("Item Name")
        u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1)
        q = st.number_input("Quantity", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.success(f"{n} Added!")
    
    st.write("---")
    for item, v in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {v['qty']} {v['unit']} | Buy Rate: ₹{v['p_price']}")
        if cb.button("Delete Item", key=f"inv_{item}"):
            del st.session_state.inventory[item]; st.rerun()

# Baki sections (Pets, Live Stock, Expenses) bhi isi tarah simple aur delete button ke saath chalenge.
