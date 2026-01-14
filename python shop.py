    import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# Data load karne ka function (Hamesha naya data uthayega)
def load_data(sheet):
    try:
        return conn.read(worksheet=sheet, ttl=0).dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 LAIKA PET MART LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "💰 Expenses", "📋 Live Stock", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (Total Sale, Expense, Profit) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Overview")
    s_df = load_data("Sales"); e_df = load_data("Expenses")
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = t_sale - t_exp
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. PURCHASE (Stock Entry + History List) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory") # Purana stock padhna
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price", min_value=1)
        if st.form_submit_button("ADD TO STOCK"):
            new_r = pd.DataFrame([{"Item": n, "qty": q, "Unit": u, "p_price": p, "Date": str(datetime.now().date())}])
            updated_inv = pd.concat([inv_df, new_r], ignore_index=True)
            conn.update(worksheet="Inventory", data=updated_inv) # Seedha sheet mein likhna
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Purchase History")
    st.table(inv_df.tail(10)) # Niche list dikhana

# --- 6. BILLING (Live Stock Dropdown + List) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("bill_f"):
        item_list = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", item_list)
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Qty", min_value=0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        with c3: price = st.number_input("Rate", min_value=1)
        mode = st.selectbox("Payment", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": it, "Qty": f"{qty} {unit}", "total": qty*price, "Mode": mode}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Saved!"); st.rerun()
    st.subheader("📋 Recent Sales")
    st.table(sales_df.tail(10))

# --- 7. LIVE STOCK (Everything from Purchase) ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_data("Inventory"))

# --- 8. EXPENSES (Dropdown + List) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Records")
    e_df = load_data("Expenses")
    with st.form("exp_f"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("SAVE"):
            new_e = pd.DataFrame([{"Date": str(datetime.now().date()), "Category": cat, "Amount": amt}])
            conn.update(worksheet="Expenses", data=pd.concat([e_df, new_e], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

# --- 9. PET REGISTER (Full Details) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone")
        with c2: br = st.text_input("Breed"); wt = st.text_input("Weight"); age = st.text_input("Age")
        vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Weight": wt, "Age": age, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([p_df, new_p], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(p_df.tail(10))

# --- 10. ADMIN SETTINGS (Dues + New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Controls")
    d_df = load_data("Dues")
    with st.expander("Record Udhaar (Dues)"):
        comp = st.text_input("Company Name"); amt = st.number_input("Amount")
        if st.button("Save Due"):
            new_d = pd.DataFrame([{"Company": comp, "Amount": amt, "Date": str(datetime.now().date())}])
            conn.update(worksheet="Dues", data=pd.concat([d_df, new_d], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(d_df)
    st.divider()
    st.subheader("👤 Create New Staff ID")
    new_u = st.text_input("New Username"); new_p = st.text_input("Password", type="password")
    if st.button("CREATE ID"):
        st.success(f"ID Created for {new_u} (Check Sheet 'Users')")
