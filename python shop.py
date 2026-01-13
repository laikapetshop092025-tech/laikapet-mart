import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Database setup (Saara data save karne ke liye)
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'ledger' not in st.session_state: st.session_state.ledger = []

# Sidebar Navigation (Saare Menu yahan dikhenge)
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Additional Settings"])

# 1. DASHBOARD
if menu == "📊 Dashboard":
    st.title("Business Overview")
    t_sale = sum(s['total'] for s in st.session_state.sales)
    t_profit = sum(s['profit'] for s in st.session_state.sales)
    t_exp = sum(e['amount'] for e in st.session_state.expenses)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL SALES", f"Rs. {t_sale}")
    col2.metric("NET PROFIT", f"Rs. {t_profit - t_exp}")
    col3.metric("EXPENSES", f"Rs. {t_exp}")

# 2. BILLING
elif menu == "🧾 Billing":
    st.title("Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Stock Entry mein saaman add karein!")
    else:
        item = st.selectbox("Product", list(st.session_state.inventory.keys()))
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
    st.title("Stock Entry")
    with st.form("stock"):
        name = st.text_input("Item Name")
        buy = st.number_input("Purchase Price")
        sell = st.number_input("Selling Price")
        if st.form_submit_button("Add to Stock"):
            st.session_state.inventory[name] = {"p_price": buy, "s_price": sell}
            st.success(f"{name} added!")

# 4. UDHAAR TRACKER
elif menu == "💸 Udhaar Tracker":
    st.title("Udhaar Register")
    cust = st.text_input("Customer Name")
    amt = st.number_input("Udhaar Amount")
    if st.button("Save Udhaar"):
        st.session_state.ledger.append({"name": cust, "amount": amt, "date": datetime.now()})
        st.info("Udhaar Saved!")

# 5. EXPENSE MANAGER
elif menu == "💰 Expense Manager":
    st.title("Expenses")
    desc = st.text_input("Expense Reason")
    e_amt = st.number_input("Amount Paid")
    if st.button("Save Expense"):
        st.session_state.expenses.append({"desc": desc, "amount": e_amt, "date": datetime.now()})
        st.success("Expense Recorded!")

# 6. ADDITIONAL SETTINGS
elif menu == "⚙️ Additional Settings":
    st.title("Settings")
    st.write("Admin: Ayush Saxena")
    if st.button("Clear All Data"):
        st.session_state.clear()
        st.warning("Data cleared!")
