import streamlit as st # Interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets connect karne ke liye
import pandas as pd # Data tables ke liye
from datetime import datetime # Date-Time ke liye

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet link

# Data load karne ka function (Hamesha naya data dikhane ke liye ttl=0)
def load_data(sheet):
    return conn.read(worksheet=sheet, ttl=0).dropna(how="all")

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

# --- 3. NAVIGATION ---
st.markdown("<h1 style='text-align: center; color: #2E5BFF;'>LAIKA PET MART</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (4 Metrics: Sale, Purchase, Expense, Profit) ---
if menu == "📊 Dashboard":
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    # Total calculation
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = (s_df['profit'].sum() if not s_df.empty else 0) - t_exp

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. PURCHASE (Item, Qty, Price + History List) ---
elif menu == "📦 Purchase":
    st.header("📦 Add New Stock")
    inv_df = load_data("Inventory")
    with st.form("p_f"):
        name = st.text_input("Item Name") # Item ka naam
        qty = st.number_input("Quantity (Nos/Kg/Ml)", min_value=0.1) # Kitni matra
        price = st.number_input("Purchase Price", min_value=1) # Kharid bhav
        if st.form_submit_button("ADD STOCK"):
            new_r = pd.DataFrame([{"Item": name, "qty": qty, "p_price": price}])
            conn.update(worksheet="Inventory", data=pd.concat([inv_df, new_r], ignore_index=True))
            st.success("Stock Added!"); st.rerun()
    st.table(inv_df.tail(10)) # Niche list dikhegi

# --- 6. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 All Shop Stock")
    st.table(load_data("Inventory")) # Poori list

# --- 7. EXPENSES (Dropdown + Miscellaneous) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    exp_df = load_data("Expenses")
    with st.form("e_f"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"]) # Dropdown
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE"):
            new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
            conn.update(worksheet="Expenses", data=pd.concat([exp_df, new_e], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(exp_df.tail(10)) # Niche list dikhegi

# --- 8. PET REGISTER (Phone, Breed, Age, Weight, Vaccine) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Customer & Pet Record")
    pet_df = load_data("PetRecords")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Beagle", "Other"]
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", breeds)
        with c2:
            age = st.text_input("Dog Age"); wt = st.text_input("Dog Weight"); vax = st.date_input("Vaccination Date")
        if st.form_submit_button("SAVE PET"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Age": age, "Weight": wt, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([pet_df, new_p], ignore_index=True))
            st.success("Record Saved!"); st.rerun()
    st.table(pet_df.tail(10)) # Niche list dikhegi

# --- 9. ADMIN SETTINGS (Dues & New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    dues_df = load_data("Dues")
    with st.expander("🏢 Company Udhaar (Dues)"):
        comp = st.text_input("Company Name"); d_amt = st.number_input("Dues Amount", min_value=1)
        if st.button("Save Dues"):
            new_d = pd.DataFrame([{"Company": comp, "Amount": d_amt}])
            conn.update(worksheet="Dues", data=pd.concat([dues_df, new_d], ignore_index=True))
            st.success("Saved!"); st.rerun()
        st.table(dues_df) # Udhaar ki list
    with st.expander("👤 Create New Staff ID"):
        st.text_input("New Username"); st.text_input("New Password", type="password")
        if st.button("Create"): st.success("Account Ready!")

# --- 10. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Generate Bill")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("b_form"):
        item = st.selectbox("Item", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", min_value=0.1); p = st.number_input("Selling Price", min_value=1)
        if st.form_submit_button("BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": item, "total": q*p, "profit": (p-10)*q}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Done!"); st.rerun()
    st.table(sales_df.tail(10)) # Billing ki list
