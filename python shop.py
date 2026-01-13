import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration (No changes here)
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- LOGIN & USER SYSTEM (Adding back) ---
if 'users' not in st.session_state:
    st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""

def check_login():
    u = st.session_state.user_input
    p = st.session_state.pass_input
    if u in st.session_state.users and st.session_state.users[u] == p:
        st.session_state.logged_in = True
        st.session_state.current_user = u
    else:
        st.error("Galt ID ya Password!")

if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    st.text_input("Username/ID", key="user_input")
    st.text_input("Password", type="password", key="pass_input")
    st.button("Login", on_click=check_login)
    st.stop()

# --- DATABASE SETUP (Keeping your data safe) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'ledger' not in st.session_state: st.session_state.ledger = []

# Sidebar Menu (Added Logout here)
st.sidebar.title("🐾 LAIKA PET MART")
st.sidebar.write(f"User: *{st.session_state.current_user}*")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# 1. DASHBOARD
if menu == "📊 Dashboard":
    st.title("Business Overview")
    t_sale = sum(s['total'] for s in st.session_state.sales)
    t_profit = sum(s['profit'] for s in st.session_state.sales)
    t_exp = sum(e['amt'] for e in st.session_state.expenses)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"Rs. {t_sale}")
    col2.metric("GROSS PROFIT", f"Rs. {t_profit}")
    col3.metric("EXPENSES", f"Rs. {t_exp}")
    col4.metric("NET PROFIT", f"Rs. {t_profit - t_exp}")

# 2. BILLING
elif menu == "🧾 Billing":
    st.title("Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Stock Entry mein saaman add karein!")
    else:
        item = st.selectbox("Product Chunein", list(st.session_state.inventory.keys()))
        qty = st.number_input("Quantity", min_value=1)
        rate = st.number_input("Selling Price", value=float(st.session_state.inventory[item]['s_price']))
        if st.button("Generate Bill"):
            buy_p = st.session_state.inventory[item]['p_price']
            total = qty * rate
            profit = (rate - buy_p) * qty
            st.session_state.sales.append({"item": item, "total": total, "profit": profit, "date": datetime.now()})
            st.success(f"Bill Generated: Rs. {total}")

# 3. STOCK ENTRY
elif menu == "📦 Stock Entry":
    st.title("Stock Management")
    with st.form("stock_form"):
        name = st.text_input("Item Name")
        buy = st.number_input("Purchase Price")
        sell = st.number_input("Selling Price")
        if st.form_submit_button("Add Stock"):
            st.session_state.inventory[name] = {"p_price": buy, "s_price": sell}
            st.success(f"{name} added!")

# 4. UDHAAR TRACKER
elif menu == "💸 Udhaar Tracker":
    st.title("Udhaar Register")
    cust = st.text_input("Customer Name")
    amt = st.number_input("Amount")
    if st.button("Save Udhaar"):
        st.session_state.ledger.append({"name": cust, "amount": amt, "date": datetime.now()})
        st.info("Udhaar Saved!")

# 5. EXPENSE MANAGER
elif menu == "💰 Expense Manager":
    st.title("Expense Tracker")
    reason = st.text_input("Kharcha Kahan Hua?")
    e_amt = st.number_input("Amount", min_value=0)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"reason": reason, "amt": e_amt, "date": datetime.now()})
        st.success("Expense Recorded!")

# 6. SETTINGS
elif menu == "⚙️ Settings":
    st.title("Admin Settings")
    st.subheader("Add New ID")
    new_id = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Create"):
        if new_id and new_pass:
            st.session_state.users[new_id] = new_pass
            st.success(f"ID '{new_id}' created!")
