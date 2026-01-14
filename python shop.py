import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Setup ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- Database Initialization ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Login Logic ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- Sidebar ---
st.sidebar.title("🐾 MENU")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Bechna)", "📦 Purchase (Maal Lana)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{t_sales:,.2f}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{t_prof:,.2f}")
    c4.metric("EXPENSES", f"₹{t_exp:,.2f}")

# --- 2. PET SALES ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Indie/Desi", "Persian Cat", "Siamese Cat", "Other"]
    with st.form("pet_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with col2:
            breed = st.selectbox("Select Breed", breeds)
            next_v = st.date_input("Next Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed, "Due": next_v})
            st.success("Record Saved!")
    if st.session_state.pet_records:
        st.dataframe(pd.DataFrame(st.session_state.pet_records))

# --- 3. SALES ENTRY (Kilo aur Packet ka Hisab) ---
elif menu == "🧾 Sales Entry (Bechna)":
    st.title("🧾 Bechna / Sales")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("sale_f", clear_on_submit=True):
            item = st.selectbox("Kaunsa Maal Becha?", list(st.session_state.inventory.keys()))
            
            # Stock Detail Dikhana
            avail = st.session_state.inventory[item].get('qty', 0)
            unit = st.session_state.inventory[item].get('unit', 'Unit')
            buy_price = st.session_state.inventory[item].get('p_price', 0)
            
            st.info(f"Dukan mein bacha hai: {avail} {unit}")
            
            c1, c2 = st.columns(2)
            with c1:
                q_sell = st.number_input(f"Kitna becha? ({unit})", min_value=0.01)
            with c2:
                s_price = st.number_input("Selling Price (Kis rate par becha)", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total = q_sell * s_price
                    profit = (s_price - buy_price) * q_sell
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "qty": q_sell, "unit": unit})
                    st.success(f"Bik gaya! ₹{total} Stock se kam ho gaya.")
                else:
                    st.error(f"Stock kam hai! Sirf {avail} {unit} bacha hai.")

# --- 4. PURCHASE (Maal Chadana) ---
elif menu == "📦 Purchase (Maal Lana)":
    st.title("📦 Add New Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "Packet/PCS"])
        with col2:
            rate = st.number_input("Khareed Rate (Per Unit)", min_value=0.0)
            q = st.number_input("Total Quantity/Weight", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory:
                st.session_state.inventory[n]['qty'] += q
            else:
                st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    st.write("---")
    st.write("### Purchase History / Stock List")
    if st.session_state.inventory:
        data = [{"Item": k, "Buy Rate": v['p_price'], "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data))

# --- 5. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Report")
    if st.session_state.inventory:
        data_stock = [{"Item": k, "Qty": v['qty'], "Unit": v['unit'], "Value": v['qty'] * v['p_price']} for k, v in st.session_state.inventory.items()]
        st.table(pd.DataFrame(data_stock))
    else: st.info("Stock Khali Hai.")

# --- 6. EXPENSES ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Manager")
    with st.form("exp"):
        r = st.text_input("Reason")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now()})
    st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Authority")
    if st.session_state.current_user == "Laika":
        new_u = st.text_input("Staff ID")
        new_p = st.text_input("Password")
        if st.button("Create ID"):
            st.session_state.users[new_u] = new_p
            st.success("Done!")
    else: st.warning("No Access")
