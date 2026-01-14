import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & BRANDING ---
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

# --- 2. DATA INITIALIZATION (Logic Safe) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'company_dues' not in st.session_state: st.session_state.company_dues = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT LOGIC (10 Minutes) ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else:
        st.session_state.last_activity = time.time()

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("🔐 Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = u_id
                st.rerun()
            else:
                st.error("Ghalat Username ya Password!")
    st.stop()

# --- 5. NAVIGATION & LOGOUT ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📅 Report Center", "🐾 Pet Sales Register", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. DASHBOARD (Original Metrics) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("NET PROFIT", f"₹{int(n_prof)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    if st.session_state.company_dues:
        t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)
        if t_udh > 0: st.error(f"⚠️ Pending Company Udhaar: ₹{int(t_udh)}")

# --- 7. EXPENSES (With Dropdown) ---
elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    exp_cats = ["Rent", "Electricity Bill", "Staff Salary", "Pet Food / Supplies", "Tea & Snacks", "Maintenance", "Other"]
    e_cat = st.selectbox("Select Category", exp_cats)
    e_amt = st.number_input("Amount (₹)", min_value=1)
    if st.button("Save Expense"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Item": e_cat, "Amount": e_amt})
        st.success("Expense Saved!")
        st.rerun()
    if st.session_state.expenses: st.table(pd.DataFrame(st.session_state.expenses))

# --- 8. PURCHASE & BILLING (With List & Stock Alert) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form", clear_on_submit=True):
        n = st.text_input("Item Name"); r = st.number_input("Purchase Price", min_value=1)
        q = st.number_input("Qty", min_value=1); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("ADD STOCK"):
            if n:
                if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
                else: st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
                st.rerun()
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Price": v['p_price'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if not st.session_state.inventory: st.warning("Stock khali hai!")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            st.info(f"Available Stock: {st.session_state.inventory[item]['qty']}")
            qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("GENERATE BILL"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": qty, "total": qty*pr, "profit": (pr-inv['p_price'])*qty, "Customer": cust})
                    st.rerun()

# --- 9. BAAKI SECTIONS (Pet Reg, Udhaar, Report) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: n = st.text_input("Customer"); p = st.text_input("Phone"); b = st.selectbox("Breed", ["Labrador", "German Shepherd", "Pug", "Other"])
        with c2: a = st.text_input("Age"); w = st.text_input("Weight"); v = st.date_input("Vaccine Date")
        if st.form_submit_button("Save Record"):
            st.session_state.pet_records.append({"Customer": n, "Phone": p, "Breed": b, "Age": a, "Next Vaccine": v})
            st.rerun()
    if st.session_state.pet_records: st.table(pd.DataFrame(st.session_state.pet_records))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar")
    with st.form("udh"):
        cn = st.text_input("Company Name"); ca = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": cn, "Amount": ca, "Date": datetime.now().date()})
            st.rerun()
    if st.session_state.company_dues: st.table(pd.DataFrame(st.session_state.company_dues))
    
    st.write("---")
    st.subheader("👤 Create Staff Account")
    new_u = st.text_input("New Username"); new_p = st.text_input("New Password")
    if st.button("Create ID"):
        st.session_state.users[new_u] = new_p
        st.success("Account Created!")

elif menu == "📅 Report Center":
    st.title("📅 Monthly Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("📥 Download Excel", df.to_csv(index=False).encode('utf-8'), "Report.csv", "text/csv")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))
