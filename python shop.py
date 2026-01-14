import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA INITIALIZATION (Ensuring no KeyError) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- SIDEBAR MENU ---
st.sidebar.title("🐾 MENU")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Billing)", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

# --- 1. DASHBOARD ---
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

# --- 2. PET SALES (No more Blank Screen) ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with col2:
            breed_sel = st.selectbox("Select Breed", breeds)
            next_v = st.date_input("Next Due Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed_sel, "Due": next_v})
            st.success("Record Saved!")
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 3. SALES ENTRY & BILLING (Theek hisab + Invoice) ---
elif menu == "🧾 Sales Entry (Billing)":
    st.title("🧾 Sales Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_f"):
            item = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            u_type = info.get('unit', 'Unit')
            avail = info.get('qty', 0)
            st.info(f"Available Stock: {avail} {u_type}")
            
            c1, c2 = st.columns(2)
            with c1: q_sell = st.number_input(f"Bechni wali Qty ({u_type})", min_value=0.01)
            with c2: s_price = st.number_input("Rate (Per Unit)", min_value=0.0)
            
            if st.form_submit_button("GENERATE BILL"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - info.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "qty": q_sell, "unit": u_type})
                    
                    # Visual Bill
                    st.success(f"Sale Done! ₹{total}")
                    st.markdown(f"### 📄 BILL: {item}")
                    st.write(f"Qty: {q_sell} {u_type} | Rate: ₹{s_price} | *Total: ₹{total}*")
                else: st.error("Stock Kam Hai!")

# --- 4. PURCHASE (History Display Fix) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Procurement")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Rate", min_value=0.0)
            q = st.number_input("Total Quantity", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Updated!")
    
    st.subheader("📋 Stock List")
    if st.session_state.inventory:
        # Manual list to avoid KeyError: 'unit' from old data
        data = [{"Item": k, "Buy Rate": v.get('p_price',0), "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# --- 5. LIVE STOCK (Error-Proof Table) ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Inventory")
    if st.session_state.inventory:
        st_data = [{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit'), "Value": v.get('qty',0)*v.get('p_price',0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))
    else: st.info("No Stock.")

# --- 6. EXPENSES & 7. SETTINGS ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        r = st.text_input("Reason")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Settings":
    st.title("⚙️ Admin Authority")
    if st.session_state.get('current_user') == "Laika":
        new_u = st.text_input("New Staff ID")
        new_p = st.text_input("New Password")
        if st.button("Create"):
            st.session_state.users[new_u] = new_p
            st.success("ID Created!")
