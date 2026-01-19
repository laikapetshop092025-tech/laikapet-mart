import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

# Initialize session states
if 'bill_cart' not in st.session_state: 
    st.session_state.bill_cart = []
if 'pur_cart' not in st.session_state: 
    st.session_state.pur_cart = []
if 'last_check_date' not in st.session_state: 
    st.session_state.last_check_date = None
if 'manual_cash' not in st.session_state:
    st.session_state.manual_cash = None
if 'manual_online' not in st.session_state:
    st.session_state.manual_online = None

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list, timeout=15)
        return response.text.strip() == "Success"
    except Exception as e:
        st.error(f"Save error: {str(e)}")
        return False

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
    except: 
        return pd.DataFrame()

def get_balance_from_sheet(mode):
    """Get balance from Google Sheets"""
    try:
        b_df = load_data("Balances")
        if b_df.empty or len(b_df.columns) < 2:
            # Initialize if empty
            save_data("Balances", ["Cash", 0.0])
            save_data("Balances", ["Online", 0.0])
            return 0.0
        
        rows = b_df[b_df.iloc[:, 0].str.strip() == mode]
        if len(rows) > 0:
            return float(pd.to_numeric(rows.iloc[0, 1], errors='coerce'))
        else:
            # Mode not found, initialize it
            save_data("Balances", [mode, 0.0])
            return 0.0
    except:
        return 0.0

def get_current_balance(mode):
    """Get current balance - only from session state"""
    if mode == "Cash":
        if st.session_state.manual_cash is None:
            # Initialize from sheets only once
            st.session_state.manual_cash = get_balance_from_sheet("Cash")
        return st.session_state.manual_cash
    elif mode == "Online":
        if st.session_state.manual_online is None:
            # Initialize from sheets only once
            st.session_state.manual_online = get_balance_from_sheet("Online")
        return st.session_state.manual_online
    return 0.0

def set_balance(mode, amount):
    """Set balance manually and save to sheets"""
    # Update session state
    if mode == "Cash":
        st.session_state.manual_cash = amount
    elif mode == "Online":
        st.session_state.manual_online = amount
    
    # Save to Google Sheets
    try:
        if save_data("Balances", [mode, amount]):
            # Wait a bit for sheets to update
            time.sleep(0.5)
            return True
        return False
    except:
        return False

def update_balance(amount, mode, operation='add'):
    """Update balance"""
    if mode not in ["Cash", "Online"]:
        return True
    
    try:
        current_bal = get_current_balance(mode)
        
        if operation == 'add':
            new_bal = current_bal + amount
        else:
            new_bal = current_bal - amount
        
        # Save to Google Sheets first
        if save_data("Balances", [mode, new_bal]):
            # Then update session state
            if mode == "Cash":
                st.session_state.manual_cash = new_bal
            elif mode == "Online":
                st.session_state.manual_online = new_bal
            
            st.success(f"✅ {mode}: ₹{current_bal:,.2f} → ₹{new_bal:,.2f}")
            time.sleep(0.5)
            return True
        else:
            st.error(f"❌ Failed to update {mode} balance in sheets!")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def archive_daily_data():
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

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password")
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. CHECK NEW DAY ---
today_dt = datetime.now().date()
if st.session_state.last_check_date != today_dt:
    if st.session_state.last_check_date is not None:
        archive_daily_data()
    st.session_state.last_check_date = today_dt

