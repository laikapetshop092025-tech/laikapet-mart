import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# CSS for App Look
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #4A90E2; color: white; font-weight: bold;}
    .main {background-color: #f8f9fa;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'last_activity' not in st.session_state: st.session_state.last_activity = time.time()
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}

# --- 3. AUTO-LOGOUT LOGIC (10 Minutes) ---
if st.session_state.logged_in:
    current_time = time.time()
    if current_time - st.session_state.last_activity > 600: # 10 mins
        st.session_state.logged_in = False
        st.rerun()
    else:
        st.session_state.last_activity = current_time

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id in st.session_state.users and st.session_state.users[u_id] == u_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = u_id
                st.session_state.last_activity = time.time()
                st.rerun()
            else:
                st.error("Invalid ID or Password!")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.title("🐾 Navigation")
menu = st.sidebar.radio("Go to:", [
    "📊 Dashboard", 
    "🐾 Pet Sales Register", 
    "🧾 Billing Terminal", 
    "📦 Purchase (Add Stock)", 
    "📋 Live Stock", 
    "💰 Expenses",
    "⚙️ Admin Settings"
])

if st.sidebar.button("🔴 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 6. PET SALES REGISTER (FIXED & DETAILED) ---
if menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Sale & Health Register")
    
    dog_breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Siberian Husky", "Doberman", "Indie/Desi", "Other"]
    
    with st.form("pet_sale_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            c_name = st.text_input("Customer Name")
            c_phone = st.text_input("Contact Number")
            breed = st.selectbox("Select Dog Breed", dog_breeds)
        with c2:
            age = st.text_input("Age (e.g. 2 Months)")
            weight = st.text_input("Weight (kg)")
            next_vaccine = st.date_input("Next Vaccine Date", min_value=datetime.now())
        
        notes = st.text_area("Additional Notes (Health/Vaccine details)")
        
        if st.form_submit_button("SAVE RECORD"):
            if c_name and c_phone:
                st.session_state.pet_records.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Customer": c_name,
                    "Contact": c_phone,
                    "Breed": breed,
                    "Age": age,
                    "Weight": weight,
                    "Next Vaccine": next_vaccine.strftime("%Y-%m-%d"),
                    "Notes": notes
                })
                st.success(f"Record for {c_name} saved!")
                st.rerun()
            else:
                st.error("Customer Name aur Phone zaroori hai!")

    st.write("---")
    st.subheader("📋 Saved Pet Records")
    if st.session_state.pet_records:
        df_pets = pd.DataFrame(st.session_state.pet_records)
        st.dataframe(df_pets, use_container_width=True)
        
        # Delete Option for Records
        for i, p in enumerate(st.session_state.pet_records):
            if st.button(f"🗑️ Delete {p['Customer']}'s Record", key=f"pet_{i}"):
                st.session_state.pet_records.pop(i)
                st.rerun()
    else:
        st.info("Abhi tak koi record nahi hai.")

# --- 7. ADMIN SETTINGS (FIXED) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Controls")
    
    # Error Fix: Key exists check
    st.subheader("Manage Staff Accounts")
    with st.form("admin_user_form"):
        new_u = st.text_input("New Staff Username")
        new_p = st.text_input("New Staff Password")
        if st.form_submit_button("Add Staff Account"):
            if new_u and new_p:
                st.session_state.users[new_u] = new_p
                st.success(f"Account created for {new_u}")
            else:
                st.error("Dono fields bharna zaroori hai!")
    
    st.write("### Active Accounts:")
    for user in st.session_state.users.keys():
        st.write(f"- {user}")

# --- 8. DASHBOARD & OTHER SECTIONS (Billing, Purchase, Stock, Expenses) ---
elif menu == "📊 Dashboard":
    st.title("📊 Business Summary")
    t_rev = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("REVENUE", f"₹{t_rev}")
    c2.metric("EXPENSES", f"₹{t_exp}")
    c3.metric("NET PROFIT", f"₹{t_prof}")
    
    if st.session_state.sales:
        csv = pd.DataFrame(st.session_state.sales).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sales Data", csv, "sales.csv", "text/csv")

elif menu == "🧾 Billing Terminal":
    st.title("🧾 Generate Bill")
    if not st.session_state.inventory:
        st.warning("Stock khali hai! Pehle Purchase mein maal add karein.")
    else:
        with st.form("bill_form"):
            item = st.selectbox("Product", list(st.session_state.inventory.keys()))
            qty = st.number_input("Quantity", min_value=0.1)
            price = st.number_input("Selling Price", min_value=1)
            if st.form_submit_button("Finish Bill"):
                inv = st.session_state.inventory[item]
                if qty <= inv['qty']:
                    st.session_state.inventory[item]['qty'] -= qty
                    profit = (price - inv['p_price']) * qty
                    st.session_state.sales.append({"Date": datetime.now(), "Item": item, "Total": qty*price, "profit": profit})
                    st.success("Bill Generated!")
                    st.rerun()
                else: st.error("Stock khatam!")

elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Inventory Purchase")
    with st.form("p_form"):
        name = st.text_input("Item Name")
        buy_p = st.number_input("Purchase Price", min_value=1)
        qty = st.number_input("Quantity", min_value=1)
        if st.form_submit_button("Add to Stock"):
            if name in st.session_state.inventory: st.session_state.inventory[name]['qty'] += qty
            else: st.session_state.inventory[name] = {'qty': qty, 'p_price': buy_p}
            st.success("Added!")
            st.rerun()

elif menu == "📋 Live Stock":
    st.title("📋 Current Inventory")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Qty": v['qty'], "Price": v['p_price']} for k, v in st.session_state.inventory.items()]))

elif menu == "💰 Expenses":
    st.title("💰 Shop Expenses")
    e_name = st.text_input("Expense Name")
    e_amt = st.number_input("Amount", min_value=1)
    if st.button("Add Expense"):
        st.session_state.expenses.append({"Date": datetime.now(), "Item": e_name, "Amount": e_amt})
        st.rerun()
    st.write(st.session_state.expenses)
