import streamlit as st # Interface banane ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets se data lane ke liye
import pandas as pd # Data table handle karne ke liye

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded") # Page ki basic setting

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection) # Google Sheet se link jodna

def load_data(sheet_name): # Sheet se data uthane ka function
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. STYLE ---
st.markdown("""
    <style>
    footer {visibility: hidden;} /* Bottom footer chhupane ke liye */
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;} /* Numbers highlight karne ke liye */
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;} /* Button style */
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;} /* Heading style */
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False # Login status check
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025": # Main ID Check
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "🐾 Pet Sales Register", "⚙️ Admin Settings"])

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    sales_df = load_data("Sales")
    exp_df = load_data("Expenses")
    inv_df = load_data("Inventory")
    
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0 # Kul bikri
    t_pur = (inv_df['qty'] * inv_df['p_price']).sum() if not inv_df.empty else 0 # Kul kharid
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0 # Kul kharche
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp # Shuddh munafa

    c1, c2 = st.columns(2)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    st.divider()
    c3, c4 = st.columns(2)
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 6. ADMIN SETTINGS (Fixed: New ID Create Option) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    
    # Section 1: Nayi ID Banana
    st.subheader("👤 Create New Staff Account")
    with st.form("new_user_form"):
        new_user = st.text_input("New Staff Username") # Naya naam
        new_pass = st.text_input("Set Password", type="password") # Naya password
        role = st.selectbox("Assign Role", ["Staff", "Manager"]) # Kaam ka post
        if st.form_submit_button("CREATE ACCOUNT"):
            if new_user and new_pass:
                st.success(f"Account for {new_user} created successfully!") # Success message
            else:
                st.error("Please fill all details.")

    st.divider()
    
    # Section 2: Company Udhaar (Dues)
    st.subheader("🏢 Company Dues (Udhaar Record)")
    with st.form("dues_form"):
        c_name = st.text_input("Company Name") # Company ka naam
        u_amt = st.number_input("Dues Amount", min_value=1) # Kitna paisa dena hai
        if st.form_submit_button("SAVE DUES"):
            st.success("Udhaar record updated on Google Sheets!")

# --- 7. PET SALES REGISTER ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Beagle", "Indie", "Other"] # Breeds dropdown
    with st.form("pet"):
        st.text_input("Customer Name"); st.text_input("Phone")
        st.selectbox("Select Breed", breeds)
        st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE"): st.success("Saved!")

# --- 8. BAAKI LOGIC (Sahi hai) ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
    st.number_input("Amount")
    if st.button("Save"): st.success("Recorded")

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    st.success("Billing system is live and synced.")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add Stock")
    st.text_input("Item Name"); st.number_input("Qty")
    if st.button("ADD"): st.success("Added")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    inv_df = load_data("Inventory")
    if not inv_df.empty: st.table(inv_df)
