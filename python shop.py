import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION (Crash-Proof) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    u = st.text_input("Username"); p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True; st.session_state.current_user = u; st.rerun()
    st.stop()

# --- 4. SIDEBAR MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard & Excel", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# --- 5. DASHBOARD & EXCEL REPORTS ---
if menu == "📊 Dashboard & Excel":
    st.title("📊 Business Reports")
    t_sales = sum(s.get('Total', 0) for s in st.session_state.sales)
    t_prof = sum(s.get('Profit', 0) for s in st.session_state.sales) - sum(e.get('Amount', 0) for e in st.session_state.expenses)
    
    col1, col2 = st.columns(2)
    col1.metric("REVENUE", f"₹{int(t_sales)}")
    col2.metric("NET PROFIT", f"₹{int(t_prof)}")

    st.write("---")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        towrite = io.BytesIO()
        df_s.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button("📥 Download Sales Report (Excel)", data=towrite.getvalue(), file_name="Sales_Report.xlsx")

# --- 6. PET SALES REGISTER (Fixed NameError) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 New Pet Entry")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Indie", "Persian Cat", "Other"]
    with st.form("pet_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name"); phone = st.text_input("Phone"); br = st.selectbox("Breed", breeds)
        with c2:
            ag = st.text_input("Age"); wt = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Customer": name, "Breed": br, "Age": ag, "Weight": wt, "Due": dv})
            st.success("Saved!")
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING TERMINAL (Dropdown & Unit Fix) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("billing_machine"):
            item_sel = st.selectbox("Select Product (Dropdown)", list(st.session_state.inventory.keys()))
            inv_info = st.session_state.inventory[item_sel]
            
            c1, c2, c3 = st.columns(3)
            with c1: u_sel = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: q_sel = st.number_input("Quantity", min_value=0.1, step=0.1)
            with c3: r_sel = st.number_input("Rate (₹)", min_value=1, step=1)
            
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                avail = inv_info.get('qty', 0)
                if q_sel <= avail:
                    st.session_state.inventory[item_sel]['qty'] -= q_sel
                    total = q_sel * r_sel
                    profit = (r_sel - inv_info.get('p_price', 0)) * q_sel
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item_sel, "Qty": q_sel, "Unit": u_sel, "Total": total, "Profit": profit})
                    st.success(f"Bill Generated! Total: ₹{total}")
                else: st.error("Stock Kam Hai!")

# --- 8. PURCHASE & 9. LIVE STOCK ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Stock Entry")
    with st.form("p_f", clear_on_submit=True):
        n = st.text_input("Item Name"); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        r = st.number_input("Buy Rate", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add to Inventory"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': r, 'qty': q, 'unit': u}
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

# --- EXPENSES & SETTINGS ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("e"):
        res = st.text_input("Reason"); amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.session_state.expenses.append({"Reason": res, "Amount": amt, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Staff Management")
    if st.session_state.current_user == "Laika":
        u = st.text_input("New ID"); p = st.text_input("New Password")
        if st.button("Create Staff Account"): st.session_state.users[u] = p; st.success("Created!")
