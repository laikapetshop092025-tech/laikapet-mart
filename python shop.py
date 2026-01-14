import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PROFESSIONAL UI SETUP ---
st.set_page_config(page_title="LAIKA PET MART - PRO", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

# --- DATA INITIALIZATION ---
if 'shop_name' not in st.session_state: st.session_state.shop_name = "LAIKA PET MART"
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title(f"🔐 {st.session_state.shop_name}")
    with st.form("login_pro"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("ENTER SYSTEM"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.header(f"🐾 {st.session_state.shop_name}")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales & Vaccine", "🧾 Billing Terminal", "📦 Purchase & Inventory", "📋 Stock Report", "💰 Expense Tracker", "⚙️ Admin Panel"])

if st.sidebar.button("LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Analytics")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", f"₹{t_sales:,.2f}")
    c2.metric("Pets Sold", len(st.session_state.pet_records))
    c3.metric("Net Profit", f"₹{t_prof:,.2f}")
    c4.metric("Expenses", f"₹{t_exp:,.2f}")

# --- 2. PET SALES REGISTER ---
elif menu == "🐾 Pet Sales & Vaccine":
    st.title("🐾 Pet Lifecycle Tracking")
    with st.form("pet_sale_pro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
            breed = st.text_input("Pet Breed/Type")
        with col2:
            v_name = st.text_input("Vaccine Given")
            next_v = st.date_input("Next Due Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Pet": breed, "Next Due": next_vac})
            st.success("Record Captured Successfully!")
    if st.session_state.pet_records:
        st.dataframe(pd.DataFrame(st.session_state.pet_records), use_container_width=True)

# --- 3. PURCHASE (Unit System Added) ---
elif menu == "📦 Purchase & Inventory":
    st.title("📦 Inventory Procurement")
    with st.form("pur_pro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name (e.g., Dog Belt or Royal Canin)")
            unit = st.selectbox("Unit Type", ["KG (Weight)", "PCS (Quantity)"])
        with col2:
            buy_rate = st.number_input("Purchase Price (Per Unit)", min_value=0.0)
            stock_qty = st.number_input("Total Quantity/Weight Received", min_value=0.0)
        
        if st.form_submit_button("ADD TO WAREHOUSE"):
            if n:
                if n in st.session_state.inventory:
                    st.session_state.inventory[n]['qty'] += stock_qty
                else:
                    st.session_state.inventory[n] = {'p_price': buy_rate, 'qty': stock_qty, 'unit': unit}
                st.success(f"Stock Updated: {n} ({stock_qty} {unit} added)")

# --- 4. BILLING TERMINAL ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 POS Terminal")
    if not st.session_state.inventory:
        st.warning("Inventory is empty! Please add stock first.")
    else:
        with st.form("bill_pro", clear_on_submit=True):
            item_sel = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            unit_type = st.session_state.inventory[item_sel]['unit']
            st.info(f"Available: {st.session_state.inventory[item_sel]['qty']} {unit_type}")
            
            c1, c2 = st.columns(2)
            with c1:
                q_sell = st.number_input(f"Selling {unit_type}", min_value=0.01)
            with c2:
                s_price = st.number_input("Selling Price (Unit Rate)", min_value=0.0)
            
            if st.form_submit_button("GENERATE INVOICE"):
                if q_sell <= st.session_state.inventory[item_sel]['qty']:
                    st.session_state.inventory[item_sel]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - st.session_state.inventory[item_sel]['p_price']) * q_sell
                    st.session_state.sales.append({"total": total, "profit": profit, "item": item_sel, "qty": q_sell, "date": datetime.now()})
                    st.success(f"Invoice Created: ₹{total:,.2f}")
                else:
                    st.error("Insufficient Stock!")
