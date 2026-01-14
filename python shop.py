import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Setup: App ka naam aur choudaai set karna ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- Database Initialization: Data ko save rakhne ke liye ---
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- Login System: Suraksha ke liye ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- Sidebar: Menu Buttons ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales & Vaccine", "🧾 Sales Entry (Bechna)", "📦 Purchase (Maal Lana)", "📋 Live Stock", "💰 Expense Manager", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. Dashboard: Business Summary ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{t_sales:,.2f}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{t_prof:,.2f}")
    c4.metric("EXPENSES", f"₹{t_exp:,.2f}")

# --- 2. Pet Sales: Janwar ka record ---
elif menu == "🐾 Pet Sales & Vaccine":
    st.title("🐾 Pet Lifecycle Record")
    with st.form("pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with c2:
            pet = st.text_input("Pet Breed/Type")
            next_v = st.date_input("Agli Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Pet": pet, "Next Due": next_v})
            st.success("Record Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 3. Sales Entry: Maal bechna (Billing ki jagah) ---
elif menu == "🧾 Sales Entry (Bechna)":
    st.title("🧾 Sales Entry")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("sale_f", clear_on_submit=True):
            item_sel = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            u_type = st.session_state.inventory[item_sel].get('unit', 'Unit')
            avail = st.session_state.inventory[item_sel]['qty']
            st.info(f"Available Stock: {avail} {u_type}")
            
            c1, c2 = st.columns(2)
            with c1: q_sell = st.number_input(f"Selling Qty ({u_type})", min_value=0.01)
            with c2: s_price = st.number_input("Selling Price (Kis rate par becha)", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if q_sell <= avail:
                    st.session_state.inventory[item_sel]['qty'] -= q_sell
                    total = q_sell * s_price
                    # Profit: (Bechne ka rate - Khareed ka rate) * Quantity
                    profit = (s_price - st.session_state.inventory[item_sel]['p_price']) * q_sell
                    st.session_state.sales.append({"item": item_sel, "total": total, "profit": profit, "qty": q_sell, "date": datetime.now()})
                    st.success(f"Sale Done! ₹{total} Stock se minus ho gaya.")
                else: st.error("Itna Stock nahi hai!")

# --- 4. Purchase: Maal dukan mein lana ---
elif menu == "📦 Purchase (Maal Lana)":
    st.title("📦 Purchase Entry")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            unit = st.selectbox("Unit Type", ["KG", "PCS"])
        with col2:
            buy_p = st.number_input("Purchase Price (Khareed Rate)", min_value=0.0)
            qty = st.number_input("Quantity/Weight", min_value=0.0)
        if st.form_submit_button("ADD TO STOCK"):
            if n:
                if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += qty
                else: st.session_state.inventory[n] = {'p_price': buy_p, 'qty': qty, 'unit': unit}
                st.success(f"{n} added to Live Stock!")

# --- 5. Live Stock: Kitna maal bacha hai ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Report")
    if st.session_state.inventory:
        df = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index()
        df.columns = ['Item Name', 'Buy Rate', 'Available Qty', 'Unit']
        st.table(df)
    else: st.info("Stock Khali Hai.")

# --- 6. Expense Manager: Daily Kharcha ---
elif menu == "💰 Expense Manager":
    st.title("💰 Expense Tracker")
    with st.form("exp_f", clear_on_submit=True):
        res = st.text_input("Kharcha Detail")
        amt = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("SAVE EXPENSE"):
            st.session_state.expenses.append({"Reason": res, "Amount": amt, "Date": datetime.now().date()})
            st.success("Expense Saved!")
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. Admin Settings: Password & ID Control ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Authority Settings")
    if st.session_state.current_user == "Laika":
        u = st.text_input("New Staff Username")
        p = st.text_input("New Password", type="password")
        if st.button("CREATE STAFF ID"):
            st.session_state.users[u] = p
            st.success(f"ID '{u}' Created!")
    else: st.warning("Only Admin (Laika) can access this.")
