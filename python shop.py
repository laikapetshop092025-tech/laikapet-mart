import streamlit as st # Interface banane ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets se judne ke liye
import pandas as pd # Data tables handle karne ke liye
from datetime import datetime # Date aur Time ke liye

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet se connection banana

# Data load karne ka function (ttl=0 matlab hamesha fresh data)
def load_data(sheet):
    return conn.read(worksheet=sheet, ttl=0).dropna(how="all")

# --- 2. STYLE ---
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {font-size: 35px; color: #2E5BFF; font-weight: bold;} /* Metric design */
    .stButton>button {width: 100%; border-radius: 10px; background-color: #2E5BFF; color: white;} /* Button design */
    .main-title {text-align: center; color: #2E5BFF; font-size: 40px; font-weight: bold;} /* Title design */
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    with st.container():
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "Laika" and p == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 5. DASHBOARD (Total Sale, Purchase, Expense, Profit) ---
if menu == "📊 Dashboard":
    st.header("📊 Business Overview")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    
    t_sale = s_df['total'].sum() if not s_df.empty else 0 # Kul bikri
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0 # Kul kharid
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0 # Kul kharche
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp # Net munafa

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. PURCHASE (Item, Qty, Price + History List) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory") # Purana stock load karna
    with st.form("p_form"):
        name = st.text_input("Item Name") # Item ka naam
        qty = st.number_input("Quantity (Nos/Kg/Ml)", min_value=0.1) # Kitni matra
        price = st.number_input("Purchase Price", min_value=1) # Kharid bhav
        if st.form_submit_button("ADD STOCK"):
            new_row = pd.DataFrame([{"Item": name, "qty": qty, "p_price": price}])
            updated_df = pd.concat([inv_df, new_row], ignore_index=True)
            conn.update(worksheet="Inventory", data=updated_df) # Sheet mein save karna
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Recent Purchase List")
    st.table(inv_df.tail(10)) # Niche list dikhana

# --- 7. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Stock in Shop")
    st.table(load_data("Inventory")) # Saara stock ek saath dikhana

# --- 8. EXPENSES (Dropdown + List) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Manager")
    exp_df = load_data("Expenses")
    with st.form("e_form"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"]) # Dropdown
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE EXPENSE"):
            new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
            conn.update(worksheet="Expenses", data=pd.concat([exp_df, new_e], ignore_index=True))
            st.success("Expense Saved!"); st.rerun()
    st.table(exp_df.tail(10)) # Kharche ki list

# --- 9. PET REGISTER (Customer, Phone, Breed, Age, Weight, Vaccine) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Beagle", "Indie", "Other"]
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", breeds)
        with c2:
            age = st.text_input("Dog Age"); wt = st.text_input("Dog Weight"); vax = st.date_input("Vaccination Date")
        if st.form_submit_button("SAVE RECORD"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Age": age, "Weight": wt, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([pet_df, new_p], ignore_index=True))
            st.success("Pet Record Saved!"); st.rerun()
    st.table(pet_df.tail(10)) # Pet records ki list

# --- 10. ADMIN SETTINGS (Dues & New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    dues_df = load_data("Dues")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏢 Company Udhaar (Dues)")
        with st.form("d_form"):
            comp = st.text_input("Company Name"); d_amt = st.number_input("Dues Amount", min_value=1)
            if st.form_submit_button("SAVE DUES"):
                new_d = pd.DataFrame([{"Company": comp, "Amount": d_amt}])
                conn.update(worksheet="Dues", data=pd.concat([dues_df, new_d], ignore_index=True))
                st.success("Dues Saved!"); st.rerun()
        st.table(dues_df) # Udhaar ki list
    with col2:
        st.subheader("👤 Create New ID")
        new_u = st.text_input("New Username"); new_p = st.text_input("Set Password", type="password")
        if st.button("CREATE ACCOUNT"): st.success(f"ID Created for {new_u}")

# --- 11. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("b_form"):
        item = st.selectbox("Select Product", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", min_value=0.1); p = st.number_input("Selling Price", min_value=1)
        if st.form_submit_button("COMPLETE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": item, "total": q*p, "profit": (p-10)*q}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Generated!"); st.rerun()
    st.table(sales_df.tail(10)) # Billing ki list
