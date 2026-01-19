import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

if 'bill_cart' not in st.session_state: st.session_state.bill_cart = []
if 'pur_cart' not in st.session_state: st.session_state.pur_cart = []
if 'last_check_date' not in st.session_state: st.session_state.last_check_date = None

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def load_data(sheet_name):
    try:
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True).dt.date
            df = df.rename(columns={date_col: 'Date'})
        return df
    except: return pd.DataFrame()

def update_balance(amount, mode, operation='add'):
    """Update Galla or Online balance - operation can be 'add' or 'subtract'"""
    b_df = load_data("Balances")
    
    if b_df.empty:
        # Create initial balance if doesn't exist
        save_data("Balances", ["Cash", 0])
        save_data("Balances", ["Online", 0])
        b_df = load_data("Balances")
    
    # Find current balance
    if mode == "Cash":
        current = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[0, 1], errors='coerce') if len(b_df[b_df.iloc[:, 0] == "Cash"]) > 0 else 0
        new_bal = current + amount if operation == 'add' else current - amount
        # Update by clearing and re-adding (simple approach)
        save_data("Balances", ["Cash", new_bal])
    elif mode == "Online":
        current = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[0, 1], errors='coerce') if len(b_df[b_df.iloc[:, 0] == "Online"]) > 0 else 0
        new_bal = current + amount if operation == 'add' else current - amount
        save_data("Balances", ["Online", new_bal])

