import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA INITIALIZATION ---
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

# --- SIDEBAR ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Billing)", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    total_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    total_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    total_profit = sum(s.get('profit', 0) for s in st.session_state.sales) - total_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{total_sales}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{total_profit}")
    c4.metric("EXPENSES", f"₹{total_exp}")

# --- SALES ENTRY (Updated with Unit & Simple Amount) ---
elif menu == "🧾 Sales Entry (Billing)":
    st.title("🧾 Bechna aur Bill Banana")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_form", clear_on_submit=True):
            item = st.selectbox("Kaunsa Maal Becha?", list(st.session_state.inventory.keys()))
            
            # Stock check
            info = st.session_state.inventory[item]
            avail = info.get('qty', 0)
            st.info(f"Dukan mein bacha hai: {avail}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # Unit selection (KG ya PCS)
                u_sell = st.selectbox("Unit Chunein", ["KG", "PCS/Packet"])
            with col2:
                # Simple number input without decimals
                q_sell = st.number_input(f"Kitna becha?", min_value=1, value=1, step=1)
            with col3:
                # Rate input - Direct amount
                s_price = st.number_input("Kis rate par becha? (₹)", min_value=1, value=100, step=1)
            
            cust_name = st.text_input("Customer ka Naam (Optional)")
            
            if st.form_submit_button("COMPLETE SALE & SHOW BILL"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total_amt = q_sell * s_price
                    profit_amt = (s_price - info.get('p_price', 0)) * q_sell
                    
                    sale_data = {
                        "Date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                        "Customer": cust_name if cust_name else "Cash Customer",
                        "Item": item,
                        "Qty": q_sell,
                        "Unit": u_sell,
                        "Total": total_amt,
                        "profit": profit_amt
                    }
                    st.session_state.sales.append(sale_data)
                    
                    # BILL DISPLAY
                    st.success("Sale Recorded!")
                    st.markdown("---")
                    st.subheader("📄 LAIKA PET MART - INVOICE")
                    st.write(f"*Date:* {sale_data['Date']}")
                    st.write(f"*Customer:* {sale_data['Customer']}")
                    st.write(f"*Item:* {item} ({q_sell} {u_sell})")
                    st.write(f"*Rate:* ₹{s_price}")
                    st.write(f"### *Total Amount: ₹{total_amt}*")
                    st.markdown("---")
                else:
                    st.error(f"Stock Kam Hai! Sirf {avail} bacha hai.")

# --- PURCHASE (Fixed List) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Naya Maal Chadhana")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Khareed Rate (₹)", min_value=1, value=50, step=1)
            q = st.number_input("Quantity", min_value=1, value=10, step=1)
        if st.form_submit_button("ADD TO STOCK"):
            if n in st.session_state.inventory:
                st.session_state.inventory[n]['qty'] += q
            else:
                st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    if st.session_state.inventory:
        st.subheader("📋 Current Stock List")
        data = [{"Item": k, "Buy Rate": v['p_price'], "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# --- Baki Sections Fix ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    with st.form("p_f"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); cp = st.text_input("Phone")
        with c2: br = st.text_input("Pet Breed"); dv = st.date_input("Vaccine Date")
        if st.form_submit_button("Save"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": cn, "Breed": br, "Due": dv})
    st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "📋 Live Stock":
    st.title("📋 Live Inventory")
    st.table(pd.DataFrame([{"Item": k, "Qty": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("e_f"):
        re = st.text_input("Reason"); am = st.number_input("Amount", min_value=1, step=1)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": re, "Amount": am, "Date": datetime.now().date()})
    st.table(pd.DataFrame(st.session_state.expenses))
