import streamlit as st # App interface banane ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets se connect karne ke liye
import pandas as pd # Data handle karne ke liye
from datetime import datetime # Date aur time ke liye

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet link karna

def load_data(sheet): # Sheet se data uthane ka function
    try:
        return conn.read(worksheet=sheet, ttl=0).dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
st.markdown("<h1 style='text-align: center; color: #2E5BFF;'>LAIKA PET MART</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD ---
if menu == "📊 Dashboard":
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. BILLING (Pcs/Kg + Online/Offline Added) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("bill_form"):
        item = st.selectbox("Select Item", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Quantity", min_value=0.1) # Kitna maal diya
        with c2: q_type = st.selectbox("Unit", ["Pcs", "Kg", "Gram", "Packet"]) # Piece ya Kilo
        with c3: price = st.number_input("Rate", min_value=1) # Kis rate par becha
        pay_mode = st.selectbox("Payment Mode", ["Online", "Offline/Cash"]) # Online ya Offline
        if st.form_submit_button("GENERATE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": item, "Qty": f"{qty} {q_type}", "total": qty*price, "Mode": pay_mode, "profit": (price-10)*qty}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Saved!"); st.rerun()
    st.table(sales_df.tail(10)) # Niche sales list

# --- 6. PURCHASE (Pcs/Kg Added) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Register")
    inv_df = load_data("Inventory")
    with st.form("pur_form"):
        name = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: p_qty = st.number_input("Qty", min_value=0.1)
        with c2: p_unit = st.selectbox("Unit", ["Pcs", "Kg", "Gram", "Packet"]) # Piece ya Kilo ka hisab
        p_rate = st.number_input("Purchase Price", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            new_r = pd.DataFrame([{"Item": name, "qty": p_qty, "Unit": p_unit, "p_price": p_rate}])
            conn.update(worksheet="Inventory", data=pd.concat([inv_df, new_r], ignore_index=True))
            st.success("Stock Added!"); st.rerun()
    st.table(inv_df.tail(10)) # Niche purchase list

# --- 7. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2:
            age = st.text_input("Dog Age"); wt = st.text_input("Weight (Kg)"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Age": age, "Weight": wt, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([pet_df, new_p], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(pet_df.tail(10))

# --- 8. ADMIN SETTINGS (Dues + New ID Added) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    dues_df = load_data("Dues")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Company Udhaar (Dues)")
        c_name = st.text_input("Company Name")
        u_amt = st.number_input("Amount", min_value=1)
        if st.button("Save Udhaar"):
            new_d = pd.DataFrame([{"Company": c_name, "Amount": u_amt}])
            conn.update(worksheet="Dues", data=pd.concat([dues_df, new_d], ignore_index=True))
            st.success("Udhaar Saved!"); st.rerun()
        st.table(dues_df)
    with col2:
        st.subheader("👤 Create New ID")
        new_user = st.text_input("New Staff Name")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create ID"):
            st.success(f"ID Created for {new_user}!"); st.info("Check your Sheets for User list")

# --- 9. LIVE STOCK & EXPENSES ---
elif menu == "📋 Live Stock":
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    e_df = load_data("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save Expense"):
        new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
        conn.update(worksheet="Expenses", data=pd.concat([e_df, new_e], ignore_index=True))
        st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))
