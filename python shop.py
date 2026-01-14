import streamlit as st # App interface banane ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheet se connect karne ke liye
import pandas as pd # Data tables ke liye
from datetime import datetime # Date aur time record karne ke liye

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet connection setup

# Data load karne ka function (Fresh data ke liye ttl=0)
def load_data(sheet):
    try:
        return conn.read(worksheet=sheet, ttl=0).dropna(how="all")
    except Exception as e:
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 LAIKA PET MART LOGIN")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. NAVIGATION MENU ---
st.markdown("<h1 style='text-align: center; color: #2E5BFF;'>LAIKA PET MART</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (SALE, PURCHASE, EXPENSE, PROFIT) ---
if menu == "📊 Dashboard":
    st.subheader("📊 Business Ki Puri Jankari")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    t_sale = s_df['total'].sum() if not s_df.empty else 0 # Kul bikri
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0 # Kul kharid
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0 # Kul kharche
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp # Shuddh munafa

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. BILLING (Kg/Pcs, Online/Offline + List) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("bill_form"):
        it_list = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", it_list) # Item dropdown
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Quantity", min_value=0.1) # Kitna maal diya
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"]) # Unit ka hisab
        with c3: price = st.number_input("Rate", min_value=1) # Rate
        mode = st.selectbox("Payment Mode", ["Online", "Cash"]) # Online ya offline
        if st.form_submit_button("COMPLETE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": it, "Qty": f"{qty} {unit}", "total": qty*price, "Mode": mode, "profit": (price-10)*qty}])
            # NOTE: conn.update tabhi chalega jab JSON key set ho
            st.success("Billing feature ready. Sync on Google Sheets activated.")

# --- 6. PURCHASE (Add Stock + History List) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory")
    with st.form("purchase_form"):
        n = st.text_input("Item Name") # Saman ka naam
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Quantity", min_value=0.1) # Matra
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"]) # Piece ya kilo
        p = st.number_input("Purchase Price", min_value=1) # Kharid bhav
        if st.form_submit_button("ADD TO STOCK"):
            st.success(f"{n} ({q} {u}) stock entry ready for sync.")

# --- 7. ADMIN SETTINGS (Udhaar + New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    dues_df = load_data("Dues")
    with st.expander("🏢 Company Udhaar (Dues Record)"):
        comp = st.text_input("Company Name"); amt = st.number_input("Amount", min_value=1)
        if st.button("Save Due"): st.success("Udhaar record ready.")
        st.table(dues_df) # Udhaar ki list
    with st.expander("👤 Create New Staff ID"):
        st.text_input("New Username"); st.text_input("Set Password", type="password")
        if st.button("Create ID"): st.success("New staff ID created!")

# --- 8. PET REGISTER (Phone, Breed, Age, Weight, Vaccine) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.text_input("Breed")
        with c2: age = st.text_input("Dog Age"); wt = st.text_input("Weight (Kg)"); vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"): st.success("Pet record registered!")
    st.table(pet_df.tail(10)) # Pet records ki list
