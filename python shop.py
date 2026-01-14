import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATA INITIALIZATION (Fixing errors by ensuring keys exist) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN LOGIC ---
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

# --- 4. SIDEBAR ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

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

# --- 6. PET SALES (With Large Breed List) ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Indie/Desi", "Persian Cat", "Siamese Cat", "Other"]
    with st.form("pet_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with col2:
            breed_sel = st.selectbox("Select Breed", breeds)
            next_v = st.date_input("Next Due", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed_sel, "Due": next_v})
            st.success("Record Saved!")
    if st.session_state.pet_records:
        st.dataframe(pd.DataFrame(st.session_state.pet_records), use_container_width=True)

# --- 7. PURCHASE (Fixes KeyError and Adds List) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add New Stock")
    with st.form("pur_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price", min_value=0.0)
            q = st.number_input("Quantity", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory:
                st.session_state.inventory[n]['qty'] += q
            else:
                st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success(f"{n} Added!")

    st.subheader("📋 Stock Entry History")
    if st.session_state.inventory:
        # Converting dict to list safely
        history_data = []
        for name, info in st.session_state.inventory.items():
            history_data.append({
                "Item Name": name, 
                "Buy Rate": info.get('p_price', 0), 
                "Current Qty": info.get('qty', 0), 
                "Unit": info.get('unit', 'KG/PCS')
            })
        st.table(pd.DataFrame(history_data))

# --- 8. SALES ENTRY (Fixes KeyError: 'unit') ---
elif menu == "🧾 Sales Entry":
    st.title("🧾 Make a Sale")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_form", clear_on_submit=True):
            item = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
            avail = st.session_state.inventory[item].get('qty', 0)
            unit_val = st.session_state.inventory[item].get('unit', 'Unit') # Fix for KeyError
            st.info(f"Stock Available: {avail} {unit_val}")
            
            qty_s = st.number_input(f"Quantity to Sell ({unit_val})", min_value=0.01)
            price_s = st.number_input("Selling Price", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if qty_s <= avail:
                    st.session_state.inventory[item]['qty'] -= qty_s
                    total = qty_s * price_s
                    profit = (price_s - st.session_state.inventory[item].get('p_price', 0)) * qty_s
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "Date": datetime.now()})
                    st.success(f"Sold! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")

# --- 9. LIVE STOCK (Fixes Live Stock Inventory Error) ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Inventory")
    if st.session_state.inventory:
        data_stock = []
        for k, v in st.session_state.inventory.items():
            data_stock.append({
                "Item": k, 
                "Qty": v.get('qty', 0), 
                "Unit": v.get('unit', 'N/A'), # Fix for KeyError
                "Value": v.get('qty', 0) * v.get('p_price', 0)
            })
        st.table(pd.DataFrame(data_stock))
    else: st.info("Stock Khali Hai.")

# --- 10. EXPENSES (Fixed Section) ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Manager")
    with st.form("exp_form"):
        r = st.text_input("Reason")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))
