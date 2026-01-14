import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. SETTINGS: Page setup ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- 2. DATABASE: Data save karne ke liye ---
if 'shop_name' not in st.session_state: st.session_state.shop_name = "LAIKA PET MART"
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title(f"🔐 {st.session_state.shop_name} - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Galt ID ya Password!")
    st.stop()

# --- 4. SIDEBAR MENU ---
st.sidebar.title(f"🐾 {st.session_state.shop_name}")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales Register", "🧾 Billing", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 5. DASHBOARD SECTION ---
if menu == "📊 Dashboard":
    st.title(f"📊 {st.session_state.shop_name} Dashboard")
    t_sales = sum(s['total'] for s in st.session_state.sales)
    t_exp = sum(e['Amount'] for e in st.session_state.expenses)
    t_pur = sum(v['p_price'] * v['qty'] for v in st.session_state.inventory.values())
    net_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL SALES", f"Rs. {t_sales}")
    col2.metric("TOTAL PURCHASE", f"Rs. {t_pur}")
    col3.metric("NET PROFIT", f"Rs. {net_prof}")
    col4.metric("PETS SOLD", f"{len(st.session_state.pet_records)}")

# --- 6. PET SALES REGISTER (Isse screen khali nahi hogi) ---
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Sales & Vaccine Record")
    with st.form("pet_sale_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name")
        c_phone = st.text_input("Phone Number")
        pet_detail = st.text_input("Pet Breed/Age")
        v_name = st.text_input("Vaccine Name")
        next_v = st.date_input("Agli Vaccine Date", datetime.now() + timedelta(days=30))
        if st.form_submit_button("Save Pet Record"):
            st.session_state.pet_records.append({
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Customer": c_name, "Phone": c_phone, "Pet": pet_detail,
                "Vaccine": v_name, "Next Due": next_v
            })
            st.success("Record Saved!")
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. BILLING SECTION ---
elif menu == "🧾 Billing":
    st.title("🧾 Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase section mein jaakar Stock bhariye!")
    else:
        with st.form("billing_form", clear_on_submit=True):
            item_sel = st.selectbox("Product Chunein", list(st.session_state.inventory.keys()))
            avail = st.session_state.inventory[item_sel]['qty']
            st.write(f"Stock available: {avail}")
            sell_qty = st.number_input("Quantity", min_value=0.1, max_value=float(avail) if avail > 0 else 0.1)
            sell_price = st.number_input("Selling Price (Is baar ka rate)", min_value=0.0)
            if st.form_submit_button("Generate Bill"):
                st.session_state.inventory[item_sel]['qty'] -= sell_qty
                tot = sell_qty * sell_price
                prof = tot - (sell_qty * st.session_state.inventory[item_sel]['p_price'])
                st.session_state.sales.append({"item": item_sel, "total": tot, "profit": prof, "date": datetime.now()})
                st.success(f"Bill Generated: Rs. {tot}")

# --- 8. PURCHASE SECTION (Isse screen khali nahi hogi) ---
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Add New Stock")
    with st.form("purchase_entry_form", clear_on_submit=True):
        p_name = st.text_input("Item Name")
        p_rate = st.number_input("Purchase Rate (Khareed)", min_value=0.0)
        p_qty = st.number_input("Quantity / Weight", min_value=0.0)
        if st.form_submit_button("Add to Stock"):
            if p_name:
                if p_name in st.session_state.inventory:
                    st.session_state.inventory[p_name]['qty'] += p_qty
                else:
                    st.session_state.inventory[p_name] = {'p_price': p_rate, 'qty': p_qty}
                st.success(f"{p_name} added to stock!")

# --- 9. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Inventory Report")
    if st.session_state.inventory:
        st.table(pd.DataFrame.from_dict(st.session_state.inventory, orient='index'))
    else:
        st.info("Stock khali hai.")

# --- 10. EXPENSES ---
elif menu == "💰 Expenses":
    st.title("💰 Expense Tracker")
    with st.form("expense_f", clear_on_submit=True):
        reason = st.text_input("Kharcha Detail")
        amount = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Reason": reason, "Amount": amount, "Date": datetime.now()})
            st.success("Expense Recorded!")
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))

# --- 11. ADMIN SETTINGS (Authority System) ---
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Authority Panel")
    if st.session_state.current_user == "Laika":
        new_name = st.text_input("Dukan ka Naam Badlein", value=st.session_state.shop_name)
        if st.button("Update Shop Name"):
            st.session_state.shop_name = new_name
            st.rerun()
            
        st.subheader("Nayi Staff ID Banayein")
        new_u = st.text_input("Staff Username")
        new_p = st.text_input("Staff Password", type="password")
        if st.button("Create ID"):
            st.session_state.users[new_u] = new_p
            st.success(f"ID {new_u} ban gayi!")
    else:
        st.warning("Sirf Admin (Laika) hi settings badal sakta hai.")
