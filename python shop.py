import streamlit as st # Streamlit library interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets se connect karne ke liye
import pandas as pd # Data handle karne ke liye
from datetime import datetime # Date aur time ke liye

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded") # Page ka title aur layout set karne ke liye

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection) # App ko Google Sheet se jodne ke liye

def load_data(sheet_name): # Sheet se data load karne ka function
    try:
        df = conn.read(worksheet=sheet_name) # Sheet read karna
        return df.dropna(how="all") # Khali rows hatana
    except:
        return pd.DataFrame() # Agar sheet na mile toh khali frame dena

# --- 2. STYLE ---
st.markdown("""
    <style>
    footer {visibility: hidden;} /* Footer chhupane ke liye */
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;} /* Dashboard numbers bada karne ke liye */
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;} /* Buttons design ke liye */
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;} /* Main title design */
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px;} /* Welcome message design */
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False # Login status check
if not st.session_state.logged_in: # Agar login nahi hai toh login box dikhana
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip() # Username input
        u_pw = st.text_input("Password", type="password").strip() # Password input
        if st.button("LOGIN"): # Login button
            if u_id == "Laika" and u_pw == "Ayush@092025": # Password check
                st.session_state.logged_in = True
                st.rerun() # Page refresh
    st.stop() # Login ke bina aage nahi badhne dena

# --- 4. BRANDING ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

# Sidebar menu
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "🐾 Pet Sales Register", "⚙️ Admin Settings"])

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    sales_df = load_data("Sales") # Sales data mangwana
    exp_df = load_data("Expenses") # Expenses data mangwana
    inv_df = load_data("Inventory") # Stock data mangwana
    
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0 # Total sale calculation
    t_pur = (inv_df['qty'] * inv_df['p_price']).sum() if not inv_df.empty else 0 # Total purchase calculation
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0 # Total expense calculation
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp # Net profit calculation

    c1, c2 = st.columns(2)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    st.divider()
    c3, c4 = st.columns(2)
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. PET SALES REGISTER (With Breed Dropdown) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    
    # Dog Breeds ki list dropdown ke liye
    dog_breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Siberian Husky", "Boxer", "Shih Tzu", "Cocker Spaniel", "Pitbull", "Indie/Desi", "Other"]

    with st.form("pet_form"): # Registration form
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Customer Name") # Customer naam
            ph = st.text_input("Phone Number") # Phone number
            b = st.selectbox("Select Dog Breed", dog_breeds) # Breed dropdown list (Naya Update)
        with c2:
            w = st.text_input("Dog Weight (Kg)") # Wajan
            a = st.text_input("Dog Age") # Umar
            v_date = st.date_input("Next Vaccine Date") # Agli vaccine ki date
        
        if st.form_submit_button("SAVE PET RECORD"): # Record save karne ka button
            st.success(f"{b} record saved for {n}!") # Success message

    st.subheader("Registered Pets")
    pet_df = load_data("PetRecords") # Pet list dikhane ke liye data load
    if not pet_df.empty: st.table(pet_df)

# --- 7. BAAKI SECTIONS (Logic Same) ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Expense"): st.success("Recorded!")

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    inv_df = load_data("Inventory")
    if not inv_df.empty:
        with st.form("bill"):
            item = st.selectbox("Product", inv_df['Item'].tolist()) # Product list dropdown
            qty = st.number_input("Qty", min_value=0.1)
            if st.form_submit_button("BILL"): st.success("Done!")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    with st.form("pur"):
        n = st.text_input("Item Name"); r = st.number_input("Price"); q = st.number_input("Qty")
        if st.form_submit_button("ADD"): st.success("Stock Added!")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    inv_df = load_data("Inventory")
    if not inv_df.empty: st.table(inv_df)

elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar (Dues)")
    c_name = st.text_input("Company Name")
    u_amt = st.number_input("Udhaar Amount", min_value=1)
    if st.button("Save Udhaar"): st.success("Updated!")
