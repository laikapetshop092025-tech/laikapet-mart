import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE SETUP: Website ka naam aur layout set karna ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATABASE: Saara data save rakhne ke liye ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- LOGIN: Password system ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- SIDEBAR: Menu Buttons ---
st.sidebar.title("🐾 MENU")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Billing)", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD: Sirf 4 main hisab ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"₹{t_sales:,.2f}")
    col2.metric("PETS SOLD", len(st.session_state.pet_records))
    col3.metric("NET PROFIT", f"₹{t_prof:,.2f}")
    col4.metric("EXPENSES", f"₹{t_exp:,.2f}")

# --- 2. PET SALES: Safed screen fix (Breed list ke saath) ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with c2:
            breed = st.selectbox("Select Breed", breeds)
            next_v = st.date_input("Next Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed, "Due": next_v})
            st.success("Pet Record Saved!")
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 3. SALES ENTRY & BILLING: KG/PCS hisab aur Bill Generate ---
elif menu == "🧾 Sales Entry (Billing)":
    st.title("🧾 Bechna aur Bill Generate")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_f"):
            item = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            u_type = info.get('unit', 'Unit')
            avail = info.get('qty', 0)
            
            st.info(f"Dukan mein bacha hai: {avail} {u_type}")
            
            c1, c2 = st.columns(2)
            with c1: q_sell = st.number_input(f"Kitna becha? ({u_type})", min_value=0.01)
            with c2: s_price = st.number_input("Selling Price (Rate)", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - info.get('p_price', 0)) * q_sell
                    sale_entry = {"Item": item, "total": total, "profit": profit, "qty": q_sell, "unit": u_type, "Date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                    st.session_state.sales.append(sale_entry)
                    
                    st.success(f"Sale Done! ₹{total}")
                    st.markdown("### 📄 CUSTOMER BILL")
                    st.write(f"*Item:* {item} | *Qty:* {q_sell} {u_type}")
                    st.write(f"*Total Amount:* ₹{total}")
                    st.markdown("---")
                else: st.error("Stock Kam Hai!")

# --- 4. PURCHASE: Stock Chadana (Niche list ke saath) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add New Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price (Khareed)", min_value=0.0)
            q = st.number_input("Total Quantity", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    st.subheader("📋 Stock List")
    if st.session_state.inventory:
        data = [{"Item": k, "Buy Rate": v['p_price'], "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# --- 5. LIVE STOCK: Safed screen fix ---
elif menu == "📋 Live Stock":
    st.title("📋 Current Live Stock")
    if st.session_state.inventory:
        st_data = [{"Item": k, "Available": v.get('qty', 0), "Unit": v.get('unit', 'Unit'), "Value": v.get('qty', 0) * v.get('p_price', 0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))
    else: st.info("Stock Khali Hai.")

# --- 6. EXPENSES: Safed screen fix ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Tracker")
    with st.form("exp_f", clear_on_submit=True):
        r = st.text_input("Kharcha Detail")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("SAVE EXPENSE"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. SETTINGS: Admin settings fix ---
elif menu == "⚙️ Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.get('current_user') == "Laika":
        new_u = st.text_input("New Staff ID")
        new_p = st.text_input("New Password")
        if st.button("Create ID"):
            st.session_state.users[new_u] = new_p
            st.success("ID Created!")
    else: st.warning("Only Admin (Laika) can access this.")
