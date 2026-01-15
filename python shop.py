import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Yahan apna naya Apps Script URL paste karein
SCRIPT_URL = "YAHAN_APNA_NEW_URL_PASTE_KAREIN" 
SHEET_LINK = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec"

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        if response.text == "Success":
            return True
        else:
            st.error(f"Sheet Error: {response.text}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 LOGIN - LAIKA PET MART")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. PURCHASE (Stock Sync) ---
if menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            if save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]):
                st.success("Data Saved!"); st.rerun()
    st.table(inv_df.tail(10))

# --- 5. PET REGISTER (Weight, Age, Vaccine Date) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie Dog/Cat", "Other"])
        with c2:
            age = st.text_input("Pet Age"); wt = st.text_input("Weight (Kg)")
            vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE"):
            if save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]):
                st.success("Pet Saved!"); st.rerun()
    st.table(p_df.tail(10))

# --- 6. DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    t_sale = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    t_exp = pd.to_numeric(e_df.iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    t_pur = (pd.to_numeric(i_df.iloc[:, 1], errors='coerce') * pd.to_numeric(i_df.iloc[:, 3], errors='coerce')).sum() if not i_df.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_sale - t_exp - t_pur)}")

# --- 7. BILLING, LIVE STOCK, EXPENSES, ADMIN (Same Logic) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    it = st.selectbox("Select Product", it_list)
    q = st.number_input("Qty", min_value=0.1); pr = st.number_input("Selling Price")
    if st.button("Complete Bill"):
        save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"])
        st.rerun()

elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    e_df = load_data("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(e_df.tail(10))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar (Dues)"); d_df = load_data("Dues")
    c = st.text_input("Company"); a = st.number_input("Amount")
    if st.button("Save Due"): 
        save_data("Dues", [c, a, str(datetime.now().date())])
        st.rerun()
    st.table(d_df)
