import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATABASE INITIALIZATION ---
# Ismein users ki list hai, Admin ka default password wahi hai jo aapne bataya tha.
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: 
    st.session_state.users = {"Laika": "Ayush@092025"} # Default Admin
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    with st.container():
        u = st.text_input("Username (Staff ya Admin ID)")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.success(f"Welcome {u}!")
                st.rerun()
            else:
                st.error("Galat Username ya Password!")
    st.stop()

# --- 4. SIDEBAR & LOGOUT ---
st.sidebar.title(f"👤 {st.session_state.current_user}")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Billing)", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 LOGOUT"):
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.rerun()

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{int(t_sales)}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{int(t_prof)}")
    c4.metric("EXPENSES", f"₹{int(t_exp)}")

# --- 6. PET SALES (With Breed Dropdown) ---
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
            next_v = st.date_input("Next Vaccine Due", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed_sel, "Due": next_v})
            st.success("Saved!")
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. SALES ENTRY & BILLING ---
elif menu == "🧾 Sales Entry (Billing)":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_f"):
            item = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            st.info(f"Available: {info['qty']} {info['unit']}")
            
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS"])
            with c2: q_sell = st.number_input("Qty", min_value=1, step=1)
            with c3: s_price = st.number_input("Rate (₹)", min_value=1, step=1)
            
            if st.form_submit_button("GENERATE BILL"):
                if q_sell <= info['qty']:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - info['p_price']) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "total": total, "profit": profit})
                    
                    st.markdown("---")
                    st.subheader("📄 INVOICE")
                    st.write(f"*Item:* {item} | *Total:* ₹{total}")
                    st.markdown("---")
                else: st.error("Stock Kam Hai!")

# --- 8. PURCHASE ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price", min_value=1, step=1)
            q = st.number_input("Quantity", min_value=1, step=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Updated!")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

# --- 9. ADMIN SETTINGS (Fixed) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Authority & Management")
    if st.session_state.current_user == "Laika":
        st.subheader("Manage Staff Accounts")
        with st.expander("➕ Add New Staff"):
            new_u = st.text_input("New Staff ID")
            new_p = st.text_input("New Staff Password")
            if st.button("Create Account"):
                if new_u and new_p:
                    st.session_state.users[new_u] = new_p
                    st.success(f"Account for {new_u} created!")
                else: st.warning("ID aur Password dono bhariye.")
        
        st.subheader("Current Accounts")
        st.write(list(st.session_state.users.keys()))
    else:
        st.error("Sirf Admin (Laika) hi is section ko dekh sakta hai.")

# --- LIVE STOCK & EXPENSES ---
elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory")
    st.table(pd.DataFrame([{"Item": k, "Qty": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        r = st.text_input("Detail"); a = st.number_input("Amount", min_value=1, step=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))
