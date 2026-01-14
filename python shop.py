import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Logo Section
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Pet Shop Management System</p>", unsafe_allow_html=True)

# --- 2. DATABASE INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("### 🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- 4. SIDEBAR MENU ---
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses", 
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD (Wapas Purana Wala) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    col2.metric("NET PROFIT", f"₹{int(t_prof)}")
    col3.metric("PETS SOLD", len(st.session_state.pet_records))

    st.write("---")
    st.subheader("📥 Download CSV Reports (Excel Compatible)")
    # Simple CSV download button jo har computer par chalega bina crash hue
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        st.download_button("📥 Download Sales Data", df_s.to_csv(index=False).encode('utf-8'), "Sales.csv", "text/csv")

# --- 6. PET SALES REGISTER ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Entry")
    with st.form("pet_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone Number")
        with c2:
            age = st.text_input("Age"); weight = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Age": age, "Weight": weight, "Due": dv})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING TERMINAL (Print Option Added) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("⚠️ Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            inv = st.session_state.inventory[item]
            st.info(f"Available: {inv.get('qty', 0)} {inv.get('unit', 'Unit')}")
            
            c1, c2, c3 = st.columns(3)
            with c1: u_sell = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sell = st.number_input("Quantity", min_value=0.01, step=0.1)
            with c3: r_sell = st.number_input("Rate (₹)", min_value=1, step=1)
            
            cust = st.text_input("Customer Name")
            generate = st.form_submit_button("COMPLETE SALE & SHOW BILL")
            
            if generate:
                if q_sell <= inv.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * r_sell
                    profit = (r_sell - inv.get('p_price', 0)) * q_sell
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": q_sell, "Unit": u_sell, "total": total, "profit": profit})
                    
                    st.markdown("---")
                    st.subheader("📄 INVOICE")
                    bill_content = f"""
                    *LAIKA PET MART*
                    Customer: {cust}
                    Item: {item}
                    Qty: {q_sell} {u_sell} | Rate: ₹{r_sell}
                    TOTAL AMOUNT: ₹{total}
                    """
                    st.write(bill_content)
                    st.info("💡 Tip: PC par 'Ctrl + P' dabakar aap is bill ka print nikaal sakte hain.")
                else: st.error("Stock Kam Hai!")

# --- 8. PURCHASE & 9. LIVE STOCK ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Entry")
    with st.form("pur_f", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u}
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

# --- 10. EXPENSES & 11. ADMIN ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        r = st.text_input("Reason"); a = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        u = st.text_input("New ID"); p = st.text_input("New Password")
        if st.button("Create Account"): st.session_state.users[u] = p; st.success("Done!")
