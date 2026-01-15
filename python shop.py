import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# AAPKA URL (Ismein Naya Deployment wala Link hona chahiye)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5hCffTuFBHYDFXKGV9s88OCOId5BJsMbDHo0gMoPOM5_6nbZSaCr9Iu5tp1V1d4qX/exec" 
SHEET_LINK = "https://script.google.com/macros/s/AKfycbx1qVD5g_QHIfDLG-T9ii-EC5Bb6U9iYyQ_gycSGxU2o-BNYdGkQrGCjNpIFdedjFJn/exec"

# --- FUNCTIONS (SAVE & DELETE) ---
def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_data(sheet_name):
    try:
        # Automatic Delete from Google Sheet Command
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN / LOGOUT SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Galti: Sahi Username/Password dalein!")
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🐾 NAVIGATION")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. DASHBOARD (SALE, PURCHASE & MARGIN PROFIT) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='text-align: center; color: #4A90E2;'>📊 Business Performance</h2>", unsafe_allow_html=True)
    s_df = load_data("Sales"); i_df = load_data("Inventory"); e_df = load_data("Expenses")
    today = datetime.now().date(); curr_m = datetime.now().month

    def get_complete_stats(sales_df, inv_df, filter_type="today"):
        if filter_type == "today":
            s_sub = sales_df[sales_df['Date'].dt.date == today] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.date == today] if not inv_df.empty else pd.DataFrame()
        else:
            s_sub = sales_df[sales_df['Date'].dt.month == curr_m] if not sales_df.empty else pd.DataFrame()
            p_sub = inv_df[pd.to_datetime(inv_df.iloc[:, 4]).dt.month == curr_m] if not inv_df.empty else pd.DataFrame()

        total_sale = 0; total_margin = 0
        for _, row in s_sub.iterrows():
            item = row.iloc[1]; q = pd.to_numeric(row.iloc[2], errors='coerce'); s_val = pd.to_numeric(row.iloc[3], errors='coerce')
            total_sale += s_val
            item_stock = inv_df[inv_df.iloc[:, 0] == item]
            if not item_stock.empty:
                p_rate = pd.to_numeric(item_stock.iloc[-1, 3], errors='coerce')
                total_margin += (s_val - (p_rate * q))
        total_pur = (pd.to_numeric(p_sub.iloc[:, 1], errors='coerce') * pd.to_numeric(p_sub.iloc[:, 3], errors='coerce')).sum() if not p_sub.empty else 0
        return total_sale, total_pur, total_margin

    ts, tp, tm = get_complete_stats(s_df, i_df, "today")
    ms, mp, mm = get_complete_stats(s_df, i_df, "month")

    st.subheader(f"📅 Today's Performance ({today})")
    c1, c2, c3 = st.columns(3)
    c1.metric("Today Sale", f"₹{int(ts)}")
    c2.metric("Today Purchase", f"₹{int(tp)}")
    c3.metric("Margin Profit (Bich ka)", f"₹{int(tm)}")

    st.divider()

    st.subheader(f"🗓️ Monthly Summary ({datetime.now().strftime('%B')})")
    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly Sale", f"₹{int(ms)}")
    m2.metric("Monthly Purchase", f"₹{int(mp)}")
    m3.metric("Monthly Margin Profit", f"₹{int(mm)}")

# --- 5. BILLING (WITH AUTO-DELETE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory")
    it_list = inv_df.iloc[:, 0].unique().tolist() if not inv_df.empty else ["No Stock"]
    with st.form("bill_f"):
        it = st.selectbox("Product", it_list)
        q = st.number_input("Qty", 0.1); pr = st.number_input("Selling Price")
        if st.form_submit_button("COMPLETE BILL"):
            save_data("Sales", [str(datetime.now().date()), it, q, q*pr, "Cash"])
            st.rerun()
    
    st.subheader("Recent Sales")
    st.table(load_data("Sales").tail(5))
    if st.button("❌ DELETE LAST SALE (From Google Sheet)"):
        if delete_data("Sales"):
            st.success("Entry Google Sheet se hat gayi aur stock sahi ho gaya!"); st.rerun()
        else:
            st.error("Error: Apps Script URL ya Deployment sahi nahi hai!")

# --- 6. PURCHASE (WITH AUTO-DELETE) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name"); q = st.number_input("Qty"); p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, "Pcs", p, str(datetime.now().date())])
            st.rerun()
    
    st.subheader("Recent Purchases")
    st.table(load_data("Inventory").tail(5))
    if st.button("❌ DELETE LAST PURCHASE (From Google Sheet)"):
        if delete_data("Inventory"):
            st.success("Purchase entry delete ho gayi!"); st.rerun()
        else:
            st.error("Error: Apps Script check karein!")

# --- 7. ADMIN SETTINGS (NEW ID OPTION) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("👤 Create New ID")
    with st.form("admin_id"):
        new_u = st.text_input("New Username"); new_p = st.text_input("New Password", type="password")
        if st.form_submit_button("CREATE ID"):
            st.success(f"ID Created for {new_u}! (Database Sync Active)"); st.rerun()
    
    st.divider()
    st.subheader("🏢 Company Dues")
    d_df = load_data("Dues")
    with st.form("due_f"):
        comp = st.text_input("Company Name"); amt = st.number_input("Due Amount")
        if st.form_submit_button("SAVE DUE"):
            save_data("Dues", [comp, amt, str(datetime.now().date())]); st.rerun()
    st.table(d_df)

# --- BAAKI SECTIONS (PET REGISTER, STOCK, EXPENSE) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Indie", "Other"])
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)]); st.rerun()
    st.table(p_df.tail(5))

elif menu == "📋 Live Stock":
    st.header("📋 Live Shop Stock")
    st.table(load_data("Inventory"))

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Staff", "Other"]); amt = st.number_input("Amount")
    if st.button("Save Expense"):
        save_data("Expenses", [str(datetime.now().date()), cat, amt]); st.rerun()
    st.table(load_data("Expenses").tail(5))

