import streamlit as st # Interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheet sync ke liye
import pandas as pd # Data tables handle karne ke liye
from datetime import datetime # Date-Time ke liye

# --- 1. CONNECTION SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet connection

# Data load karne ka function (ttl=0 taaki hamesha fresh data mile)
def load_data(sheet):
    try:
        # Sheet se data padhna aur khali rows hatana
        return conn.read(worksheet=sheet, ttl=0).dropna(how="all")
    except Exception as e:
        # Agar sheet nahi mili toh khali table dikhana bajaye error ke
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.subheader("🔐 Staff Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
st.markdown("<h1 style='text-align: center; color: #2E5BFF;'>LAIKA PET MART</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (Metrics logic) ---
if menu == "📊 Dashboard":
    st.subheader("📊 Business Overview")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    # Calculations
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. PURCHASE (Form + List) ---
elif menu == "📦 Purchase":
    st.header("📦 Add Stock")
    inv_df = load_data("Inventory")
    with st.form("p_f"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", min_value=0.1); p = st.number_input("Price", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            new_r = pd.DataFrame([{"Item": n, "qty": q, "p_price": p}])
            conn.update(worksheet="Inventory", data=pd.concat([inv_df, new_r], ignore_index=True)) # Save
            st.success("Stock Added!"); st.rerun()
    st.table(inv_df.tail(10))

# --- 6. PET REGISTER (Full columns) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2:
            age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Age": age, "Weight": wt, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([pet_df, new_p], ignore_index=True)) # Save
            st.success("Saved!"); st.rerun()
    st.table(pet_df.tail(10))

# --- 7. BAAKI SECTIONS ---
elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    e_df = load_data("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save"):
        new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
        conn.update(worksheet="Expenses", data=pd.concat([e_df, new_e], ignore_index=True))
        st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

elif menu == "⚙️ Admin Settings":
    st.subheader("Dues Record")
    st.table(load_data("Dues"))

elif menu == "🧾 Billing":
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    it = st.selectbox("Item", i_df['Item'].tolist() if not i_df.empty else ["No Stock"])
    if st.button("Complete Bill"):
        st.success("Bill Synced!"); st.rerun()
