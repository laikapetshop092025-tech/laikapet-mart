import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Apna Apps Script URL yahan dalein
SCRIPT_URL = "YAHAN_APNA_APPS_SCRIPT_URL_PASTE_KAREIN" 
# Sheet Link (CSV export format mein)
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_to_gsheet(sheet_name, data_list):
    try:
        requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return True
    except:
        return False

def load_from_gsheet(sheet_name):
    try:
        # Taza data khinchne ke liye cache clear rakhte hain
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

# --- 4. PURCHASE (Yahan entry karte hi Stock update hoga) ---
if menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    # Fresh Inventory Load karna
    inv_df = load_from_gsheet("Inventory")
    
    with st.form("pur_f"):
        n = st.text_input("Item Name (Product Name)")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Quantity", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price (Rate)")
        if st.form_submit_button("ADD TO STOCK"):
            # Google Sheet mein save karna
            save_to_gsheet("Inventory", [n, q, u, p, str(datetime.now().date())])
            st.success(f"{n} Stock mein add ho gaya!")
            st.rerun() # App ko turant refresh karega
            
    st.subheader("📋 Purchase History (Jo aapne kharida)")
    st.table(inv_df.tail(10))

# --- 5. BILLING (Stock se Item uthayega) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_from_gsheet("Inventory")
    sales_df = load_from_gsheet("Sales")
    
    with st.form("bill_f"):
        # Agar inventory khali nahi hai, toh items dikhayega
        items_list = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock Available"]
        it = st.selectbox("Select Product (From Purchase Stock)", items_list)
        
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Qty", min_value=0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        with c3: price = st.number_input("Selling Price")
        
        mode = st.selectbox("Payment Mode", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_to_gsheet("Sales", [str(datetime.now().date()), it, f"{qty} {unit}", qty*price, mode])
            st.success("Bill Saved!")
            st.rerun()
            
    st.subheader("📋 Recent Sales")
    st.table(sales_df.tail(10))

# --- 6. LIVE STOCK (Vahi jo Purchase mein hai) ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock (Live)")
    # Direct Inventory Sheet se data load karna
    stock_df = load_from_gsheet("Inventory")
    if not stock_df.empty:
        st.table(stock_df)
    else:
        st.warning("Abhi koi stock nahi hai. Pehle Purchase mein entry karein.")

# --- 7. DASHBOARD (Total Sale/Purchase Sync) ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Overview")
    s_df = load_from_gsheet("Sales"); i_df = load_from_gsheet("Inventory"); e_df = load_from_gsheet("Expenses")
    
    t_sale = pd.to_numeric(s_df['total'], errors='coerce').sum() if not s_df.empty else 0
    t_exp = pd.to_numeric(e_df['Amount'], errors='coerce').sum() if not e_df.empty else 0
    t_pur = 0
    if not i_df.empty:
        t_pur = (pd.to_numeric(i_df['qty'], errors='coerce') * pd.to_numeric(i_df['p_price'], errors='coerce')).sum()
    
    t_profit = t_sale - t_exp - t_pur

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 8. EXPENSES, PET REGISTER, ADMIN (Baaki Code Same Rahega) ---
elif menu == "💰 Expenses":
    e_df = load_from_gsheet("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save"):
        save_to_gsheet("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(e_df.tail(10))

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "Persian Cat", "Other"])
        age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            save_to_gsheet("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Saved!"); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.subheader("🏢 Company Dues")
    st.text_input("Company Name"); st.number_input("Amount")
    if st.button("Save Due"): st.success("Saved!")
    st.divider()
    st.subheader("👤 Staff Management")
    st.text_input("New User"); st.text_input("Pass", type="password")
    if st.button("Create ID"): st.success("Created!")
