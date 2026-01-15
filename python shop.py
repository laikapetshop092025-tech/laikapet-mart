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
        # FIXED: Delete command ab sahi tarah se jayegi
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

# --- 3. SIDEBAR (LOGO & NAVIGATION) ---
st.sidebar.markdown("<h2 style='text-align: center; color: #4A90E2;'>🐾 LAIKA PET MART</h2>", unsafe_allow_html=True)

# Logo Logic: Bina URL ke, sirf upload file se
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SALE, PURCHASE, PROFIT, EXPENSE) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center;'>📊 Business Performance</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses")
    today = datetime.now().date(); curr_m = datetime.now().month

    def get_all_stats(sales_df, inv_df, exp_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.date == today] if not inv_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.date == today] if not exp_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.month == curr_m] if not inv_df.empty else pd.DataFrame()
            e_sub = exp_df[exp_df['Date'].dt.month == curr_m] if not exp_df.empty else pd.DataFrame()
        
        t_sale = pd.to_numeric(s_sub.iloc[:, 3], errors='coerce').sum() if not s_sub.empty else 0
        t_pur = (pd.to_numeric(p_sub.iloc[:, 1], errors='coerce') * pd.to_numeric(p_sub.iloc[:, 3], errors='coerce')).sum() if not p_sub.empty else 0
        t_exp = pd.to_numeric(e_sub.iloc[:, 2], errors='coerce').sum() if not e_sub.empty else 0
        
        t_margin = 0
        for _, row in s_sub.iterrows():
            item = row.iloc[1]; q = pd.to_numeric(row.iloc[2], errors='coerce'); s_val = pd.to_numeric(row.iloc[3], errors='coerce')
            item_stock = inv_df[inv_df.iloc[:, 0] == item]
            if not item_stock.empty:
                p_rate = pd.to_numeric(item_stock.iloc[-1, 3], errors='coerce')
                t_margin += (s_val - (p_rate * q))
        return t_sale, t_pur, t_margin, t_exp

    ts, tp, tm, te = get_all_stats(s_df, i_df, e_df, "today")
    ms, mp, mm, me = get_all_stats(s_df, i_df, e_df, "month")

    st.subheader(f"📍 Today's Stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{int(ts)}"); c2.metric("Purchase", f"₹{int(tp)}"); c3.metric("Profit", f"₹{int(tm)}"); c4.metric("Expense", f"₹{int(te)}")
    st.divider()
    st.subheader(f"🗓️ Monthly Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sale", f"₹{int(ms)}"); m2.metric("Purchase", f"₹{int(mp)}"); m3.metric("Profit", f"₹{int(mm)}"); m4.metric("Expense", f"₹{int(me)}")

# --- BAAKI SECTIONS (NO CHANGES) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing")
    inv_df = load_data("Inventory")
    with st.form("bill"):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); pr = st.number_input("Price")
        if st.form_submit_button("SAVE"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Paid"]); time.sleep(1); st.rerun()
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE"):
        if delete_data("Sales"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); q = st.number_input("Qty", 1); p = st.number_input("Rate")
        if st.form_submit_button("ADD"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE"):
        if delete_data("Inventory"): st.success("Deleted!"); time.sleep(1); st.rerun()

elif menu == "📋 Live Stock":
    i_df = load_data("Inventory"); s_df = load_data("Sales")
    if not i_df.empty:
        stock_list = []
        for item in i_df.iloc[:, 0].unique():
            p_q = pd.to_numeric(i_df[i_df.iloc[:, 0] == item].iloc[:, 1], errors='coerce').sum()
            s_q = pd.to_numeric(s_df[s_df.iloc[:, 1] == item].iloc[:, 2], errors='coerce').sum() if not s_df.empty else 0
            stock_list.append({"Product": item, "Available": p_q - s_q})
        st.table(pd.DataFrame(stock_list))

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.text_input("Breed")
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Next Vaccine")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); time.sleep(1); st.rerun()
    st.table(load_data("PetRecords").tail(5))

elif menu == "💰 Expenses":
    cat = st.selectbox("Cat", ["Rent", "Salary", "Other"]); amt = st.number_input("Amt")
    if st.button("Save"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); time.sleep(1); st.rerun()
    st.table(load_data("Expenses").tail(5))

elif menu == "⚙️ Admin Settings":
    st.subheader("Udhaar (Dues)")
    with st.form("due"):
        comp = st.text_input("Company"); amt = st.number_input("Due")
        if st.form_submit_button("SAVE"): save_data("Dues", [comp, amt, str(datetime.now().date())]); time.sleep(1); st.rerun()
    st.table(load_data("Dues"))
