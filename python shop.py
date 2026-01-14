import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATA INITIALIZATION (Ensuring no crash) ---
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
st.sidebar.title("🐾 MENU")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Sales Entry (Bechna)", "📦 Purchase (Maal Lana)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

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
    c1.metric("TOTAL SALES", f"₹{total_sales:,.0f}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{total_profit:,.0f}")
    c4.metric("EXPENSES", f"₹{total_exp:,.0f}")

# --- 6. ADVANCED PET REGISTER (Weight, Age, Vaccine) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Lifecycle & Health Record")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
            breed_sel = st.selectbox("Select Breed", breeds)
        with col2:
            age = st.text_input("Pet Age (e.g., 2 Months)")
            weight = st.text_input("Pet Weight (e.g., 5 KG)")
            next_v = st.date_input("Next Vaccine Date", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({
                "Date": datetime.now().date(), "Customer": name, "Phone": phone, 
                "Breed": breed_sel, "Age": age, "Weight": weight, "Next Vaccine": next_v
            })
            st.success("Record Saved!")
    
    if st.session_state.pet_records:
        st.write("### Purane Records")
        st.dataframe(pd.DataFrame(st.session_state.pet_records), use_container_width=True)

# --- 7. SIMPLE SALES ENTRY (Bechna) ---
elif menu == "🧾 Sales Entry (Bechna)":
    st.title("🧾 Bechna / Sales Entry")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_f", clear_on_submit=True):
            item = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            u_type = info.get('unit', 'Unit')
            avail = info.get('qty', 0)
            st.info(f"Available Stock: {avail} {u_type}")
            
            c1, c2 = st.columns(2)
            with c1: q_sell = st.number_input(f"Bechni wali Qty ({u_type})", min_value=0.01)
            with c2: s_price = st.number_input("Rate (Per Unit)", min_value=1, step=1)
            
            if st.form_submit_button("SAVE SALE"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - info.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "qty": q_sell, "unit": u_type})
                    st.success(f"Sale Done! ₹{total}")
                else: st.error("Stock Kam Hai!")

# --- 8. PURCHASE & 9. LIVE STOCK ---
elif menu == "📦 Purchase (Maal Lana)":
    st.title("📦 Add New Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price", min_value=1, step=1)
            q = st.number_input("Total Quantity", min_value=1, step=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Updated!")
    
    if st.session_state.inventory:
        st.write("### Current Stock List")
        st.table(pd.DataFrame([{"Item": k, "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Inventory")
    if st.session_state.inventory:
        st_data = [{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit'), "Value": v.get('qty',0)*v.get('p_price',0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))
    else: st.info("Stock Khali.")

# --- 10. EXPENSES & 11. SETTINGS ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Tracker")
    with st.form("exp"):
        r = st.text_input("Reason"); a = st.number_input("Amount", min_value=1, step=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Authority")
    if st.session_state.get('current_user') == "Laika" or True:
        new_u = st.text_input("New Staff ID")
        new_p = st.text_input("New Password")
        if st.button("Create Account"):
            st.session_state.users[new_u] = new_p
            st.success("ID Created!")
