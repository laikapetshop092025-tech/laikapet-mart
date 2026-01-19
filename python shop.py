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

def get_current_balance(mode):
    """Get current balance from Balances sheet"""
    try:
        b_df = load_data("Balances")
        if b_df.empty or len(b_df.columns) < 2:
            return 0.0
        
        rows = b_df[b_df.iloc[:, 0].str.strip() == mode]
        if len(rows) > 0:
            return float(pd.to_numeric(rows.iloc[0, 1], errors='coerce'))
        return 0.0
    except:
        return 0.0

def update_balance(amount, mode, operation='add'):
    """Update Galla or Online balance - returns True if successful"""
    if mode not in ["Cash", "Online"]:
        return True  # For Pocket/Hand/Udhaar, no balance update needed
    
    try:
        current_bal = get_current_balance(mode)
        
        if operation == 'add':
            new_bal = current_bal + amount
        else:  # subtract
            new_bal = current_bal - amount
        
        # Update in Google Sheets
        success = save_data("Balances", [mode, new_bal])
        
        if success:
            st.success(f"✅ {mode} Balance: ₹{current_bal:,.2f} → ₹{new_bal:,.2f} ({'+' if operation=='add' else '-'}₹{amount:,.2f})")
        
        return success
    except Exception as e:
        st.error(f"⚠️ Balance update error: {str(e)}")
        return False

