import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATA INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 4. SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Bechna)", "📦 Purchase (Maal Lana)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    total_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    total_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    total_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - total_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{total_sales:,.2f}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{total_profit:,.2f}")
    c4.metric("EXPENSES", f"₹{total_exp:,.2f}")

# --- 6. SALES ENTRY (Kg aur Packet Unit ke Saath) ---
elif menu == "🧾 Sales Entry (Bechna)":
    st.title("🧾 Bechna / Sales Entry")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_form", clear_on_submit=True):
            # Item select karte hi uski unit dikhegi
            item = st.selectbox("Kaunsa Item Becha?", list(st.session_state.inventory.keys()))
            
            # Unit aur Stock ki jankari nikalna
            info = st.session_state.inventory[item]
            avail = info.get('qty', 0)
            u_type = info.get('unit', 'Unit') # KG ya Packet yahan se aayega
            buy_rate = info.get('p_price', 0)
            
            st.info(f"Dukan mein bacha hai: *{avail} {u_type}*")
            
            c1, c2 = st.columns(2)
            with c1:
                # Yahan aapse unit ke hisab se quantity poochega
                qty_s = st.number_input(f"Kitna becha? (Kilo/Packet: {u_type})", min_value=0.01)
            with c2:
                s_price = st.number_input(f"Selling Price (Rate per {u_type})", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if qty_s <= avail:
                    st.session_state.inventory[item]['qty'] -= qty_s
                    total_amt = qty_s * s_price
                    profit_amt = (s_price - buy_rate) * qty_s
                    st.session_state.sales.append({
                        "Item": item, 
                        "total": total_amt, 
                        "profit": profit_amt, 
                        "Qty": qty_s, 
                        "Unit": u_type, # Unit save ho rahi hai
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.success(f"Bik gaya! ₹{total_amt} Stock se minus ho gaya.")
                else:
                    st.error(f"Stock kam hai! Sirf {avail} {u_type} bacha hai.")

# --- 7. PURCHASE (Unit Set Karna) ---
elif menu == "📦 Purchase (Maal Lana)":
    st.title("📦 Add New Stock")
    with st.form("pur_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit Chunein", ["KG", "Packet/PCS"]) # Yahan unit set hogi
        with col2:
            rate = st.number_input("Khareed Rate (Per KG/Packet)", min_value=0.0)
            q = st.number_input("Total Quantity/Weight", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory:
                st.session_state.inventory[n]['qty'] += q
            else:
                st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success(f"{n} Stock mein jud gaya!")
