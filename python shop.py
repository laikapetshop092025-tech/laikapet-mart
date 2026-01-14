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
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales & Billing", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses"])

# --- DASHBOARD (Total Business) ---
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

# --- SALES & BILLING (Naya Updated Section) ---
elif menu == "🧾 Sales & Billing":
    st.title("🧾 Sales Terminal & Bill Generator")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein stock bhariye!")
    else:
        with st.form("sale_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                item = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
                cust_name = st.text_input("Customer Name (Optional)")
            
            # Stock ki jankari nikalna
            avail = st.session_state.inventory[item].get('qty', 0)
            unit = st.session_state.inventory[item].get('unit', 'Unit')
            buy_rate = st.session_state.inventory[item].get('p_price', 0)
            
            st.info(f"Dukan mein bacha hai: {avail} {unit}")
            
            with col2:
                qty_s = st.number_input(f"Kitna becha? ({unit})", min_value=0.01, step=0.01)
                price_s = st.number_input("Kis rate par becha? (Per Unit Price)", min_value=0.0)
            
            generate_bill = st.form_submit_button("COMPLETE SALE & GENERATE BILL")
            
            if generate_bill:
                if qty_s <= avail:
                    # Calculation
                    st.session_state.inventory[item]['qty'] -= qty_s
                    total_amt = qty_s * price_s
                    profit_amt = (price_s - buy_rate) * qty_s
                    
                    sale_data = {
                        "Customer": cust_name if cust_name else "Cash Customer",
                        "Item": item,
                        "Qty": qty_s,
                        "Unit": unit,
                        "Rate": price_s,
                        "Total": total_amt,
                        "profit": profit_amt,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.sales.append(sale_data)
                    
                    # --- BILL DISPLAY (Visual Bill) ---
                    st.success("Sale Recorded Successfully!")
                    st.markdown("---")
                    st.markdown(f"### 📄 BILL / INVOICE")
                    st.markdown(f"*Shop:* {st.session_state.get('shop_name', 'LAIKA PET MART')}")
                    st.write(f"*Date:* {sale_data['Date']}")
                    st.write(f"*Customer:* {sale_data['Customer']}")
                    
                    bill_df = pd.DataFrame([{
                        "Description": item,
                        "Qty": f"{qty_s} {unit}",
                        "Rate": f"₹{price_s}",
                        "Total Amount": f"₹{total_amt}"
                    }])
                    st.table(bill_df)
                    st.markdown(f"## *GRAND TOTAL: ₹{total_amt}*")
                    st.markdown("---")
                else:
                    st.error(f"Error: Stock mein sirf {avail} {unit} bacha hai!")

# --- PURCHASE (Fixed with List) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add New Stock")
    with st.form("pur_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price (Khareed)", min_value=0.0)
            q = st.number_input("Quantity (Total)", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory:
                st.session_state.inventory[n]['qty'] += q
            else:
                st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success(f"{n} Added!")

    st.subheader("📋 Stock Inventory History")
    if st.session_state.inventory:
        data = [{"Item": k, "Buy Rate": v['p_price'], "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# Baki sections (Pet Sales, Live Stock, Expenses) ka code waisa hi rahega...
