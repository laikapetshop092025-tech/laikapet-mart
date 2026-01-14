import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- Database Setup ---
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
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- Menu ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("🚀 Business Overview")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{t_sales:,.2f}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{t_prof:,.2f}")
    c4.metric("EXPENSES", f"₹{t_exp:,.2f}")

# --- 2. PET SALES (With Breed Dropdown) ---
elif menu == "🐾 Pet Sales":
    st.title("🐾 Pet Registration")
    # Popular breeds ki list
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Indie/Desi", "Persian Cat", "Siamese Cat", "Other"]
    
    with st.form("pet_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with col2:
            breed_sel = st.selectbox("Select Breed", breeds)
            next_v = st.date_input("Next Vaccine Due", datetime.now() + timedelta(days=30))
        if st.form_submit_button("SAVE"):
            st.session_state.pet_records.append({"Customer": name, "Phone": phone, "Breed": breed_sel, "Due": next_v})
            st.success("Saved!")
    st.write("### Recent Pet Sales")
    st.dataframe(pd.DataFrame(st.session_state.pet_records))

# --- 3. SALES ENTRY (With Live Stock Check) ---
elif menu == "🧾 Sales Entry":
    st.title("🧾 Make a Sale")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("sale_f", clear_on_submit=True):
            item = st.selectbox("Select Item", list(st.session_state.inventory.keys()))
            # Live Stock dikhana
            avail = st.session_state.inventory[item]['qty']
            unit = st.session_state.inventory[item]['unit']
            st.info(f"Current Stock Available: {avail} {unit}")
            
            qty = st.number_input(f"Qty to Sell ({unit})", min_value=0.01)
            price = st.number_input("Selling Price (Per Unit)", min_value=0.0)
            
            if st.form_submit_button("COMPLETE SALE"):
                if qty <= avail:
                    st.session_state.inventory[item]['qty'] -= qty
                    total = qty * price
                    profit = (price - st.session_state.inventory[item]['p_price']) * qty
                    st.session_state.sales.append({"Item": item, "total": total, "profit": profit, "Date": datetime.now()})
                    st.success(f"Sale Successful! ₹{total}")
                else:
                    st.error("Stock mein itna maal nahi hai!")

# --- 4. PURCHASE (With List Below) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add New Stock")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Price", min_value=0.0)
            q = st.number_input("Quantity", min_value=0.0)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    st.write("---")
    st.write("### Purchase History / Stock List")
    if st.session_state.inventory:
        df_pur = pd.DataFrame.from_dict(st.session_state.inventory, orient='index').reset_index()
        df_pur.columns = ['Item Name', 'Buy Rate', 'Current Qty', 'Unit']
        st.table(df_pur)

# --- 5. LIVE STOCK (Fixing the Error) ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Inventory")
    if st.session_state.inventory:
        data = []
        for k, v in st.session_state.inventory.items():
            data.append({"Item": k, "Qty": v['qty'], "Unit": v['unit'], "Value": v['qty'] * v['p_price']})
        st.table(pd.DataFrame(data))
    else:
        st.info("Stock Khali Hai.")

# --- 6. EXPENSES ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Manager")
    with st.form("exp"):
        r = st.text_input("Reason")
        a = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"Reason": r, "Amount": a, "Date": datetime.now()})
    st.table(pd.DataFrame(st.session_state.expenses))

# --- 7. SETTINGS ---
elif menu == "⚙️ Settings":
    st.title("⚙️ Admin Settings")
    if st.session_state.current_user == "Laika":
        new_u = st.text_input("New Staff ID")
        new_p = st.text_input("New Password")
        if st.button("Create"):
            st.session_state.users[new_u] = new_p
            st.success("Created!")
    else: st.warning("No Access")
