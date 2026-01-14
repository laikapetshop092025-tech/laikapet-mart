import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. PAGE SETUP & BRANDING ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
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

# --- 3. AUTO-LOGOUT ---
if st.session_state.logged_in:
    if time.time() - st.session_state.last_activity > 600:
        st.session_state.logged_in = False
        st.rerun()
    else: st.session_state.last_activity = time.time()

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Ghalat Details!")
    st.stop()

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", 
    "📅 Report Center", 
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

# --- 6. PET SALES REGISTER (Wapas Saare Options Add Kar Diye) ---
if menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration & Vaccine Record")
    with st.form("pet_reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cust_name = st.text_input("Customer Name")
            cust_phone = st.text_input("Customer Phone Number")
            # Dog Breed Dropdown
            dog_breed = st.selectbox("Select Dog Breed", ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Indie", "Other"])
        with c2:
            dog_age = st.text_input("Dog Age (e.g. 2 Months / 1 Year)")
            dog_weight = st.text_input("Dog Weight (kg)")
            vaccine_date = st.date_input("Next Vaccine Date", datetime.now())
        
        if st.form_submit_button("SAVE PET RECORD"):
            if cust_name and cust_phone:
                st.session_state.pet_records.append({
                    "Date": datetime.now().date(),
                    "Customer": cust_name,
                    "Phone": cust_phone,
                    "Breed": dog_breed,
                    "Age": dog_age,
                    "Weight": dog_weight,
                    "Next Vaccine": vaccine_date
                })
                st.success(f"Record for {cust_name} saved!")
                st.rerun()
            else:
                st.error("Please enter Customer Name and Phone!")

    if st.session_state.pet_records:
        st.write("### Recent Registrations")
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Analytics")
    t_sale = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_pur = sum(v.get('qty', 0) * v.get('p_price', 0) for v in st.session_state.inventory.values())
    n_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    t_udh = sum(d.get('Amount', 0) for d in st.session_state.company_dues)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("NET PROFIT", f"₹{int(n_prof)}")
    c4.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    
    if t_udh > 0:
        st.error(f"⚠️ Pending Company Udhaar: ₹{int(t_udh)}")

# --- 8. ADMIN SETTINGS (Udhaar Option) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar (Pending Payments)")
    with st.form("udh_form", clear_on_submit=True):
        c_name = st.text_input("Company Name")
        c_amt = st.number_input("Pending Amount (₹)", min_value=1)
        if st.form_submit_button("Save Udhaar"):
            st.session_state.company_dues.append({"Company": c_name, "Amount": c_amt, "Date": datetime.now().date()})
            st.rerun()
    
    if st.session_state.company_dues:
        st.table(pd.DataFrame(st.session_state.company_dues))
        for i, d in enumerate(st.session_state.company_dues):
            if st.button(f"Clear Udhaar: {d['Company']}", key=f"udh_{i}"):
                st.session_state.company_dues.pop(i); st.rerun()

# --- BAAKI ORIGINAL SECTIONS (Billing, Purchase, Stock, Report) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    if st.session_state.inventory:
        with st.form("bill_f"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
            cust = st.text_input("Customer Name")
            if st.form_submit_button("Generate Bill"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    st.session_state.sales.append({"Date": datetime.now().date(), "Item": item, "Qty": qty, "total": qty*pr, "profit": (pr-inv['p_price'])*qty, "Customer": cust})
                    st.rerun()

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); r = st.number_input("Price", min_value=1)
        q = st.number_input("Qty", min_value=1); u = st.selectbox("Unit", ["KG", "PCS", "Packet"])
        if st.form_submit_button("Add Stock"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'qty': q, 'p_price': r, 'unit': u}
            st.rerun()

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff", "Other"])
    amt = st.number_input("Amount", min_value=1)
    if st.button("Save"):
        st.session_state.expenses.append({"Date": datetime.now().date(), "Amount": amt, "Category": cat})
        st.rerun()

elif menu == "📅 Report Center":
    st.title("📅 Monthly Report")
    if st.session_state.sales:
        df = pd.DataFrame(st.session_state.sales)
        st.table(df)
        st.download_button("Download Excel", df.to_csv(index=False).encode('utf-8'), "Report.csv", "text/csv")