def archive_daily_data():
    """Archive previous day's data to separate sheet"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Create sheet name like "Archive_18Jan2026"
    archive_sheet = f"Archive_{yesterday.strftime('%d%b%Y')}"
    
    # Get all transaction sheets
    for sheet in ["Sales", "Inventory", "Expenses"]:
        df = load_data(sheet)
        if not df.empty and 'Date' in df.columns:
            old_data = df[df['Date'] < today]
            if not old_data.empty:
                # Save to archive
                for _, row in old_data.iterrows():
                    save_data(archive_sheet, row.tolist())

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password")
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. CHECK FOR NEW DAY & ARCHIVE ---
today_dt = datetime.now().date()
if st.session_state.last_check_date != today_dt:
    if st.session_state.last_check_date is not None:
        archive_daily_data()
    st.session_state.last_check_date = today_dt

# --- 4. SIDEBAR ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# --- 5. DASHBOARD (FIXED CALCULATIONS) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances")
    k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Get current balances from Balances sheet
    cash_bal = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[0, 1], errors='coerce') if not b_df.empty and len(b_df[b_df.iloc[:, 0] == "Cash"]) > 0 else 0
    online_bal = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[0, 1], errors='coerce') if not b_df.empty and len(b_df[b_df.iloc[:, 0] == "Online"]) > 0 else 0
    
    # Calculate stock value
    total_stock_val = 0
    if not i_df.empty and len(i_df.columns) > 3:
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df['qty_v'] * i_df['rate_v']).sum()

    # Calculate total udhaar
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h3 style="margin: 0;">₹{cash_bal:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online</p> <h3 style="margin: 0;">₹{online_bal:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Total Balance</p> <h3 style="margin: 0;">₹{cash_bal + online_bal:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # TODAY'S REPORT
    st.divider(); st.subheader("📈 Today's Report")
    s_today = s_df[s_df['Date'] == today_dt] if not s_df.empty else pd.DataFrame()
    i_today = i_df[i_df['Date'] == today_dt] if not i_df.empty else pd.DataFrame()
    e_today = e_df[e_df['Date'] == today_dt] if not e_df.empty else pd.DataFrame()
    
    today_sale = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum() if not s_today.empty else 0
    today_pur = 0
    if not i_today.empty and len(i_today.columns) > 3:
        today_pur = (pd.to_numeric(i_today.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * 
                     pd.to_numeric(i_today.iloc[:, 3], errors='coerce').fillna(0)).sum()
    today_exp = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty else 0
    today_profit = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sale", f"₹{today_sale:,.2f}")
    c2.metric("Purchase", f"₹{today_pur:,.2f}")
    c3.metric("Expense", f"₹{today_exp:,.2f}")
    c4.metric("Profit", f"₹{today_profit:,.2f}")

    # MONTHLY REPORT
    st.divider(); st.subheader(f"🗓️ {curr_m_name} Summary")
    s_month = s_df[pd.to_datetime(s_df['Date'], errors='coerce').dt.month == curr_m] if not s_df.empty else pd.DataFrame()
    i_month = i_df[pd.to_datetime(i_df['Date'], errors='coerce').dt.month == curr_m] if not i_df.empty else pd.DataFrame()
    e_month = e_df[pd.to_datetime(e_df['Date'], errors='coerce').dt.month == curr_m] if not e_df.empty else pd.DataFrame()
    
    month_sale = pd.to_numeric(s_month.iloc[:, 3], errors='coerce').sum() if not s_month.empty else 0
    month_pur = 0
    if not i_month.empty and len(i_month.columns) > 3:
        month_pur = (pd.to_numeric(i_month.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0) * 
                     pd.to_numeric(i_month.iloc[:, 3], errors='coerce').fillna(0)).sum()
    month_exp = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum() if not e_month.empty else 0
    month_profit = pd.to_numeric(s_month.iloc[:, 7], errors='coerce').sum() if not s_month.empty and len(s_month.columns) > 7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sale", f"₹{month_sale:,.2f}")
    c2.metric("Total Purchase", f"₹{month_pur:,.2f}")
    c3.metric("Total Expense", f"₹{month_exp:,.2f}")
    c4.metric("Total Profit", f"₹{month_profit:,.2f}")

# --- 6. BILLING (WITH AUTO BALANCE UPDATE) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Royalty Club")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Name"); c_ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty) else 0
    st.info(f"👑 Royalty Points: {pts_bal}")
    
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"]); p = st.number_input("Price", 1.0)
        rd = st.checkbox(f"Redeem {pts_bal} Pts?"); rf = st.checkbox("Referral Bonus (+10 Pts)")
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty else 0
            pts = int(((q*p)/100)* (5 if is_weekend else 2)); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    
    if st.session_state.bill_cart:
        st.table(pd.DataFrame(st.session_state.bill_cart))
        total_amt = sum([item['Price'] for item in st.session_state.bill_cart])
        st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        
        if st.button("✅ Save Bill"):
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            
            # Update balance automatically (only for Cash/Online, not Udhaar)
            if pay_m in ["Cash", "Online"]:
                update_balance(total_amt, pay_m, 'add')
                st.success(f"✅ Bill saved! {pay_m} balance updated by +₹{total_amt:,.2f}")
            else:
                st.success("✅ Bill saved as Udhaar!")
            
            st.session_state.bill_cart = []
            time.sleep(1)
            st.rerun()

# --- 7. PURCHASE (WITH AUTO BALANCE UPDATE) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add Stock", expanded=True):
        n = st.text_input("Item"); q = st.number_input("Qty", 1.0); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt"]); r = st.number_input("Rate"); m = st.selectbox("Paid From", ["Cash", "Online", "Pocket", "Hand"])
        if st.button("➕ Save"):
            total_cost = q * r
            save_data("Inventory", [n, f"{q} {u}", "Stock", r, str(today_dt), m])
            
            # Deduct from balance (only for Cash/Online)
            if m in ["Cash", "Online"]:
                update_balance(total_cost, m, 'subtract')
                st.success(f"✅ Stock added! {m} balance deducted by -₹{total_cost:,.2f}")
            else:
                st.success("✅ Stock added!")
            
            time.sleep(1)
            st.rerun()
    
    # Show recent purchases
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.subheader("Recent Purchases")
        st.dataframe(i_df.tail(10), use_container_width=True)

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    if not i_df.empty and len(i_df.columns) > 3:
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        t_v = (i_df['qty_v'] * i_df['rate_v']).sum()
        st.subheader(f"💰 Total Stock Value: ₹{t_v:,.2f}")
        
        # Group by item and show current stock
        stock_summary = i_df.groupby(i_df.columns[0]).agg({
            i_df.columns[1]: 'last',
            i_df.columns[3]: 'last'
        }).reset_index()
        
        for _, row in stock_summary.iterrows():
            qv = float(str(row.iloc[1]).split()[0]) if len(str(row.iloc[1]).split()) > 0 else 0
            if qv < 2: 
                st.error(f"🚨 LOW STOCK: {row.iloc[0]} ({row.iloc[1]})")
            else: 
                st.info(f"✅ {row.iloc[0]}: {row.iloc[1]}")

# --- 9. EXPENSES (WITH AUTO BALANCE UPDATE) ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Transport", "Utilities", "Other"])
        amt = st.number_input("Amount", min_value=0.0)
        m = st.selectbox("Mode", ["Cash", "Online"])
        note = st.text_input("Note (Optional)")
        
        if st.form_submit_button("💾 Save Expense"):
            if amt > 0:
                save_data("Expenses", [str(today_dt), cat, amt, m, note])
                
                # Deduct from balance
                update_balance(amt, m, 'subtract')
                st.success(f"✅ Expense saved! {m} balance deducted by -₹{amt:,.2f}")
                time.sleep(1)
                st.rerun()
    
    e_df = load_data("Expenses")
    if not e_df.empty: 
        st.subheader("Recent Expenses")
        st.dataframe(e_df.tail(15), use_container_width=True)

# --- 10. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner"); ph = c2.text_input("Phone"); br = c1.text_input("Breed")
        age = c2.number_input("Age (Months)", 1); wt = c1.number_input("Weight (Kg)", 0.1); vd = c2.date_input("Last Vax")
        if st.form_submit_button("Save"):
            nv = vd + timedelta(days=365)
            save_data("PetRecords", [on, ph, br, age, wt, str(vd), str(nv), str(today_dt)])
            st.success("✅ Pet record saved!")
            time.sleep(1)
            st.rerun()
    
    p_df = load_data("PetRecords")
    if not p_df.empty: 
        st.dataframe(p_df, use_container_width=True)

# --- 11. CUSTOMER KHATA ---
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata")
    with st.form("kh"):
        n = st.text_input("Name"); a = st.number_input("Amount", min_value=0.0)
        t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        m = st.selectbox("Mode", ["Cash", "Online", "N/A"])
        
        if st.form_submit_button("Save Entry"):
            if a > 0:
                final_amt = a if "+" in t else -a
                save_data("CustomerKhata", [n, final_amt, str(today_dt), m])
                
                # If payment received (Jama), add to balance
                if "-" in t and m in ["Cash", "Online"]:
                    update_balance(a, m, 'add')
                    st.success(f"✅ Payment received! {m} balance increased by +₹{a:,.2f}")
                else:
                    st.success("✅ Entry saved!")
                time.sleep(1)
                st.rerun()
    
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        sum_df.columns = ['Customer', 'Balance']
        sum_df = sum_df[sum_df['Balance'] != 0].sort_values('Balance', ascending=False)
        st.table(sum_df)

# --- 12. SUPPLIER DUES ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier"); a = st.number_input("Amount", min_value=0.0)
        t = st.selectbox("Type", ["Maal (+)", "Payment (-)"])
        m = st.selectbox("Mode", ["Cash", "Online", "Hand", "Pocket"])
        
        if st.form_submit_button("Save"):
            if a > 0:
                final_amt = a if "+" in t else -a
                save_data("Dues", [s, final_amt, str(today_dt), m])
                
                # If payment made, deduct from balance
                if "-" in t and m in ["Cash", "Online"]:
                    update_balance(a, m, 'subtract')
                    st.success(f"✅ Payment made! {m} balance deducted by -₹{a:,.2f}")
                else:
                    st.success("✅ Entry saved!")
                time.sleep(1)
                st.rerun()
    
    d_df = load_data("Dues")
    if not d_df.empty: 
        st.dataframe(d_df, use_container_width=True)
