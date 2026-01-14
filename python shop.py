import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- SETTINGS: Website ka naam aur page set karna ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATABASE: Saara data save karne ki jagah ---
if 'shop_name' not in st.session_state: st.session_state.shop_name = "LAIKA PET MART"
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN: Password system ---
if not st.session_state.logged_in:
    st.title(f"🔐 {st.session_state.shop_name} - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Galt ID ya Password!")
    st.stop()

# --- SIDEBAR: Menu Buttons ---
st.sidebar.title(f"🐾 {st.session_state.shop_name}")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD: Sabhi hisab ek jagah ---
if menu == "📊 Dashboard":
    st.title(f"📊 {st.session_state.shop_name} Dashboard")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_pur = sum(v['p_price'] * v['qty'] for v in st.session_state.inventory.values())
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    # Profit calculation: Sales - (Cost of Goods Sold) - Expenses
    net_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"Rs. {t_sales}")
    col2.metric("TOTAL PURCHASE", f"Rs. {t_pur}")
    col3.metric("NET PROFIT", f"Rs. {net_profit}")
    col4.metric("PETS SOLD", f"{len(st.session_state.pet_records)}")

# --- 2. BILLING: Saaman bechna aur stock kam karna ---
elif menu == "🧾 Billing":
    st.title("Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein saaman add karein!")
    else:
        with st.form("bill_form", clear_on_submit=True):
            item = st.selectbox("Product Chunein", list(st.session_state.inventory.keys()))
            avail = st.session_state.inventory[item]['qty']
            st.write(f"Available Stock: {avail}")
            qty = st.number_input("Bechne wali Quantity", min_value=0.1, max_value=float(avail) if avail > 0 else 0.1)
            rate = st.number_input("Kis Rate par Becha (Selling Price)", min_value=0.0)
            
            if st.form_submit_button("Generate Bill (Enter)"):
                if qty <= avail:
                    st.session_state.inventory[item]['qty'] -= qty
                    total = qty * rate
                    cost = qty * st.session_state.inventory[item]['p_price']
                    profit = total - cost
                    st.session_state.sales.append({"item": item, "total": total, "profit": profit, "date": datetime.now()})
                    st.success(f"Bill Saved: Rs. {total}")
                else:
                    st.error("Stock kam hai!")

# --- 3. LIVE STOCK: Dukan mein kitna maal bacha hai ---
elif menu == "📋 Live Stock":
    st.title("Current Inventory (Live Stock)")
    if st.session_state.inventory:
        # Table banane ke liye data set karna
        stock_data = []
        for name, details in st.session_state.inventory.items():
            stock_data.append({
                "Item Name": name,
                "Buy Rate": details['p_price'],
                "Available Qty": details['qty'],
                "Stock Value": details['p_price'] * details['qty']
            })
        st.table(pd.DataFrame(stock_data))
    else:
        st.info("Stock khali hai.")

# --- 4. EXPENSES: Kharcha likhne ke liye ---
elif menu == "💰 Expenses":
    st.title("Expense Register")
    with st.form("exp_form", clear_on_submit=True):
        res = st.text_input("Kharcha Kahan Hua?")
        amt = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save Expense (Enter)"):
            st.session_state.expenses.append({"Reason": res, "Amount": amt, "Date": datetime.now()})
            st.success("Kharcha save ho gaya!")
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# (Pet Sales Register, Purchase aur Admin Settings ka purana code niche rahega)
