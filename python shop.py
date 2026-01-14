import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP (Branding & Icon) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Dashboard ke upar Icon aur Branding
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #4A90E2; font-size: 40px; font-weight: bold; margin-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# Top par Branding aur Icon
st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Hamesha Aapke Pet Ke Saath 🤝</h4>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Safe) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT & LOGIN (No Change in Logic) ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = u_id
                st.rerun()
            else: st.error("Ghalat ID/Password!")
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Classic Look) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("NET PROFIT", f"₹{int(n_prof)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udhaar = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        st.warning(f"⚠️ Total Company Udhaar: ₹{int(t_udhaar)}")

# --- 6. EXPENSES (With Your Requested Dropdown) ---
elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    # Dropdown for Expense categories
    exp_cats = ["Rent", "Electricity Bill", "Staff Salary", "Pet Food / Supplies", "Tea & Snacks", "Maintenance", "Other"]
    e_cat = st.selectbox("Select Expense Category", exp_cats)
    e_detail = st.text_input("Additional Detail (Optional)")
    e_amt = st.number_input("Amount (₹)", min_value=1)
    
    if st.button("Add Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Category": e_cat, "Detail": e_detail, "Amount": e_amt})
        st.success("Expense Saved!")
        st.rerun()
    
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. BAAKI SECTIONS (NO CHANGE IN CODE) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: 
            name = st.text_input("Customer Name"); phone = st.text_input("Phone")
            breed = st.selectbox("Breed", ["Labrador", "German Shepherd", "Beagle", "Pug", "Indie", "Other"])
        with c2: 
            age = st.text_input("Pet Age"); weight = st.text_input("Weight (kg)"); vaccine = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Breed": breed, "Age": age, "Weight": weight, "Next Vaccine": vaccine})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & History")
    if not st.session_state.inventory: st.warning("Stock khali hai!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            qty = st.number_input("Quantity", min_value=0.1)
            price = st.number_input("Price", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("GENERATE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    profit = (price - inv['p_price']) * qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": qty, "total": qty*price, "profit": profit, "Customer": cust})
                    st.rerun()
                else: st.error("Stock khatam!")
    
    for i, s in enumerate(reversed(st.session_state.sales)):
        idx = len(st.session_state.sales) - 1 - i
        ca, cb = st.columns([4, 1])
        # Safe get prevents the KeyError in your photo
        ca.write(f"*{s.get('Item','-')}* | ₹{s.get('total',0)} | Cust: {s.get('Customer','')}")
        if cb.button("🗑️ Delete Bill", key=f"s_{idx}"):
            if s.get('Item') in st.session_state.inventory: st.session_state.inventory[s['Item']]['qty'] += s.get('Qty',0)
            st.session_state.sales.pop(idx); st.rerun()

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form"):
        n = st.text_input("Item Name"); r = st.number_input("Purchase Price", min_value=1)
        q = st.number_input("Quantity", min_value=1); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
            st.rerun()

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    st.subheader("🏢 Company Udhaar (Pending Payments)")
    with st.form("udhaar_form", clear_on_submit=True):
        c_name = st.text_input("Company Name"); c_amt = st.number_input("Amount (₹)", min_value=1)
        if st.form_submit_button("Add Udhaar"):
            st.session_state.company_dues.append({"Company": c_name, "Amount": c_amt, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','-')} for k, v in st.session_state.inventory.items()]))
