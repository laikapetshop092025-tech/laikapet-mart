import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
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

# --- 4. SIDEBAR ---
menu = st.sidebar.radio("Menu", ["📊 Dashboard & Reports", "🐾 Pet Sales Register", "🧾 Billing & Sales", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# --- 5. DASHBOARD & EXCEL REPORTS ---
if menu == "📊 Dashboard & Reports":
    st.title("📊 Business Analytics")
    t_sales = sum(s.get('Total Amount', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('Profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL REVENUE", f"₹{int(t_sales)}")
    c2.metric("NET PROFIT", f"₹{int(t_prof)}")
    c3.metric("EXPENSES", f"₹{int(t_exp)}")

    st.write("---")
    st.subheader("📥 Download Business Reports (Excel)")
    col_a, col_b = st.columns(2)
    
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        output_s = io.BytesIO()
        with pd.ExcelWriter(output_s, engine='xlsxwriter') as writer:
            df_s.to_excel(writer, index=False, sheet_name='Sales')
        col_a.download_button("📥 Download Sales Report", data=output_s.getvalue(), file_name="Sales_Report.xlsx")

    if st.session_state.inventory:
        df_p = pd.DataFrame([{"Item": k, **v} for k, v in st.session_state.inventory.items()])
        output_p = io.BytesIO()
        with pd.ExcelWriter(output_p, engine='xlsxwriter') as writer:
            df_p.to_excel(writer, index=False, sheet_name='Inventory')
        col_b.download_button("📥 Download Stock Report", data=output_p.getvalue(), file_name="Stock_Report.xlsx")

# --- 6. BILLING & SALES ENTRY ---
elif menu == "🧾 Billing & Sales":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("bill_form", clear_on_submit=True):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            st.info(f"Available Stock: {info.get('qty', 0)} {info.get('unit', 'Unit')}")
            
            c1, c2, c3 = st.columns(3)
            with c1: unit_s = st.selectbox("Unit", ["KG", "PCS", "Packet"])
            with c2: qty_s = st.number_input("Quantity", min_value=0.01, step=0.1)
            with c3: price_s = st.number_input("Rate (₹)", min_value=1, step=1)
            
            cust = st.text_input("Customer Name")
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                if qty_s <= info.get('qty', 0):
                    st.session_state.inventory[item]['qty'] -= qty_s
                    total = qty_s * price_s
                    profit = (price_s - info.get('p_price', 0)) * qty_s
                    sale_data = {"Date": datetime.now().date(), "Customer": cust, "Item": item, "Qty": qty_s, "Unit": unit_s, "Rate": price_s, "Total Amount": total, "Profit": profit}
                    st.session_state.sales.append(sale_data)
                    
                    st.success("Sale Recorded!")
                    st.markdown(f"### 📄 INVOICE: {item}\n*Customer:* {cust}\n*Total: ₹{total}*")
                else: st.error("Stock Kam Hai!")

# --- 7. PET SALES REGISTER ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Lifecycle Record")
    with st.form("pet_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer"); p = st.text_input("Phone"); br = st.text_input("Breed")
        with col2: ag = st.text_input("Age"); wt = st.text_input("Weight"); dv = st.date_input("Next Vaccine")
        if st.form_submit_button("Save"):
            st.session_state.pet_records.append({"Customer": n, "Breed": br, "Age": ag, "Weight": wt, "Next Due": dv})
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

# --- 8. PURCHASE ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: name = st.text_input("Item Name"); unit = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        with col2: buy = st.number_input("Buy Rate", min_value=1); qty = st.number_input("Qty", min_value=1)
        if st.form_submit_button("Add Stock"):
            if name in st.session_state.inventory: st.session_state.inventory[name]['qty'] += qty
            else: st.session_state.inventory[name] = {'p_price': buy, 'qty': qty, 'unit': unit}
    if st.session_state.inventory:
        st.write("### Current Stock")
        st.table(pd.DataFrame([{"Item": k, "Stock": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))

# --- 9. LIVE STOCK, EXPENSES, ADMIN ---
elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v.get('qty',0), "Unit": v.get('unit','Unit')} for k, v in st.session_state.inventory.items()]))
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        r = st.text_input("Reason"); a = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Authority")
    if st.session_state.current_user == "Laika":
        u = st.text_input("New ID"); p = st.text_input("New Password")
        if st.button("Create"): st.session_state.users[u] = p; st.success("Done!")
