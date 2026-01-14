import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA INITIALIZATION ---
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []

# --- LOGIN SECTION ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing (Items)", "📦 Purchase", "📋 Live Stock", "⚙️ Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- NEW PET SALES & VACCINE REGISTER ---
if menu == "🐾 Pet Sales Register":
    st.title("Janwar Bikri aur Vaccine Register")
    
    with st.form("pet_sale_form", clear_on_submit=True):
        st.subheader("Nayi Bikri ki Entry (Press TAB to move, ENTER to save)")
        col1, col2 = st.columns(2)
        
        with col1:
            c_name = st.text_input("Customer ka Naam")
            c_phone = st.text_input("Phone Number")
            pet_type = st.text_input("Kaun sa Janwar (e.g. Labrador Dog)")
            sale_price = st.number_input("Kitne mein Becha (Price)", min_value=0)
        
        with col2:
            last_vac = st.text_input("Kaun si Vaccine lag chuki hai?")
            vac_date = st.date_input("Vaccine Lagne ki Tarikh", datetime.now())
            next_vac_date = st.date_input("Agli Vaccine ki Tarikh", datetime.now() + timedelta(days=30))
            remark = st.text_area("Koi aur baat (Remarks)")
            
        if st.form_submit_button("Record Save Karein"):
            st.session_state.pet_records.append({
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Customer": c_name,
                "Phone": c_phone,
                "Pet": pet_type,
                "Price": sale_price,
                "Last Vaccine": last_vac,
                "Next Due": next_vac_date,
                "Notes": remark
            })
            st.success(f"✅ {c_name} ko {pet_type} bechne ka record save ho gaya!")

    st.subheader("📋 Sabhi Bikri aur Vaccine Records")
    if st.session_state.pet_records:
        df_pets = pd.DataFrame(st.session_state.pet_records)
        st.dataframe(df_pets, use_container_width=True)
        
        # Search Feature
        search = st.text_input("Phone ya Naam se search karein")
        if search:
            filtered_df = df_pets[df_pets.apply(lambda row: search in str(row.values), axis=1)]
            st.write("Search Results:")
            st.table(filtered_df)
    else:
        st.info("Abhi tak koi record nahi hai.")

# --- REST OF THE CODE (Billing, Stock etc. remains same) ---
elif menu == "📊 Dashboard":
    st.title("Dukan Dashboard")
    st.metric("Total Pets Sold", len(st.session_state.pet_records))
    # ... baki dashboard details
