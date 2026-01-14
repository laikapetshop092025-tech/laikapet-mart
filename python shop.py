import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Logo ki jagah (Yahan aap apna logo laga sakte hain)
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Pet Shop Management System</p>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Proof Logic) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("### 🔐 Login Karein")
    with st.container():
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
            else:
                st.error("Galat ID ya Password!")
    st.stop()

# --- 4. SIDEBAR MENU & LOGOUT ---
st.sidebar.title(f"👤 User: {st.session_state.current_user}")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Sales Entry (Bechna)", 
    "📦 Purchase (Maal Lana)", 
    "📋 Live Stock", 
    "💰 Expenses", 
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
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

# --- 6. PET SALES REGISTER (Age, Weight, Vaccine Columns) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration & History")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Indie/Desi", "Persian Cat", "Siamese Cat", "Other"]
    
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
            st.success("Pet Record Saved!")
            
    if st.session_state.pet_records:
        st.write("### Sabhi Pets Ka Data")
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. SALES ENTRY (Simple & Billing) ---
elif menu == "🧾 Sales Entry (Bechna)":
    st.title("🧾 Bechna / Billing")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_f", clear_on_submit=True):
            item = st.selectbox("Item Chunein", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            u_type = info.get('unit', 'Unit')
            avail = info.get('qty', 0)
            st.info(f"Dukan mein bacha hai: {avail} {u_type}")
            
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Bechne wali Unit", ["KG", "PCS"])
            with c2: q_sell = st.number_input(f"Kitna becha?", min_value=1, step=1, value=1)
            with c3: s_price = st.number_input("Rate (₹)", min_value=1, step=1, value=100)
            
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - info.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "qty": q_sell, "unit": u_sell, "Date": datetime.now().date()})
                    
                    st.success(f"Sale Done! ₹{total}")
                    st.markdown("### 📄 BILL")
                    st.write(f"*Item:* {item} | *Qty:* {q_sell} {u_sell} | *Total:* ₹{total}")
                else: st.error("Stock Kam Hai!")

# --- 8. PURCHASE (Maal Lana) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Naya Maal Chadhana")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit Chunein", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Khareed Rate (₹)", min_value=1, step=1, value=10)
            q = st.number_input("Quantity/Weight", min_value=1, step=1, value=10)
        if st.form_submit_button("ADD TO STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Updated!")
    
    if st.session_state.inventory:
        st.subheader("📋 Stock List")
        st.table(pd.DataFrame([{"Item": k, "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

# --- 9. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory Status")
    if st.session_state.inventory:
        st_data = [{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit'), "Value": v.get('qty',0)*v.get('p_price',0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))
    else: st.info("Stock Khali Hai.")

# --- 10. EXPENSES ---
elif menu == "💰 Expenses":
    st.title("💰 Kharcha Tracker")
    with st.form("exp_f"):
        reason = st.text_input("Detail"); amt = st.number_input("Amount", min_value=1, step=1)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Reason": reason, "Amount": amt, "Date": datetime.now().date()})
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# --- 11. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Authority Control")
    if st.session_state.current_user == "Laika":
        st.subheader("Staff Accounts Banayein")
        new_u = st.text_input("New ID")
        new_p = st.text_input("New Password")
        if st.button("Create Staff Account"):
            st.session_state.users[new_u] = new_p
            st.success(f"ID '{new_u}' ban gayi!")
        
        st.write("---")
        st.write("Current IDs:", list(st.session_state.users.keys()))
    else:
        st.error("Sirf Admin (Laika) hi naye account bana sakta hai.")
