import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# App ko full screen jaisa dikhane ke liye CSS
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION INITIALIZATION (Crash-Safe) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- 3. LOGIN LOGIC (FIXED) ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h2>", unsafe_allow_html=True)
    
    # Login fields (Bina form ke taaki button turant kaam kare)
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("LOGIN NOW"):
        if user_input == "Laika" and pass_input == "Ayush@092025":
            st.session_state.logged_in = True
            st.session_state.current_user = "Laika"
            st.success("Sahi hai! Dashboard khul raha hai...")
            st.rerun() # Refresh to show dashboard
        else:
            st.error("Ghalat ID ya Password! Phir se koshish karein.")
    st.stop() # Login hone tak niche ka code hide rahega

# --- 4. NAVIGATION (Login ke baad) ---
st.sidebar.markdown(f"### 🤝 Welcome, {st.session_state.current_user}!")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD & OTHER SECTIONS (Aapka Sahi wala code) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_rev = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_rev)}")
    c2.metric("EXPENSES", f"₹{int(t_exp)}")
    c3.metric("NET PROFIT", f"₹{int(t_prof)}")

    st.write("---")
    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel Report", csv, f"Sales_{datetime.now().date()}.csv", "text/csv")

# --- Baki ka Billing, Purchase, Pets code bilkul waisa hi hai ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing & Delete Options")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        # Billing Logic (With Auto-Stock Revert)
        with st.form("bill_final"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            c1, c2 = st.columns(2)
            with c1: q_sell = st.number_input("Quantity", min_value=0.01)
            with c2: r_sell = st.number_input("Rate (₹)", min_value=1)
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
        if cb.button("🗑️ Delete Bill", key=f"s_{idx}"):
            if s['Item'] in st.session_state.inventory:
                st.session_state.inventory[s['Item']]['qty'] += s['Qty']
            st.session_state.sales.pop(idx); st.rerun()

# --- Purchase Section ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_final"):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        rate = st.number_input("Buy Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u, 'Date': datetime.now().date()}
            st.rerun()
    for item, v in list(st.session_state.inventory.items()):
        ca, cb = st.columns([4, 1])
        ca.write(f"*{item}* | Stock: {v['qty']} {v['unit']}")
        if cb.button("Delete Item", key=f"inv_{item}"):
            del st.session_state.inventory[item]; st.rerun()

# --- Expenses with Dropdown ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    cats = ["Rent", "Electricity", "Staff Salary", "Tea/Snacks", "Other"]
    with st.form("exp_final"):
        cat = st.selectbox("Category", cats); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Date": datetime.now().date(), "Category": cat, "Amount": amt})
            st.rerun()
    for i, ex in enumerate(st.session_state.expenses):
        ca, cb = st.columns([4, 1])
        ca.write(f"{ex['Date']} | {ex['Category']} | ₹{ex['Amount']}")
        if cb.button("Delete", key=f"ex_{i}"):
            st.session_state.expenses.pop(i); st.rerun()

# --- Pet Sales Register ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Entry")
    with st.form("pet_final"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Customer"); breed = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2: age = st.text_input("Age"); weight = st.text_input("Weight"); dv = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Customer": name, "Breed": breed, "Due": dv})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- Live Stock ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))