def archive_daily_data():
    """Archive previous day's data"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    archive_sheet = f"Archive_{yesterday.strftime('%d%b%Y')}"
    
    for sheet in ["Sales", "Inventory", "Expenses"]:
        df = load_data(sheet)
        if not df.empty and 'Date' in df.columns:
            old_data = df[df['Date'] < today]
            if not old_data.empty:
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

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); k_df = load_data("CustomerKhata"); i_df = load_data("Inventory")
    
    # Get CURRENT balances from Balances sheet
    cash_bal = get_current_balance("Cash")
    online_bal = get_current_balance("Online")
    total_bal = cash_bal + online_bal
    
    # Calculate stock value
    total_stock_val = 0
    if not i_df.empty and len(i_df.columns) > 3:
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df['qty_v'] * i_df['rate_v']).sum()

    # Calculate total udhaar
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty and len(k_df.columns) > 1 else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 19%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h3 style="margin: 0;">₹{cash_bal:,.2f}</h3>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 19%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online</p> <h3 style="margin: 0;">₹{online_bal:,.2f}</h3>
        </div>
        <div style="background-color: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 8px solid #7B1FA2; width: 19%;">
            <p style="color: #7B1FA2; margin: 0;">⚡ Total Balance</p> <h3 style="margin: 0;">₹{total_bal:,.2f}</h3>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 19%;">
            <p style="color: #F57C00; margin: 0;">📒 Udhaar</p> <h3 style="margin: 0;">₹{total_u:,.2f}</h3>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 19%;">
            <p style="color: #388E3C; margin: 0;">📦 Stock Value</p> <h3 style="margin: 0;">₹{total_stock_val:,.2f}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # BALANCE CORRECTION TOOL
    with st.expander("🔧 Balance Correction (Admin Only)"):
        st.warning("⚠️ Use only if balance is incorrect!")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cash Balance")
            new_cash = st.number_input("Set Cash Balance", value=float(cash_bal), step=1.0, key="cash_corr")
            if st.button("Update Cash", key="update_cash"):
                save_data("Balances", ["Cash", new_cash])
                st.success(f"✅ Cash balance set to ₹{new_cash:,.2f}")
                time.sleep(1)
                st.rerun()
        with col2:
            st.subheader("Online Balance")
            new_online = st.number_input("Set Online Balance", value=float(online_bal), step=1.0, key="online_corr")
            if st.button("Update Online", key="update_online"):
                save_data("Balances", ["Online", new_online])
                st.success(f"✅ Online balance set to ₹{new_online:,.2f}")
                time.sleep(1)
                st.rerun()
    
    # TODAY'S REPORT
    st.divider()
    st.subheader("📈 Today's Report")
    s_today = s_df[s_df['Date'] == today_dt] if not s_df.empty and 'Date' in s_df.columns else pd.DataFrame()
    i_today = i_df[i_df['Date'] == today_dt] if not i_df.empty and 'Date' in i_df.columns else pd.DataFrame()
    e_today = e_df[e_df['Date'] == today_dt] if not e_df.empty and 'Date' in e_df.columns else pd.DataFrame()
    
    today_sale = 0
    if not s_today.empty and len(s_today.columns) > 3:
        today_sale = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum()
    
    today_pur = 0
    if not i_today.empty and len(i_today.columns) > 3:
        qty_vals = pd.to_numeric(i_today.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals = pd.to_numeric(i_today.iloc[:, 3], errors='coerce').fillna(0)
        today_pur = (qty_vals * rate_vals).sum()
    
    today_exp = 0
    if not e_today.empty and len(e_today.columns) > 2:
        today_exp = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum()
    
    today_profit = 0
    if not s_today.empty and len(s_today.columns) > 7:
        today_profit = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Sale", f"₹{today_sale:,.2f}")
    c2.metric("📦 Purchase", f"₹{today_pur:,.2f}")
    c3.metric("💸 Expense", f"₹{today_exp:,.2f}")
    c4.metric("📈 Profit", f"₹{today_profit:,.2f}")
    
    # DATE-WISE PURCHASE VIEWER
    st.divider()
    st.subheader("📅 Date-wise Purchase Summary")
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_date = st.date_input("Select Date", value=today_dt, key="purchase_date_picker")
    
    if not i_df.empty and 'Date' in i_df.columns:
        date_purchases = i_df[i_df['Date'] == selected_date]
        if not date_purchases.empty and len(date_purchases.columns) > 3:
            qty_vals = pd.to_numeric(date_purchases.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
            rate_vals = pd.to_numeric(date_purchases.iloc[:, 3], errors='coerce').fillna(0)
            date_total = (qty_vals * rate_vals).sum()
            
            with col2:
                st.metric(f"📦 Total Purchase on {selected_date.strftime('%d-%m-%Y')}", f"₹{date_total:,.2f}")
            
            st.dataframe(date_purchases, use_container_width=True, height=300)
        else:
            st.info(f"No purchases found on {selected_date.strftime('%d-%m-%Y')}")
    else:
        st.info("No purchase data available")

    # MONTHLY REPORT
    st.divider()
    st.subheader(f"🗓️ {curr_m_name} Summary")
    
    s_month = pd.DataFrame(); i_month = pd.DataFrame(); e_month = pd.DataFrame()
    
    if not s_df.empty and 'Date' in s_df.columns:
        s_df['Month'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.month
        s_month = s_df[s_df['Month'] == curr_m]
    
    if not i_df.empty and 'Date' in i_df.columns:
        i_df['Month'] = pd.to_datetime(i_df['Date'], errors='coerce').dt.month
        i_month = i_df[i_df['Month'] == curr_m]
    
    if not e_df.empty and 'Date' in e_df.columns:
        e_df['Month'] = pd.to_datetime(e_df['Date'], errors='coerce').dt.month
        e_month = e_df[e_df['Month'] == curr_m]
    
    month_sale = 0
    if not s_month.empty and len(s_month.columns) > 3:
        month_sale = pd.to_numeric(s_month.iloc[:, 3], errors='coerce').sum()
    
    month_pur = 0
    if not i_month.empty and len(i_month.columns) > 3:
        qty_vals = pd.to_numeric(i_month.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals = pd.to_numeric(i_month.iloc[:, 3], errors='coerce').fillna(0)
        month_pur = (qty_vals * rate_vals).sum()
    
    month_exp = 0
    if not e_month.empty and len(e_month.columns) > 2:
        month_exp = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum()
    
    month_profit = 0
    if not s_month.empty and len(s_month.columns) > 7:
        month_profit = pd.to_numeric(s_month.iloc[:, 7], errors='coerce').sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Sale", f"₹{month_sale:,.2f}")
    c2.metric("📦 Total Purchase", f"₹{month_pur:,.2f}")
    c3.metric("💸 Total Expense", f"₹{month_exp:,.2f}")
    c4.metric("📈 Total Profit", f"₹{month_profit:,.2f}")

# --- 6. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Royalty Club")
    inv_df = load_data("Inventory"); s_df = load_data("Sales")
    c_name = st.text_input("Name"); c_ph = st.text_input("Phone"); pay_m = st.selectbox("Mode", ["Cash", "Online", "Udhaar"])
    pts_bal = pd.to_numeric(s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)].iloc[:, 6], errors='coerce').sum() if (c_ph and not s_df.empty and len(s_df.columns) > 6) else 0
    st.info(f"👑 Royalty Points: {pts_bal}")
    
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1); u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"]); p = st.number_input("Price", 1.0)
        rd = st.checkbox(f"Redeem {pts_bal} Pts?"); rf = st.checkbox("Referral Bonus (+10 Pts)")
        if st.button("➕ Add"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty and len(inv_df[inv_df.iloc[:, 0] == it]) > 0 else 0
            pts = int(((q*p)/100)* (5 if is_weekend else 2)); pts = -pts_bal if rd else pts; pts += 10 if rf else 0
            st.session_state.bill_cart.append({"Item": it, "Qty": f"{q} {u}", "Price": p, "Profit": (p-pur_r)*q, "Pts": pts})
            st.rerun()
    
    if st.session_state.bill_cart:
        st.table(pd.DataFrame(st.session_state.bill_cart))
        total_amt = sum([item['Price'] for item in st.session_state.bill_cart])
        st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        
        if st.button("✅ Save Bill"):
            # First save all items to Sales sheet
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            
            # Update balance based on payment mode
            if pay_m == "Cash":
                if update_balance(total_amt, "Cash", 'add'):
                    st.session_state.bill_cart = []
                    time.sleep(1.5)
                    st.rerun()
            elif pay_m == "Online":
                if update_balance(total_amt, "Online", 'add'):
                    st.session_state.bill_cart = []
                    time.sleep(1.5)
                    st.rerun()
            else:  # Udhaar
                save_data("CustomerKhata", [f"{c_name}({c_ph})", total_amt, str(today_dt), "Udhaar"])
                st.success("✅ Bill saved as Udhaar!")
                st.session_state.bill_cart = []
                time.sleep(1.5)
                st.rerun()

# --- 7. PURCHASE ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    with st.expander("📥 Add Stock", expanded=True):
        n = st.text_input("Item Name")
        q = st.number_input("Quantity", min_value=0.1, value=1.0)
        u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        r = st.number_input("Rate per Unit", min_value=0.0, value=0.0)
        m = st.selectbox("Paid From", ["Cash", "Online", "Pocket", "Hand"])
        
        if st.button("➕ Save Purchase"):
            if q > 0 and r > 0 and n.strip():
                total_cost = q * r
                # First save to Inventory
                save_data("Inventory", [n, f"{q} {u}", "Stock", r, str(today_dt), m])
                
                # Update balance based on payment mode
                if m == "Cash":
                    if update_balance(total_cost, "Cash", 'subtract'):
                        time.sleep(1.5)
                        st.rerun()
                elif m == "Online":
                    if update_balance(total_cost, "Online", 'subtract'):
                        time.sleep(1.5)
                        st.rerun()
                else:  # Pocket or Hand
                    st.success(f"✅ Stock added! (Paid from {m})")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.error("❌ Please enter valid item name, quantity and rate!")
    
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.subheader("📋 Recent Purchases")
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

# --- 9. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Transport", "Utilities", "Other"])
        amt = st.number_input("Amount", min_value=0.0)
        m = st.selectbox("Mode", ["Cash", "Online"])
        note = st.text_input("Note (Optional)")
        
        if st.form_submit_button("💾 Save Expense"):
            if amt > 0:
                # First save to Expenses
                save_data("Expenses", [str(today_dt), cat, amt, m, note])
                
                # Update balance based on payment mode
                if m == "Cash":
                    if update_balance(amt, "Cash", 'subtract'):
                        time.sleep(1.5)
                        st.rerun()
                elif m == "Online":
                    if update_balance(amt, "Online", 'subtract'):
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.error("❌ Please enter valid amount!")
    
    e_df = load_data("Expenses")
    if not e_df.empty: 
        st.subheader("📋 Recent Expenses")
        st.dataframe(e_df.tail(15), use_container_width=True)

# --- 10. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner"); ph = c2.text_input("Phone"); br = c1.text_input("Breed")
        age = c2.number_input("Age (Months)", 1); wt = c1.number_input("Weight (Kg)", 0.1); vd = c2.date_input("Last Vax")
        if st.form_submit_button("💾 Save Pet"):
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
        n = st.text_input("Customer Name")
        a = st.number_input("Amount", min_value=0.0)
        t = st.selectbox("Type", ["Udhaar (+)", "Jama (-)"])
        m = st.selectbox("Mode", ["Cash", "Online", "N/A"])
        
        if st.form_submit_button("💾 Save Entry"):
            if a > 0 and n.strip():
                final_amt = a if "+" in t else -a
                # First save to CustomerKhata
                save_data("CustomerKhata", [n, final_amt, str(today_dt), m])
                
                # If payment received (Jama), update balance
                if "-" in t:  # Jama/Payment received
                    if m == "Cash":
                        if update_balance(a, "Cash", 'add'):
                            time.sleep(1.5)
                            st.rerun()
                    elif m == "Online":
                        if update_balance(a, "Online", 'add'):
                            time.sleep(1.5)
                            st.rerun()
                    else:  # N/A
                        st.success("✅ Entry saved!")
                        time.sleep(1.5)
                        st.rerun()
                else:  # Udhaar
                    st.success("✅ Udhaar entry saved!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.error("❌ Please enter valid name and amount!")
    
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        st.subheader("📊 Customer Balance Summary")
        sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
        sum_df.columns = ['Customer', 'Balance']
        sum_df = sum_df[sum_df['Balance'] != 0].sort_values('Balance', ascending=False)
        st.table(sum_df)

# --- 12. SUPPLIER DUES ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    with st.form("due"):
        s = st.text_input("Supplier Name")
        a = st.number_input("Amount", min_value=0.0)
        t = st.selectbox("Type", ["Maal (+)", "Payment (-)"])
        m = st.selectbox("Mode", ["Cash", "Online", "Hand", "Pocket"])
        
        if st.form_submit_button("💾 Save"):
            if a > 0 and s.strip():
                final_amt = a if "+" in t else -a
                # First save to Dues
                save_data("Dues", [s, final_amt, str(today_dt), m])
                
                # If payment made (Payment -), update balance
                if "-" in t:  # Payment made to supplier
                    if m == "Cash":
                        if update_balance(a, "Cash", 'subtract'):
                            time.sleep(1.5)
                            st.rerun()
                    elif m == "Online":
                        if update_balance(a, "Online", 'subtract'):
                            time.sleep(1.5)
                            st.rerun()
                    else:  # Hand/Pocket
                        st.success(f"✅ Payment saved! (Paid from {m})")
                        time.sleep(1.5)
                        st.rerun()
                else:  # Maal liya (Credit +)
                    st.success("✅ Supplier due added!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.error("❌ Please enter valid supplier name and amount!")
    
    d_df = load_data("Dues")
    if not d_df.empty and len(d_df.columns) > 1:
        st.subheader("📊 Supplier Dues Summary")
        # Create summary
        sum_df = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        sum_df.columns = ['Supplier', 'Due Amount']
        sum_df = sum_df[sum_df['Due Amount'] != 0].sort_values('Due Amount', ascending=False)
        st.table(sum_df)
        
        st.divider()
        st.subheader("📋 All Transactions")
        st.dataframe(d_df, use_container_width=True)
