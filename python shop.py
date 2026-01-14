import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. PAGE SETUP & APP LOOK ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# App jaisa look dene ke liye (PWA Features)
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 10px; height: 3em; background-color: #4A90E2; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Proof) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- 3. LOGIN SYSTEM (FIXED) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🔐 Login</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Username: Laika | Password: Ayush@092025 (L and A Capital)
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.session_state.current_user = "Laika"
                st.rerun()
            else:
                st.error("Ghalat ID/Password! Sahi: 'Laika' & 'Ayush@092025'")
    st.stop()

# --- 4. NAVIGATION & SIDEBAR ---
st.sidebar.markdown(f"## 🤝 Welcome, {st.session_state.current_user}")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses"
])

# Excel Report Download Button
if st.session_state.sales:
    csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Sales Excel", csv, f"Sales_{datetime.now().date()}.csv", "text/csv")

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Fixed as per request) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    today = datetime.now().date()
    t_rev = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_rev)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("EXPENSES", f"₹{int(t_exp)}")
    
    st.write("---")
    c4, c5 = st.columns(2)
    c4.metric("NET PROFIT", f"₹{int(t_prof)}")
    c5.metric("PETS SOLD", len(st.session_state.pet_records))

# --- 6. PET SALES REGISTER (More Breeds) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breed_list = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Indie", "Pitbull", "Shih Tzu", "Beagle", "Rottweiler", "Persian Cat", "Other"]
    with st.form("pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: 
            n = st.text_input("Customer Name"); p = st.text_input("Phone"); b = st.selectbox("Breed", breed_list)
        with c2: 
            a = st.text_input("Age"); w = st.text_input("Weight"); d = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": n, "Phone": p, "Breed": b, "Age": a, "Weight": w, "Due": d})
            st.rerun()
    
    for i, pet in enumerate(st.session_state.pet_records):
        col_a, col_b = st.columns([4, 1])
        col_a.write(f"*{pet['Customer']}* | {pet['Breed']} | Vaccine: {pet['Due']}")
        if col_b.button("Delete", key=f"pet_{i}"):
            st.session_state.pet_records.pop(i); st.rerun()

# --- 7. BILLING TERMINAL (Auto-Stock Revert) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & History")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            c1, c2, c3 = st.columns(3)
            with c1: q_sell = st.number_input("Quantity", min_value=0.01)
            with c2: r_sell = st.number_input("Rate (₹)", min_value=1)
            with c3: cust = st.text_input("Customer Name")
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
        ca.write(f"*{s['Item']}* | Qty: {s['Qty']} | Total: ₹{s['total']} | Cust: {s['Customer']}")
        if cb.button("🗑️ Delete Bill", key=f"s_{idx}"):
            if s['Item'] in st.session_state.inventory:
                st.session_state.inventory[s['Item']]['qty'] += s['Qty']
            st.session_state.sales.pop(idx); st.rerun()

# --- 8. PURCHASE & 9. LIVE STOCK ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form"):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.rerun()
    for item, v in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {v['qty']} {v['unit']}")
        if cb.button("Remove Item", key=f"inv_{item}"):
            del st.session_state.inventory[item]; st.rerun()

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

# --- 10. EXPENSES (Dropdown) ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    exp_cats = ["Rent", "Electricity", "Salary", "Tea/Snacks", "Other"]
    with st.form("exp_form"):
        cat = st.selectbox("Category", exp_cats); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
            st.rerun()
    for i, ex in enumerate(st.session_state.expenses):
        ca, cb = st.columns([4, 1])
        ca.write(f"{ex['Date']} | {ex['Category']} | ₹{ex['Amount']}")
        if cb.button("Delete", key=f"ex_{i}"):
            st.session_state.expenses.pop(i); st.rerun()
