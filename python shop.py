import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Custom Styling for Logo
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Pet Shop Management System</p>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Fixing KeyErrors & NameErrors) ---
# Ensuring all keys exist so software never crashes
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("### 🔐 User Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
        else:
            st.error("Galat ID ya Password! Kripya sahi detail bhariye.")
    st.stop()

# --- 4. SIDEBAR MENU & LOGOUT ---
st.sidebar.title(f"👤 {st.session_state.current_user}")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard & Reports", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal (Bechna)", 
    "📦 Purchase (Maal Lana)", 
    "📋 Live Stock Inventory", 
    "💰 Expense Tracker", 
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD & EXCEL EXPORT ---
if menu == "📊 Dashboard & Reports":
    st.title("📊 Business Performance")
    t_sales = sum(s.get('Total', 0) for s in st.session_state.sales)
    t_prof = sum(s.get('Profit', 0) for s in st.session_state.sales) - sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    col1, col2 = st.columns(2)
    col1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    col2.metric("NET PROFIT", f"₹{int(t_prof)}")

    st.write("---")
    st.subheader("📥 Download Data (Excel)")
    if st.session_state.sales:
        df_sales = pd.DataFrame(st.session_state.sales)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_sales.to_excel(writer, index=False)
        st.download_button("📥 Download Sales Report", data=buffer.getvalue(), file_name="Sales_Report.xlsx")

# --- 6. PET SALES REGISTER (Age, Weight, Vaccine Fix) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Indie", "Persian Cat", "Other"]
    # Fixed NameError by using proper form scoping
    with st.form("pet_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Customer Name")
            p_phone = st.text_input("Phone Number")
            p_breed = st.selectbox("Select Breed", breeds)
        with col2:
            p_age = st.text_input("Pet Age (e.g., 2 Months)")
            p_weight = st.text_input("Pet Weight (e.g., 5 KG)")
            p_next_v = st.date_input("Next Vaccine Date", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({
                "Date": datetime.now().date(), "Customer": p_name, "Phone": p_phone, 
                "Breed": p_breed, "Age": p_age, "Weight": p_weight, "Next Due": p_next_v
            })
            st.success("Record Saved Successfully!")
            
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING TERMINAL (Dropdown & Unit Logic) ---
elif menu == "🧾 Billing Terminal (Bechna)":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein maal add karein!")
    else:
        with st.form("billing_terminal_form", clear_on_submit=True):
            # Automated Dropdown from Inventory
            item_sel = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
            inv_info = st.session_state.inventory[item_sel]
            
            st.info(f"Dukan mein bacha hai: {inv_info.get('qty', 0)} {inv_info.get('unit', 'Unit')}")
            
            c1, c2, c3 = st.columns(3)
            with c1: b_unit = st.selectbox("Selling Unit", ["KG", "PCS", "Packet"])
            with c2: b_qty = st.number_input("Selling Qty", min_value=0.01, step=0.1)
            with c3: b_rate = st.number_input("Selling Rate (₹)", min_value=1, step=1)
            
            b_cust = st.text_input("Customer Name")
            
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                avail = inv_info.get('qty', 0)
                if b_qty <= avail:
                    st.session_state.inventory[item_sel]['qty'] -= b_qty
                    total_amt = b_qty * b_rate
                    profit_amt = (b_rate - inv_info.get('p_price', 0)) * b_qty
                    st.session_state.sales.append({
                        "Date": datetime.now().date(), "Customer": b_cust, "Item": item_sel, 
                        "Qty": b_qty, "Unit": b_unit, "Total": total_amt, "Profit": profit_amt
                    })
                    st.success(f"Bik gaya! Bill: ₹{total_amt}")
                    st.markdown(f"### 📄 BILL SUMMARY\n*Item:* {item_sel} | *Total:* ₹{total_amt}")
                else:
                    st.error(f"Stock kam hai! Sirf {avail} bacha hai.")

# --- 8. PURCHASE & 9. LIVE STOCK (Fixing Display Errors) ---
elif menu == "📦 Purchase (Maal Lana)":
    st.title("📦 Procurement / Stock Entry")
    with st.form("purchase_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            p_n = st.text_input("Item Name")
            p_u = st.selectbox("Select Unit", ["KG", "PCS", "Packet"])
        with col2:
            p_r = st.number_input("Purchase Price (₹)", min_value=1)
            p_q = st.number_input("Quantity Received", min_value=1)
        if st.form_submit_button("Add to Stock"):
            if p_n in st.session_state.inventory: st.session_state.inventory[p_n]['qty'] += p_q
            else: st.session_state.inventory[p_n] = {'p_price': p_r, 'qty': p_q, 'unit': p_u}
            st.success("Stock Updated!")
    
    if st.session_state.inventory:
        st.subheader("📋 Stock Entry History")
        # Fixed ValueError using manual list comprehension
        h_data = [{"Item": k, "Buy Rate": v.get('p_price',0), "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(h_data))

elif menu == "📋 Live Stock Inventory":
    st.title("📋 Current Inventory Report")
    if st.session_state.inventory:
        # Fixed Live Stock Error
        st_data = [{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit'), "Value": v.get('qty',0)*v.get('p_price',0)} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(st_data))
    else: st.info("Stock Khali Hai.")

# --- 10. EXPENSES & 11. ADMIN ---
elif menu == "💰 Expense Tracker":
    st.title("💰 Business Expenses")
    with st.form("expense_form"):
        e_r = st.text_input("Expense Reason")
        e_a = st.number_input("Amount (₹)", min_value=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": e_r, "Amount": e_a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Account Management")
    if st.session_state.current_user == "Laika":
        new_id = st.text_input("New Staff ID")
        new_pass = st.text_input("New Password")
        if st.button("Create Account"):
            st.session_state.users[new_id] = new_pass
            st.success(f"ID '{new_id}' ban gayi!")
        st.write("Current IDs:", list(st.session_state.users.keys()))
    else: st.error("Sirf Admin Access!")
