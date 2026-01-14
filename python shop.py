import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. PAGE SETUP & LOGO ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# LOGO LAGANE KI JAGAH: 
# Apne logo ki file (jaise 'logo.png') ko GitHub par upload karein aur niche naam badal dein.
# Agar file nahi hai, toh ye sirf naam dikhayega.
col_l, col_r = st.columns([1, 5])
with col_l:
    # Yahan aap apna logo laga sakte hain: st.image("logo.png", width=100)
    st.title("🐾") 
with col_r:
    st.title("LAIKA PET MART - Management System")

# --- 2. DATABASE INITIALIZATION ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'pet_records' not in st.session_state: st.session_state.pet_records = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.subheader("🔐 Please Login to Continue")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.logged_in = True
            st.session_state.current_user = u
            st.rerun()
    st.stop()

# --- 4. SIDEBAR MENU ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🐾 Pet Sales", "🧾 Sales Entry (Billing)", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Settings"])

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.subheader("🚀 Business Overview")
    t_sales = sum(s.get('total', 0) for s in st.session_state.sales)
    t_exp = sum(e.get('Amount', 0) for e in st.session_state.expenses)
    t_prof = sum(s.get('profit', 0) for s in st.session_state.sales) - t_exp
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALES", f"₹{int(t_sales)}")
    c2.metric("PETS SOLD", len(st.session_state.pet_records))
    c3.metric("NET PROFIT", f"₹{int(t_prof)}")
    c4.metric("EXPENSES", f"₹{int(t_exp)}")

# --- 6. PET SALES (With Dropdown) ---
elif menu == "🐾 Pet Sales":
    st.subheader("🐾 Pet Sales & Registration")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Rottweiler", "Doberman", "Indie/Desi", "Persian Cat", "Siamese Cat", "Other"]
    
    with st.form("pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Customer Name")
            phone = st.text_input("Phone Number")
        with c2:
            breed_sel = st.selectbox("Select Pet Breed (Dropdown)", breeds)
            next_v = st.date_input("Next Vaccine Due", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("SAVE PET RECORD"):
            st.session_state.pet_records.append({"Date": datetime.now().date(), "Customer": name, "Phone": phone, "Breed": breed_sel, "Due": next_v})
            st.success(f"{breed_sel} record saved!")
            
    if st.session_state.pet_records:
        st.table(pd.DataFrame(st.session_state.pet_records))

# --- 7. SALES ENTRY (Billing & Unit Fix) ---
elif menu == "🧾 Sales Entry (Billing)":
    st.subheader("🧾 Create Sales Invoice")
    if not st.session_state.inventory:
        st.warning("Pehle Purchase mein maal add karein!")
    else:
        with st.form("billing_form", clear_on_submit=True):
            item = st.selectbox("Kaunsa Item Becha?", list(st.session_state.inventory.keys()))
            info = st.session_state.inventory[item]
            
            c1, c2, c3 = st.columns(3)
            with c1:
                u_sell = st.selectbox("Unit", ["KG", "PCS/Packet"])
            with c2:
                # Direct amount input (no 0.00 mess)
                q_sell = st.number_input("Quantity", min_value=1, value=1, step=1)
            with c3:
                s_price = st.number_input("Rate (₹)", min_value=1, value=100, step=1)
            
            cust = st.text_input("Customer Name (Optional)")
            
            if st.form_submit_button("COMPLETE SALE & GENERATE BILL"):
                avail = info.get('qty', 0)
                if q_sell <= avail:
                    st.session_state.inventory[item]['qty'] -= q_sell
                    total_amt = q_sell * s_price
                    profit_amt = (s_price - info.get('p_price', 0)) * q_sell
                    
                    sale_data = {"Date": datetime.now().strftime("%d/%m/%Y"), "Item": item, "Qty": q_sell, "Unit": u_sell, "total": total_amt, "profit": profit_amt}
                    st.session_state.sales.append(sale_data)
                    
                    # BILL DISPLAY
                    st.markdown("---")
                    st.success("Sale Successful!")
                    st.subheader("📄 INVOICE - LAIKA PET MART")
                    st.write(f"*Customer:* {cust if cust else 'Cash Customer'}")
                    st.write(f"*Item:* {item} ({q_sell} {u_sell})")
                    st.write(f"### *Total: ₹{total_amt}*")
                    st.markdown("---")
                else:
                    st.error(f"Stock Kam Hai! Sirf {avail} bacha hai.")

# --- 8. PURCHASE (Fix) ---
elif menu == "📦 Purchase (Add Stock)":
    st.subheader("📦 Add New Stock to Inventory")
    with st.form("pur_f", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Item Name")
            u = st.selectbox("Default Unit", ["KG", "PCS"])
        with col2:
            rate = st.number_input("Purchase Rate (₹)", min_value=1, step=1)
            q = st.number_input("Quantity", min_value=1, step=1)
        if st.form_submit_button("ADD STOCK"):
            if n in st.session_state.inventory: st.session_state.inventory[n]['qty'] += q
            else: st.session_state.inventory[n] = {'p_price': rate, 'qty': q, 'unit': u}
            st.success("Stock Added!")
    
    if st.session_state.inventory:
        st.write("### Current Inventory List")
        st.table(pd.DataFrame([{"Item": k, "Stock": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))

# --- 9. SETTINGS (Blank Screen Fix) ---
elif menu == "⚙️ Settings":
    st.subheader("⚙️ Admin Settings")
    st.write(f"*Current User:* {st.session_state.get('current_user')}")
    
    with st.expander("Create New Staff Account"):
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password")
        if st.button("Create Account"):
            st.session_state.users[new_u] = new_p
            st.success("Staff Account Created!")
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- LIVE STOCK & EXPENSES ---
elif menu == "📋 Live Stock":
    st.subheader("📋 Current Live Stock Report")
    if st.session_state.inventory:
        st.table(pd.DataFrame([{"Item": k, "Available Qty": v['qty'], "Unit": v['unit']} for k, v in st.session_state.inventory.items()]))
    else: st.info("Stock Khali Hai.")

elif menu == "💰 Expenses":
    st.subheader("💰 Expense Tracker")
    with st.form("exp_f"):
        reason = st.text_input("Expense Detail")
        amt = st.number_input("Amount", min_value=1, step=1)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"Reason": reason, "Amount": amt, "Date": datetime.now().date()})
    if st.session_state.expenses:
        st.table(pd.DataFrame(st.session_state.expenses))
