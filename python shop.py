import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #4A90E2; font-size: 40px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'>🐾 LAIKA PET MART</div>", unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. LOGIN & AUTO-LOGOUT ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username")
        u_pw = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

# --- 5. PURCHASE (FIXED: List dikhegi niche) ---
if menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form", clear_on_submit=True):
        n = st.text_input("Item Name")
        r = st.number_input("Purchase Price", min_value=1)
        q = st.number_input("Quantity", min_value=1)
        u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("ADD TO STOCK"):
            if n:
                if n in st.session_state.inventory:
                    st.session_state.inventory[n]['qty'] += q
                else:
                    st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
                st.success(f"{n} added!")
                st.rerun()
    
    st.write("---")
    st.subheader("📋 Current Stock List")
    if st.session_state.inventory:
        df_inv = pd.DataFrame([{"Item": k, "Stock": v['qty'], "Price": v['p_price'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()])
        st.table(df_inv)

# --- 6. BILLING (FIXED: Stock alert dikhega) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
            available = st.session_state.inventory[item]['qty']
            st.info(f"Available Stock: {available}")
            qty = st.number_input("Selling Qty", min_value=0.1)
            pr = st.number_input("Selling Price", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("GENERATE BILL"):
                if qty <= available:
                    st.session_state.inventory[item]['qty'] -= qty
                    profit = (pr - st.session_state.inventory[item]['p_price']) * qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": qty, "total": qty*pr, "profit": profit, "Customer": cust})
                    st.success("Bill Generated!")
                    st.rerun()
                else: st.error("Stock Kam Hai!")
    
    st.write("---")
    st.subheader("📋 Recent Bills")
    if st.session_state.sales:
        st.table(pd.DataFrame(st.session_state.sales).tail(5))

# --- 7. PET REGISTER (FIXED: All details) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Register")
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Customer Name")
            p = st.text_input("Phone")
            b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Husky", "Pug", "Other"])
        with c2:
            a = st.text_input("Age")
            w = st.text_input("Weight")
            v = st.date_input("Vaccine Date")
        if st.form_submit_button("Save Record"):
            st.session_state.pet_records.append({"Name": n, "Phone": p, "Breed": b, "Age": a, "Vaccine": v})
            st.rerun()
    st.table(pd.DataFrame(st.session_state.pet_records))

# --- 8. ADMIN SETTINGS (Udhaar + ID) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar")
    with st.form("udh"):
        cn = st.text_input("Company Name")
        ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca})
            st.rerun()
    st.table(pd.DataFrame(st.session_state.company_dues))
    
    st.write("---")
    st.subheader("👤 Create Staff ID")
    new_u = st.text_input("New Username")
    new_p = st.text_input("New Password")
    if st.button("Create"):
        st.session_state.users[new_u] = new_p
        st.success("ID Created!")

# --- 9. OTHERS ---
elif menu == "📊 Dashboard":
    st.title("📊 Dashboard")
    t_s = sum(s['total'] for s in st.session_state.sales)
    t_e = sum(e['Amount'] for e in st.session_state.expenses)
    st.metric("Total Sale", f"₹{t_s}")
    st.metric("Total Expense", f"₹{t_e}")

elif menu == "📋 Live Stock":
    st.title("📋 Stock")
    st.table(pd.DataFrame([{"Item": k, "Qty": v['qty']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    amt = st.number_input("Amount", min_value=1)
    if st.button("Save"):
        st.session_state.expenses.append({"Amount": amt, "Date": datetime.now().date()})
        st.rerun()

elif menu == "📅 Report Center":
    st.title("📅 Monthly Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("Download", df.to_csv().encode('utf-8'), "Report.csv")
