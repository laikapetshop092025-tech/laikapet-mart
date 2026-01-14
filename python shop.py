import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")
conn = st.connection("gsheets", type=GSheetsConnection)

# Data Load karne ka function
def load_data(sheet_name):
    try:
        return conn.read(worksheet=sheet_name).dropna(how="all")
    except:
        return pd.DataFrame()

# Data Save karne ka function (Naya Logic)
def save_data(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear() # Cache clear taaki nayi list turant dikhe

# --- 2. STYLE (No Change) ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN (No Change) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u_id = st.text_input("Username"); u_pw = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "🐾 Pet Sales Register", "⚙️ Admin Settings"])

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    sales_df = load_data("Sales"); exp_df = load_data("Expenses"); inv_df = load_data("Inventory")
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. BILLING (List Fixed) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    inv_df = load_data("Inventory")
    sales_df = load_data("Sales")
    with st.form("bill"):
        item = st.selectbox("Product", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
        meth = st.selectbox("Payment", ["Cash", "Online"])
        if st.form_submit_button("COMPLETE BILL"):
            new_row = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": item, "total": qty*pr, "Method": meth, "profit": qty*10}]) # Profit sample
            updated_sales = pd.concat([sales_df, new_row], ignore_index=True)
            save_data(updated_sales, "Sales")
            st.success("Bill Saved!")
            st.rerun()
    st.subheader("📋 Recent Sales")
    st.table(sales_df.tail(10))

# --- 7. PURCHASE (List Fixed) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    inv_df = load_data("Inventory")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", min_value=1); r = st.number_input("Price", min_value=1)
        if st.form_submit_button("ADD"):
            new_stock = pd.DataFrame([{"Item": n, "qty": q, "p_price": r}])
            updated_inv = pd.concat([inv_df, new_stock], ignore_index=True)
            save_data(updated_inv, "Inventory")
            st.success("Stock Added!")
            st.rerun()
    st.subheader("📋 Purchase History")
    st.table(inv_df.tail(10))

# --- 8. PET REGISTER (List Fixed) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Other"])
        if st.form_submit_button("SAVE"):
            new_pet = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br}])
            updated_pets = pd.concat([pet_df, new_pet], ignore_index=True)
            save_data(updated_pets, "PetRecords")
            st.rerun()
    st.table(pet_df.tail(10))

# --- 9. ADMIN & LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar Records")
    st.table(load_data("Dues"))
    st.subheader("Create New ID")
    st.text_input("New Username")
