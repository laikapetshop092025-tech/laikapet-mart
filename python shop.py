import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import os

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# AAPKA NAYA URL
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR (LOGO & WELCOME) ---
st.sidebar.markdown("<h3 style='text-align: center; color: #FF4B4B;'>👋 Welcome <br> Laika Pet Mart</h3>", unsafe_allow_html=True)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", use_container_width=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (COLORFUL & DYNAMIC) ---
if menu == "📊 Dashboard":
    today_str = datetime.now().strftime('%d %B, %Y')
    month_name = datetime.now().strftime('%B %Y')
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>📈 Business Dashboard</h2>", unsafe_allow_html=True)
    
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses")
    today_dt = datetime.now().date(); curr_m = datetime.now().month

    def get_stats(sales_df, inv_df, exp_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today_dt] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.date == today_dt] if not inv_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.date == today_dt] if not exp_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.month == curr_m] if not inv_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.month == curr_m] if not exp_df.empty else pd.DataFrame()
        
        t_sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum() if not s_sub.empty else 0
        t_pur = (pd.to_numeric(p_sub.iloc[:, 1], errors='coerce') * pd.to_numeric(p_sub.iloc[:, 3], errors='coerce')).sum() if not p_sub.empty else 0
        t_exp = pd.to_numeric(e_sub.iloc[:, 2], errors='coerce').sum() if not e_sub.empty else 0
        
        t_margin = 0
        if not s_sub.empty and not inv_df.empty:
            for _, row in s_sub.iterrows():
                item = row.iloc[1]
                try:
                    q_val = float(str(row.iloc[2]).split()[0]); s_val = float(row.iloc[3])
                    item_stock = inv_df[inv_df.iloc[:, 0] == item]
                    if not item_stock.empty:
                        p_rate = float(item_stock.iloc[-1, 3])
                        t_margin += (s_val - (p_rate * q_val))
                except: continue
        return t_sale, t_pur, t_margin, t_exp

    ts, tp, tm, te = get_stats(s_df, i_df, e_df, "today")
    ms, mp, mm, me = get_stats(s_df, i_df, e_df, "month")

    st.markdown(f"#### 📅 Today's Report: <span style='color: #FF4B4B;'>{today_str}</span>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.info(f"*Today Sale*\n### ₹{int(ts)}")
    with c2: st.warning(f"*Today Purchase*\n### ₹{int(tp)}")
    with c3: st.success(f"*Margin Profit*\n### ₹{int(tm)}")
    with c4: st.error(f"*Today Expense*\n### ₹{int(te)}")

    st.divider()

    st.markdown(f"#### 🗓️ Monthly Summary: <span style='color: #1E88E5;'>{month_name}</span>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.info(f"*Total Sale*\n### ₹{int(ms)}")
    with m2: st.warning(f"*Total Purchase*\n### ₹{int(mp)}")
    with m3: st.success(f"*Net Margin*\n### ₹{int(mm)}")
    with m4: st.error(f"*Total Expense*\n### ₹{int(me)}")

# --- 5. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        col1, col2 = st.columns(2)
        with col1: q = st.number_input("Quantity", 0.1)
        with col2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        pr = st.number_input("Selling Price")
        if st.form_submit_button("SAVE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {unit}", q*pr, "Paid"]); time.sleep(1); st.rerun()
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE"):
        if delete_data("Sales"): st.success("Deleted!"); time.sleep(1); st.rerun()

# --- 6. PURCHASE ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name")
        col1, col2 = st.columns(2)
        with col1: q = st.number_input("Quantity", 1)
        with col2: unit = st.selectbox("Unit", ["Pcs", "Kg"])
        p = st.number_input("Purchase Rate")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, unit, p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE"):
        if delete_data("Inventory"): st.success("Deleted!"); time.sleep(1); st.rerun()

# --- 7. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock (Automatic Inventory)")
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            t_purchased = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            unit = i_df[i_df.iloc[:, 0] == item].iloc[:, 2].iloc[-1]
            t_sold = 0
            if not s_df.empty:
                sold_data = s_df[s_df.iloc[:, 1] == item]
                for val in sold_data.iloc[:, 2]:
                    try: t_sold += float(str(val).split()[0])
                    except: continue
            stock_list.append({"Product": item, "Purchased": t_purchased, "Sold": t_sold, "Available": t_purchased - t_sold, "Unit": unit})
        st.table(pd.DataFrame(stock_list))

# --- 8. EXPENSES (DELETE ADDED) ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Electricity", "Pet Food", "Other"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save Expense"):
            save_data("Expenses", [str(datetime.now().date()), cat, amt]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(5))
    if st.button("❌ DELETE LAST EXPENSE"): # Naya Delete Option
        if delete_data("Expenses"): st.success("Expense Deleted!"); time.sleep(1); st.rerun()

# --- 9. PET REGISTER & ADMIN ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    dog_breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Beagle", "Pug", "Indie Dog", "Husky", "Boxer", "Pitbull", "Shih Tzu"]
    cat_breeds = ["Persian Cat", "Siamese Cat", "Indie Cat", "Bengal Cat", "Maine Coon"]
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Select Breed", dog_breeds + cat_breeds + ["Other"])
        with c2: age = st.text_input("Pet Age"); wt = st.text_input("Weight (Kg)"); vax = st.date_input("Next Vaccine Date")
        if st.form_submit_button("SAVE RECORD"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    st.table(load_data("PetRecords").tail(5))

elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("🏢 Company Dues")
    with st.form("due"):
        comp = st.text_input("Company Name"); amt = st.number_input("Due Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Dues"))
