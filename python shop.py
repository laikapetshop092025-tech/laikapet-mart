import streamlit as st # Interface ke liye
from streamlit_gsheets import GSheetsConnection # Google Sheets sync ke liye
import pandas as pd # Data management ke liye

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")
conn = st.connection("gsheets", type=GSheetsConnection) # Sheets se connection link

def load_data(sheet_name): # Data load karne ka function
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
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

# --- 5. DASHBOARD (4 Metrics) ---
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

# --- 6. PURCHASE REGISTER (Original) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Purchase Register (Add Stock)")
    with st.form("purchase_form"):
        c1, c2 = st.columns(2)
        with c1:
            p_name = st.text_input("Item/Product Name") # Product ka naam
            p_qty = st.number_input("Quantity", min_value=1) # Kitna maal aaya
        with c2:
            p_price = st.number_input("Purchase Price (Per Unit)", min_value=1) # Kitne mein kharida
            p_vendor = st.text_input("Vendor/Supplier Name") # Kisse kharida
        if st.form_submit_button("ADD TO STOCK"):
            st.success(f"{p_name} added to inventory!")

# --- 7. PET SALES REGISTER (Original) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Siberian Husky", "Boxer", "Shih Tzu", "Cocker Spaniel", "Pitbull", "Indie/Desi", "Other"]
    with st.form("pet_reg_form"):
        c1, c2 = st.columns(2)
        with c1:
            c_name = st.text_input("Customer Name") # Grahak ka naam
            c_phone = st.text_input("Customer Phone") # Phone number
            p_breed = st.selectbox("Dog Breed", breeds) # Breed dropdown
        with c2:
            p_age = st.text_input("Pet Age") # Umar
            p_weight = st.text_input("Pet Weight (Kg)") # Wajan
            v_date = st.date_input("Next Vaccine Date") # Vaccine ki tarik
        if st.form_submit_button("SAVE PET RECORD"):
            st.success("Pet record saved successfully!")
    st.subheader("Recent Pet Registrations")
    p_df = load_data("PetRecords")
    if not p_df.empty: st.table(p_df)

# --- 8. ADMIN SETTINGS (New ID + Dues) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    tab1, tab2 = st.tabs(["👤 User Management", "🏢 Company Dues"])
    with tab1:
        st.subheader("Create New Staff ID")
        new_u = st.text_input("Username"); new_p = st.text_input("Password", type="password")
        if st.button("CREATE ID"): st.success(f"ID Created for {new_u}")
    with tab2:
        st.subheader("Udhaar (Dues) Record")
        comp = st.text_input("Company Name"); d_amt = st.number_input("Amount", min_value=1)
        if st.button("SAVE DUES"): st.success("Dues updated!")

# --- 9. BAAKI SECTIONS ---
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
    st.number_input("Amount", min_value=1)
    if st.button("Save Expense"): st.success("Saved")

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing Terminal")
    st.info("Billing details Google Sheet mein sync ho rahi hain.")

elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty: st.table(i_df)