# --- 4. SIDEBAR ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🏢 Supplier Dues", "👑 Royalty Points"])
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
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    k_df = load_data("CustomerKhata")
    i_df = load_data("Inventory")
    
    cash_bal = get_current_balance("Cash")
    online_bal = get_current_balance("Online")
    total_bal = cash_bal + online_bal
    
    total_stock_val = 0
    if not i_df.empty and len(i_df.columns) > 3:
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        total_stock_val = (i_df['qty_v'] * i_df['rate_v']).sum()

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
    
    with st.expander("🔧 Balance Settings"):
        st.success("✅ Live Balance Tracking - All transactions update automatically!")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cash Balance")
            new_cash = st.number_input("Set Cash", value=float(cash_bal), step=1.0, key="cash_set")
            if st.button("Set Cash", key="btn_cash"):
                set_balance("Cash", new_cash)
                st.success(f"✅ Cash set to ₹{new_cash:,.2f}")
                time.sleep(1)
                st.rerun()
        with col2:
            st.subheader("Online Balance")
            new_online = st.number_input("Set Online", value=float(online_bal), step=1.0, key="online_set")
            if st.button("Set Online", key="btn_online"):
                set_balance("Online", new_online)
                st.success(f"✅ Online set to ₹{new_online:,.2f}")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    col_header1, col_header2 = st.columns(2)
    with col_header1:
        st.subheader(f"📈 Today's Report - {today_dt.strftime('%d %b %Y')}")
    with col_header2:
        st.subheader(f"🗓️ {curr_m_name} Report")
    
    s_today = s_df[s_df['Date'] == today_dt] if not s_df.empty and 'Date' in s_df.columns else pd.DataFrame()
    i_today = i_df[i_df['Date'] == today_dt] if not i_df.empty and 'Date' in i_df.columns else pd.DataFrame()
    e_today = e_df[e_df['Date'] == today_dt] if not e_df.empty and 'Date' in e_df.columns else pd.DataFrame()
    
    today_sale = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 3 else 0
    
    today_pur = 0
    if not i_today.empty and len(i_today.columns) > 3:
        qty_vals = pd.to_numeric(i_today.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals = pd.to_numeric(i_today.iloc[:, 3], errors='coerce').fillna(0)
        today_pur = (qty_vals * rate_vals).sum()
    
    today_exp = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty and len(e_today.columns) > 2 else 0
    today_profit = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 7 else 0
    
    # Calculate monthly data
    s_month = pd.DataFrame()
    i_month = pd.DataFrame()
    e_month = pd.DataFrame()
    
    if not s_df.empty and 'Date' in s_df.columns:
        s_df['Month'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.month
        s_df['Year'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.year
        s_month = s_df[(s_df['Month'] == curr_m) & (s_df['Year'] == today_dt.year)]
    
    if not i_df.empty and 'Date' in i_df.columns:
        i_df['Month'] = pd.to_datetime(i_df['Date'], errors='coerce').dt.month
        i_df['Year'] = pd.to_datetime(i_df['Date'], errors='coerce').dt.year
        i_month = i_df[(i_df['Month'] == curr_m) & (i_df['Year'] == today_dt.year)]
    
    if not e_df.empty and 'Date' in e_df.columns:
        e_df['Month'] = pd.to_datetime(e_df['Date'], errors='coerce').dt.month
        e_df['Year'] = pd.to_datetime(e_df['Date'], errors='coerce').dt.year
        e_month = e_df[(e_df['Month'] == curr_m) & (e_df['Year'] == today_dt.year)]
    
    month_sale = pd.to_numeric(s_month.iloc[:, 3], errors='coerce').sum() if not s_month.empty and len(s_month.columns) > 3 else 0
    
    month_pur = 0
    if not i_month.empty and len(i_month.columns) > 3:
        qty_vals = pd.to_numeric(i_month.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals = pd.to_numeric(i_month.iloc[:, 3], errors='coerce').fillna(0)
        month_pur = (qty_vals * rate_vals).sum()
    
    month_exp = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum() if not e_month.empty and len(e_month.columns) > 2 else 0
    month_profit = pd.to_numeric(s_month.iloc[:, 7], errors='coerce').sum() if not s_month.empty and len(s_month.columns) > 7 else 0
    
    # Display both reports side by side
    col1, col2 = st.columns(2)
    
    with col1:
        c1, c2 = st.columns(2)
        c1.metric("💰 Sale", f"₹{today_sale:,.2f}")
        c2.metric("📦 Purchase", f"₹{today_pur:,.2f}")
        c1.metric("💸 Expense", f"₹{today_exp:,.2f}")
        c2.metric("📈 Profit", f"₹{today_profit:,.2f}")
    
    with col2:
        c1, c2 = st.columns(2)
        c1.metric("💰 Sale", f"₹{month_sale:,.2f}")
        c2.metric("📦 Purchase", f"₹{month_pur:,.2f}")
        c1.metric("💸 Expense", f"₹{month_exp:,.2f}")
        c2.metric("📈 Profit", f"₹{month_profit:,.2f}")

# --- 6. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing & Royalty Club")
    inv_df = load_data("Inventory")
    s_df = load_data("Sales")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        c_name = st.text_input("Customer Name")
        c_ph = st.text_input("Customer Phone")
    
    with col2:
        st.write("")
        st.write("")
        # Calculate points for this customer
        if c_ph and not s_df.empty and len(s_df.columns) > 6:
            customer_sales = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)]
            pts_bal = pd.to_numeric(customer_sales.iloc[:, 6], errors='coerce').sum()
        else:
            pts_bal = 0
        
        st.metric("👑 Available Points", int(pts_bal))
    
    pay_m = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
    
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        q = st.number_input("Qty", 0.1)
        u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        p = st.number_input("Price", 1.0)
        
        col1, col2 = st.columns(2)
        with col1:
            rd = st.checkbox(f"Redeem {int(pts_bal)} Points?", disabled=(pts_bal <= 0))
        with col2:
            ref_ph = st.text_input("Referral Phone (Optional)", placeholder="For +10 bonus points")
        
        if st.button("➕ Add to Cart"):
            pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty and len(inv_df[inv_df.iloc[:, 0] == it]) > 0 else 0
            
            # Calculate points
            pts = int(((q*p)/100) * (5 if is_weekend else 2))
            pts_used = 0
            
            if rd and pts_bal > 0:
                pts_used = -int(pts_bal)
                pts += pts_used
            
            if ref_ph and ref_ph.strip():
                pts += 10
            
            st.session_state.bill_cart.append({
                "Item": it, 
                "Qty": f"{q} {u}", 
                "Price": p, 
                "Profit": (p-pur_r)*q, 
                "Pts": pts,
                "PtsUsed": pts_used
            })
            st.rerun()
    
    if st.session_state.bill_cart:
        st.table(pd.DataFrame(st.session_state.bill_cart))
        total_amt = sum([item['Price'] for item in st.session_state.bill_cart])
        total_pts = sum([item['Pts'] for item in st.session_state.bill_cart])
        
        st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        st.info(f"🎁 Points Earned: +{total_pts}")
        
        if st.button("✅ Save Bill & Send WhatsApp", type="primary"):
            # Save to Sales
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            
            # Update balance
            if pay_m in ["Cash", "Online"]:
                update_balance(total_amt, pay_m, 'add')
            else:
                save_data("CustomerKhata", [f"{c_name}({c_ph})", total_amt, str(today_dt), "Udhaar"])
                st.success("✅ Bill saved as Udhaar!")
            
            # Generate WhatsApp message
            items_text = "\n".join([f"• {item['Item']} - {item['Qty']} - ₹{item['Price']}" for item in st.session_state.bill_cart])
            
            message = f"""🐾 *LAIKA PET MART* 🐾
            
नमस्ते {c_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{total_amt:,.2f}
👑 *आपके प्वाइंट्स:* +{total_pts}

धन्यवाद! 🙏
फिर से आइएगा! 🐕"""
            
            import urllib.parse
            encoded_msg = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/91{c_ph}?text={encoded_msg}"
            
            st.success("✅ Bill saved successfully!")
            st.markdown(f"### 📱 Send WhatsApp Message")
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">📲 Send via WhatsApp</button></a>', unsafe_allow_html=True)
            
            st.session_state.bill_cart = []
            time.sleep(3)
            st.rerun()
    
    # TODAY'S BILLS SECTION
    st.divider()
    st.subheader("📋 Today's Bills")
    
    if not s_df.empty and 'Date' in s_df.columns:
        today_bills = s_df[s_df['Date'] == today_dt]
        
        if not today_bills.empty:
            # Group by customer
            customer_bills = {}
            for _, row in today_bills.iterrows():
                customer_info = str(row.iloc[5]) if len(row) > 5 else "Unknown"
                item = str(row.iloc[1]) if len(row) > 1 else ""
                qty = str(row.iloc[2]) if len(row) > 2 else ""
                price = float(row.iloc[3]) if len(row) > 3 else 0
                mode = str(row.iloc[4]) if len(row) > 4 else ""
                points = int(pd.to_numeric(row.iloc[6], errors='coerce')) if len(row) > 6 else 0
                
                if customer_info not in customer_bills:
                    customer_bills[customer_info] = {
                        'items': [],
                        'total': 0,
                        'mode': mode,
                        'points': 0
                    }
                
                customer_bills[customer_info]['items'].append(f"{item} - {qty}")
                customer_bills[customer_info]['total'] += price
                customer_bills[customer_info]['points'] += points
            
            # Display each bill with WhatsApp button
            for customer_info, bill_data in customer_bills.items():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    # Extract name and phone
                    if "(" in customer_info and ")" in customer_info:
                        cust_name = customer_info.split("(")[0].strip()
                        cust_phone = customer_info.split("(")[1].replace(")", "").strip()
                    else:
                        cust_name = customer_info
                        cust_phone = ""
                    
                    with col1:
                        st.write(f"**{cust_name}**")
                        for item in bill_data['items']:
                            st.write(f"  • {item}")
                    
                    with col2:
                        st.write(f"💰 ₹{bill_data['total']:,.2f}")
                        st.write(f"💳 {bill_data['mode']}")
                    
                    with col3:
                        st.write(f"👑 +{bill_data['points']} Points")
                        st.write(f"📱 {cust_phone}")
                    
                    with col4:
                        if cust_phone:
                            # Create WhatsApp message
                            items_text = "\n".join(bill_data['items'])
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {cust_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{bill_data['total']:,.2f}
👑 *आपके प्वाइंट्स:* +{bill_data['points']}

धन्यवाद! 🙏
फिर से आइएगा! 🐕"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; font-size: 20px;">💬</button></a>', unsafe_allow_html=True)
                    
                    st.divider()
        else:
            st.info("No bills generated today yet.")
    else:
        st.info("No sales data available.")

# --- 7. PURCHASE ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    with st.expander("📥 Add Stock", expanded=True):
        n = st.text_input("Item Name")
        q = st.number_input("Quantity", min_value=0.1, value=1.0)
        u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        r = st.number_input("Rate per Unit", min_value=0.0, value=0.0)
        m = st.selectbox("Paid From", ["Cash", "Online", "Pocket", "Hand"])
        
        if st.button("➕ Save Purchase", type="primary"):
            if q > 0 and r > 0 and n.strip():
                total_cost = q * r
                save_data("Inventory", [n, f"{q} {u}", "Stock", r, str(today_dt), m])
                
                if m in ["Cash", "Online"]:
                    update_balance(total_cost, m, 'subtract')
                else:
                    st.success(f"✅ Stock added! (Paid from {m})")
                
                time.sleep(1)
                st.rerun()
    
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
        i_df['value'] = i_df['qty_v'] * i_df['rate_v']
        t_v = i_df['value'].sum()
        
        st.subheader(f"💰 Total Stock Value: ₹{t_v:,.2f}")
        
        stock_summary = i_df.groupby(i_df.columns[0]).agg({
            i_df.columns[1]: 'last',
            i_df.columns[3]: 'last',
            'qty_v': 'last',
            'value': 'last'
        }).reset_index()
        stock_summary.columns = ['Item', 'Quantity', 'Rate', 'Qty_Numeric', 'Value']
        
        # Separate low stock items
        low_stock_items = []
        normal_stock_items = []
        
        for _, row in stock_summary.iterrows():
            item_dict = {
                'Item': row['Item'],
                'Quantity': row['Quantity'],
                'Rate': f"₹{row['Rate']:.2f}",
                'Stock Value': f"₹{row['Value']:.2f}",
                'Qty_Numeric': row['Qty_Numeric']
            }
            
            if row['Qty_Numeric'] < 2:
                low_stock_items.append(item_dict)
            else:
                normal_stock_items.append(item_dict)
        
        # Display LOW STOCK section
        if low_stock_items:
            st.divider()
            st.subheader("🚨 LOW STOCK ALERT")
            
            low_stock_df = pd.DataFrame(low_stock_items)
            low_stock_df = low_stock_df.drop('Qty_Numeric', axis=1)
            
            for _, row in low_stock_df.iterrows():
                st.error(f"🚨 **{row['Item']}** - {row['Quantity']} - Rate: {row['Rate']} - Value: {row['Stock Value']}")
            
            # Download button for low stock
            st.divider()
            csv = low_stock_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Low Stock Report",
                data=csv,
                file_name=f"low_stock_report_{today_dt}.csv",
                mime="text/csv",
                type="primary"
            )
        
        # Display NORMAL STOCK
        if normal_stock_items:
            st.divider()
            st.subheader("✅ Available Stock")
            for item in normal_stock_items:
                st.info(f"✅ **{item['Item']}** - {item['Quantity']} - Rate: {item['Rate']} - Value: {item['Stock Value']}")

# --- 9. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expense Entry")
    
    with st.form("ex"):
        cat = st.selectbox("Category", ["Rent", "Salary", "Food", "Transport", "Utilities", "Miscellaneous", "Other"])
        amt = st.number_input("Amount", min_value=0.0)
        m = st.selectbox("Mode", ["Cash", "Online"])
        note = st.text_input("Note (Optional)")
        
        if st.form_submit_button("💾 Save Expense", type="primary"):
            if amt > 0:
                save_data("Expenses", [str(today_dt), cat, amt, m, note])
                update_balance(amt, m, 'subtract')
                time.sleep(1)
                st.rerun()
    
    e_df = load_data("Expenses")
    if not e_df.empty: 
        st.subheader("📋 Recent Expenses")
        st.dataframe(e_df.tail(15), use_container_width=True)

# --- 10. PET REGISTER ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    
    with st.form("pet"):
        c1, c2 = st.columns(2)
        on = c1.text_input("Owner")
        ph = c2.text_input("Phone")
        br = c1.text_input("Breed")
        age = c2.number_input("Age (Months)", 1)
        wt = c1.number_input("Weight (Kg)", 0.1)
        vd = c2.date_input("Last Vax")
        
        if st.form_submit_button("💾 Save Pet", type="primary"):
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
        
        if st.form_submit_button("💾 Save Entry", type="primary"):
            if a > 0 and n.strip():
                final_amt = a if "+" in t else -a
                save_data("CustomerKhata", [n, final_amt, str(today_dt), m])
                
                if "-" in t and m in ["Cash", "Online"]:
                    update_balance(a, m, 'add')
                else:
                    st.success("✅ Entry saved!")
                
                time.sleep(1)
                st.rerun()
    
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
        
        if st.form_submit_button("💾 Save", type="primary"):
            if a > 0 and s.strip():
                final_amt = a if "+" in t else -a
                save_data("Dues", [s, final_amt, str(today_dt), m])
                
                if "-" in t and m in ["Cash", "Online"]:
                    update_balance(a, m, 'subtract')
                else:
                    st.success("✅ Entry saved!")
                
                time.sleep(1)
                st.rerun()
    
    d_df = load_data("Dues")
    if not d_df.empty and len(d_df.columns) > 1:
        st.divider()
        st.subheader("📊 Supplier Balance Summary")
        
        # Calculate balance per supplier
        sum_df = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
        sum_df.columns = ['Supplier', 'Balance']
        
        # Separate those who owe money (positive balance) and those we owe (negative)
        suppliers_owe_us = sum_df[sum_df['Balance'] < 0].copy()
        suppliers_owe_us['Balance'] = -suppliers_owe_us['Balance']
        suppliers_owe_us = suppliers_owe_us.sort_values('Balance', ascending=False)
        
        we_owe_suppliers = sum_df[sum_df['Balance'] > 0].copy()
        we_owe_suppliers = we_owe_suppliers.sort_values('Balance', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💰 We Paid Less (We Owe)")
            if not we_owe_suppliers.empty:
                for _, row in we_owe_suppliers.iterrows():
                    st.error(f"📤 **{row['Supplier']}**: ₹{row['Balance']:,.2f}")
                st.metric("Total We Owe", f"₹{we_owe_suppliers['Balance'].sum():,.2f}")
            else:
                st.success("✅ No pending dues!")
        
        with col2:
            st.markdown("### 💵 They Paid Less (They Owe)")
            if not suppliers_owe_us.empty:
                for _, row in suppliers_owe_us.iterrows():
                    st.info(f"📥 **{row['Supplier']}**: ₹{row['Balance']:,.2f}")
                st.metric("Total They Owe", f"₹{suppliers_owe_us['Balance'].sum():,.2f}")
            else:
                st.info("No receivables")
        
        st.divider()
        st.subheader("📋 All Transactions")
        st.dataframe(d_df, use_container_width=True)

# --- 13. ROYALTY POINTS ---
elif menu == "👑 Royalty Points":
    st.header("👑 Royalty Points System")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 6:
        st.info("💡 Weekend shopping gives 5x points! Weekday shopping gives 2x points!")
        
        # Calculate points per customer
        customer_points = {}
        for _, row in s_df.iterrows():
            customer_info = str(row.iloc[5]) if len(row) > 5 else ""
            points = pd.to_numeric(row.iloc[6], errors='coerce') if len(row) > 6 else 0
            
            if customer_info and customer_info != "nan":
                if customer_info in customer_points:
                    customer_points[customer_info] += points
                else:
                    customer_points[customer_info] = points
        
        # Convert to dataframe
        if customer_points:
            points_df = pd.DataFrame([
                {
                    "Customer": k.split("(")[0] if "(" in k else k,
                    "Phone": k.split("(")[1].replace(")", "") if "(" in k else "N/A",
                    "Total Points": int(v)
                }
                for k, v in customer_points.items()
            ])
            
            points_df = points_df.sort_values("Total Points", ascending=False)
            
            # Filter options
            col1, col2 = st.columns([2, 1])
            with col1:
                search = st.text_input("🔍 Search by Name or Phone", "")
            with col2:
                min_points = st.number_input("Min Points Filter", min_value=0, value=0)
            
            # Apply filters
            if search:
                points_df = points_df[
                    points_df['Customer'].str.contains(search, case=False, na=False) | 
                    points_df['Phone'].str.contains(search, case=False, na=False)
                ]
            
            if min_points > 0:
                points_df = points_df[points_df['Total Points'] >= min_points]
            
            # Display metrics
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("👥 Total Customers", len(customer_points))
            c2.metric("🎁 Total Points Given", sum(customer_points.values()))
            c3.metric("⭐ Active Customers", len([v for v in customer_points.values() if v > 0]))
            
            st.divider()
            st.subheader("📊 Customer Points Leaderboard")
            
            # Color code the dataframe
            def highlight_points(row):
                if row['Total Points'] >= 100:
                    return ['background-color: #D4EDDA'] * len(row)
                elif row['Total Points'] >= 50:
                    return ['background-color: #FFF3CD'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = points_df.style.apply(highlight_points, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Download option
            csv = points_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Points Report",
                data=csv,
                file_name=f"royalty_points_{today_dt}.csv",
                mime="text/csv"
            )
        else:
            st.info("No points data available yet. Start billing to earn points!")
    else:
        st.info("No sales data found. Start billing to track royalty points!")

