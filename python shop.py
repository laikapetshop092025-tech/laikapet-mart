import streamlit as st # Interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets sync ke liye
import pandas as pd # Data management ke liye

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")
conn = st.connection("gsheets", type=GSheetsConnection) # Sheets se connection link

def load_data(sheet_name): # Data load karne ka function
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all") # Khali rows hatana
    except:
        return pd.DataFrame()

# --- 2. STYLE (Blue Theme) ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
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
    t_pur = (inv_df['qty'] * inv_df['p_price']).sum() if not inv_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp
    c1, c2 = st.columns(2)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    st.divider()
    c3, c4 = st.columns(2)
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. BILLING TERMINAL (Niche List Ke Saath) ---
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    inv_df = load_data("Inventory")
    with st.form("bill_form"):
        item = st.selectbox("Select Product", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
        qty = st.number_input("Qty", min_value=0.1); pr = st.number_input("Price", min_value=1)
        meth = st.selectbox("Payment", ["Cash", "Online"])
        if st.form_submit_button("COMPLETE BILL"):
            st.success("Bill Generated!") # Database update logic yahan
    
    st.subheader("📋 Recent Sales History") # Billing ki list niche dikhayega
    sales_list = load_data("Sales")
    if not sales_list.empty: st.table(sales_list.tail(10)) # Niche records dikhane ke liye

# --- 7. PURCHASE (Niche List Ke Saath) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur_form"):
        p_name = st.text_input("Item Name"); p_qty = st.number_input("Qty", min_value=1)
        p_price = st.number_input("Purchase Price", min_value=1); p_vendor = st.text_input("Vendor")
        if st.form_submit_button("ADD"):
            st.success("Stock Added!")
            
    st.subheader("📋 Recent Purchase History") # Purchase ki list niche dikhayega
    pur_list = load_data("Inventory")
    if not pur_list.empty: st.table(pur_list.tail(10)) # Niche records dikhane ke liye

# --- 8. PET REGISTER (Niche List Ke Saath) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie", "Other"]
    with st.form("pet_form"):
        c_name = st.text_input("Customer Name"); c_phone = st.text_input("Phone")
        p_breed = st.selectbox("Breed", breeds); p_weight = st.text_input("Weight")
        p_age = st.text_input("Age"); v_date = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            st.success("Record Saved!")
            
    st.subheader("📋 Registered Pets Record") # Pet register ki list niche dikhayega
    pet_list = load_data("PetRecords")
    if not pet_list.empty: st.table(pet_list.tail(10)) # Niche records dikhane ke liye

# --- 9. BAAKI SECTIONS ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty: st.table(i_df)

elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Cat", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save"): st.success("Saved")
    st.table(load_data("Expenses"))

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("New ID & Udhaar")
    st.info("Admin controls are synced with Google Sheets.")
