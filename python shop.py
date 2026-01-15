[12:00 pm, 15/1/2026] Laika pet Shop: import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# Data load karne ka function (Hamesha taza data ke liye)
def load_data(sheet):
    try:
        df = conn.read(worksheet=sheet, ttl=0)
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 LAIKA PET MART LOGIN")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "💰 Expenses", "📋 Live Stock", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (SALE, PURCHASE, EXPENSE, PROFIT) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Overview")
    s_df = load_data("Sales"); e_df = load_data("Expenses"); i_df = load_data("Inventory")
    t_sale = s_df['total'].sum() if not s_df.empty else 0
    t_pur = (i_df['qty'] * i_df['p_price']).sum() if not i_df.empty else 0
    t_exp = e_df['Amount'].sum() if not e_df.empty else 0
    t_profit = t_sale - t_exp
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. PURCHASE (LIST KE SAATH) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_data("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price", min_value=1)
        if st.form_submit_button("ADD TO STOCK"):
            new_r = pd.DataFrame([{"Item": n, "qty": q, "Unit": u, "p_price": p, "Date": str(datetime.now().date())}])
            conn.update(worksheet="Inventory", data=pd.concat([inv_df, new_r], ignore_index=True))
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Recent Purchase List")
    st.table(inv_df.tail(10))

# --- 6. BILLING (ONLINE/OFFLINE + LIST) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_data("Inventory"); sales_df = load_data("Sales")
    with st.form("bill_f"):
        it_list = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", it_list)
        c1, c2, c3 = st.columns(3)
        with c1: qty = st.number_input("Qty", min_value=0.1)
        with c2: unit = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        with c3: price = st.number_input("Rate", min_value=1)
        mode = st.selectbox("Payment Mode", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            new_s = pd.DataFrame([{"Date": str(datetime.now().date()), "Item": it, "Qty": f"{qty} {unit}", "total": qty*price, "Mode": mode}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Bill Saved!"); st.rerun()
    st.subheader("📋 Recent Sales History")
    st.table(sales_df.tail(10))

# --- 7. EXPENSES (DROP-DOWN + LIST) ---
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
    st.subheader("📋 Expenses History")
    st.table(e_df.tail(10))

# --- 8. PET REGISTER (DOG & CAT BREEDS) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_data("PetRecords")
    # Dog aur Cat ki breeds ka mix dropdown
    pet_breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Beagle", "Persian Cat", "Siamese Cat", "Indie Dog", "Indie Cat", "Other"]
    with st.form("pet_f"):
        c1, c2 = st.columns(2)
        with c1: cn = st.text_input("Customer Name"); ph = st.text_input("Phone Number"); br = st.selectbox("Breed", pet_breeds)
        with c2: age = st.text_input("Age"); wt = st.text_input("Weight (Kg)"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            new_p = pd.DataFrame([{"Customer": cn, "Phone": ph, "Breed": br, "Weight": wt, "Age": age, "Vaccine": str(vax)}])
            conn.update(worksheet="PetRecords", data=pd.concat([p_df, new_p], ignore_index=True))
            st.success("Saved!"); st.rerun()
    st.table(p_df.tail(10))

# --- 9. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_data("Inventory"))

# --- 10. ADMIN SETTINGS (NO CHANGES) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
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
    new_u = st.text_input("New Staff Name"); new_p = st.text_input("Password", type="password")
    if st.button("CREATE ID"): st.success(f"ID Created for {new_u}!")
[12:04 pm, 15/1/2026] Laika pet Shop: function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(e.parameter.sheet);
  sheet.appendRow(data);
  return ContentService.createTextOutput("Success");
}
[12:04 pm, 15/1/2026] Laika pet Shop: import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# APNA APPS SCRIPT URL YAHAN DALEIN
SCRIPT_URL = "YAHAN_APNA_URL_PASTE_KAREIN" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_to_gsheet(sheet_name, data_list):
    requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)

def load_from_gsheet(sheet_name):
    try: return pd.read_csv(SHEET_LINK + sheet_name)
    except: return pd.DataFrame()

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. PURCHASE (Jo yahan bharenge wo Stock mein dikhega) ---
if menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD TO STOCK"):
            save_to_gsheet("Inventory", [n, q, u, p, str(datetime.now().date())])
            st.success("Stock Added Successfully!"); st.rerun()
    st.subheader("📋 Recent Purchase List")
    st.table(load_from_gsheet("Inventory").tail(10))

# --- 5. BILLING (Stock se Item uthayega) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_from_gsheet("Inventory")
    with st.form("bill_f"):
        # Dropdown mein wahi items aayenge jo Purchase mein dale hain
        items = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", items)
        qty = st.number_input("Qty", min_value=0.1)
        pr = st.number_input("Selling Price")
        mode = st.selectbox("Payment", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_to_gsheet("Sales", [str(datetime.now().date()), it, qty, qty*pr, mode])
            st.success("Bill Saved!"); st.rerun()
    st.table(load_from_gsheet("Sales").tail(10))

# --- 6. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_from_gsheet("Inventory"))

# --- 7. BAAKI SECTIONS (Admin, Pet Register etc. logic same rahega) ---
