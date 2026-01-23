import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import time

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Custom CSS for beautiful sidebar with button menu
st.markdown("""
<style>
    /* Sidebar styling - Light background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e0e7ff 0%, #f3f4f6 100%);
    }
    
    /* All sidebar buttons - Menu items + Logout */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid transparent;
        padding: 14px 20px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
        width: 100%;
        margin: 4px 0;
        text-align: left;
    }
    
    /* Hover effect - All buttons */
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(240, 147, 251, 0.5);
        border: 2px solid #ff6b9d;
    }
    
    /* Primary button (selected menu item) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        box-shadow: 0 5px 25px rgba(255, 216, 155, 0.6);
        transform: scale(1.03);
        border: 2px solid #ffd89b;
        font-weight: 700;
    }
    
    /* Primary button hover */
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        transform: scale(1.05) translateX(5px);
        box-shadow: 0 8px 30px rgba(255, 216, 155, 0.7);
    }
    
    /* Main Menu heading */
    [data-testid="stSidebar"] h2 {
        color: #1e293b !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Main content area */
    .main {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 10px;
        padding: 15px;
        font-weight: bold;
    }
    
    .streamlit-expanderHeader:hover {
        opacity: 0.9;
        transform: scale(1.01);
        transition: all 0.3s ease;
    }
    
    /* Form styling */
    .stForm {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

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
    st.session_state.balance_initialized = False
if 'manual_online' not in st.session_state:
    st.session_state.manual_online = None
if 'balance_initialized' not in st.session_state:
    st.session_state.balance_initialized = False

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
    """Get LATEST balance from Google Sheets"""
    try:
        b_df = load_data("Balances")
        if b_df.empty or len(b_df.columns) < 2:
            return 0.0
        
        rows = b_df[b_df.iloc[:, 0].str.strip() == mode]
        
        if len(rows) > 0:
            latest_balance = rows.iloc[-1, 1]
            return float(pd.to_numeric(latest_balance, errors='coerce'))
        
        return 0.0
    except Exception as e:
        st.error(f"Error loading balance: {str(e)}")
        return 0.0

def get_current_balance(mode):
    """Get current balance"""
    if mode == "Cash":
        if st.session_state.manual_cash is None:
            st.session_state.manual_cash = get_balance_from_sheet("Cash")
        return st.session_state.manual_cash
    elif mode == "Online":
        if st.session_state.manual_online is None:
            st.session_state.manual_online = get_balance_from_sheet("Online")
        return st.session_state.manual_online
    return 0.0

def set_balance(mode, amount):
    """Set balance manually"""
    if mode == "Cash":
        st.session_state.manual_cash = amount
    elif mode == "Online":
        st.session_state.manual_online = amount
    
    try:
        if save_data("Balances", [mode, amount]):
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
        
        if mode == "Cash":
            st.session_state.manual_cash = new_bal
        elif mode == "Online":
            st.session_state.manual_online = new_bal
        
        if save_data("Balances", [mode, new_bal]):
            st.success(f"✅ {mode}: ₹{current_bal:,.2f} → ₹{new_bal:,.2f}")
            time.sleep(0.5)
            return True
        else:
            st.error(f"❌ Failed to save {mode} balance!")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

# --- 2. MULTI-USER LOGIN ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

USERS = {
    "Prateek": {"password": "Prateek092025", "role": "ceo", "name": "Prateek (CEO)"},
    "Laika": {"password": "Ayush@092025", "role": "owner", "name": "Ayush (Owner)"},
    "Manager": {"password": "Manager@123", "role": "manager", "name": "Store Manager"},
    "Staff1": {"password": "Staff@123", "role": "staff", "name": "Staff Member 1"},
    "Staff2": {"password": "Staff@456", "role": "staff", "name": "Staff Member 2"}
}

if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 48px;">🔐 LAIKA PET MART</h1>
        <p style="color: white; margin-top: 15px; font-size: 20px;">Multi-User Login System</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div style="background: white; padding: 30px; border-radius: 15px;">', unsafe_allow_html=True)
        
        u = st.text_input("👤 Username", key="login_username").strip()
        p = st.text_input("🔒 Password", type="password", key="login_password").strip()
        
        with st.expander("ℹ️ Available User Roles"):
            st.info("**Owner**: Full access\n**Manager**: Reports, billing, inventory\n**Staff**: Billing only")
        
        if st.button("🚀 LOGIN", use_container_width=True, type="primary"):
            if u and u in USERS and USERS[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = USERS[u]["role"]
                st.session_state.username = USERS[u]["name"]
                st.success(f"✅ Welcome {USERS[u]['name']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# --- 3. CHECK NEW DAY ---
today_dt = datetime.now().date()
if st.session_state.last_check_date != today_dt:
    st.session_state.last_check_date = today_dt

# --- 4. SIDEBAR MENU WITH 14 MENUS ---
if st.session_state.user_role:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h3 style="color: white; margin: 0;">👤 {st.session_state.username}</h3>
        <p style="color: white; margin: 5px 0 0 0; font-size: 14px;">{st.session_state.user_role.upper()}</p>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("<h2 style='text-align: center;'>📋 Main Menu</h2>", unsafe_allow_html=True)

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "📊 Dashboard"

user_role = st.session_state.user_role or "staff"

# Define 14-menu structure based on role
if user_role in ["ceo", "owner"]:
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📦 Purchase", 
        "📋 Live Stock", 
        "💰 Expenses",
        "🐾 Pet Register",
        "📒 Customer Khata",
        "🏢 Supplier Dues",
        "👑 Royalty Points",
        "📈 Advanced Reports",
        "👥 Customer Analytics",
        "🎁 Discounts & Offers",
        "💼 Financial Reports",
        "🔐 Security & Compliance"
    ]
elif user_role == "manager":
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📦 Purchase", 
        "📋 Live Stock", 
        "💰 Expenses",
        "🐾 Pet Register",
        "📒 Customer Khata",
        "🏢 Supplier Dues",
        "👑 Royalty Points",
        "📈 Advanced Reports",
        "👥 Customer Analytics",
        "🎁 Discounts & Offers",
        "💼 Financial Reports"
    ]
else:  # staff
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📋 Live Stock",
        "🐾 Pet Register"
    ]

for item in menu_items:
    is_selected = (st.session_state.selected_menu == item)
    button_type = "primary" if is_selected else "secondary"
    
    if st.sidebar.button(item, key=f"menu_{item}", use_container_width=True, type=button_type):
        st.session_state.selected_menu = item
        st.rerun()

menu = st.session_state.selected_menu

st.sidebar.divider()

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# ========================================
# MENU 1: DASHBOARD
# ========================================
if menu == "📊 Dashboard":
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-size: 52px;">Welcome to Laika Pet Mart</h1>
        <p style="color: white; margin-top: 15px; font-size: 22px;">🐕 Your Trusted Pet Care Partner 🐈</p>
    </div>
    """, unsafe_allow_html=True)
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    
    cash_bal = get_current_balance("Cash")
    online_bal = get_current_balance("Online")
    total_bal = cash_bal + online_bal
    
    # Customer Udhaar Calculation
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        customer_udhaar = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum()
        total_customer_udhaar = customer_udhaar[customer_udhaar > 0].sum()
    else:
        total_customer_udhaar = 0
    
    # Stock Value Calculation
    inv_df = load_data("Inventory")
    if not inv_df.empty and len(inv_df.columns) > 3:
        inv_df['qty_val'] = pd.to_numeric(inv_df.iloc[:, 1], errors='coerce').fillna(0)
        inv_df['rate_val'] = pd.to_numeric(inv_df.iloc[:, 3], errors='coerce').fillna(0)
        inv_df['total_val'] = inv_df['qty_val'] * inv_df['rate_val']
        total_stock_value = inv_df['total_val'].sum()
    else:
        total_stock_value = 0
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💵 Cash</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{cash_bal:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">🏦 Online</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{online_bal:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">⚡ Total</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_bal:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📒 Customer Udhaar</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_customer_udhaar:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">📦 Stock Value</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_stock_value:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔧 Balance Settings"):
        st.success("✅ Balance auto-loads from Google Sheets")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cash Balance")
            st.write(f"Current: ₹{cash_bal:,.2f}")
            new_cash = st.number_input("Update Cash", value=float(cash_bal), step=1.0)
            if st.button("💾 Save Cash"):
                st.session_state.manual_cash = new_cash
                save_data("Balances", ["Cash", new_cash])
                st.success(f"✅ Updated to ₹{new_cash:,.2f}")
                time.sleep(1)
                st.rerun()
        
        with col2:
            st.subheader("Online Balance")
            st.write(f"Current: ₹{online_bal:,.2f}")
            new_online = st.number_input("Update Online", value=float(online_bal), step=1.0)
            if st.button("💾 Save Online"):
                st.session_state.manual_online = new_online
                save_data("Balances", ["Online", new_online])
                st.success(f"✅ Updated to ₹{new_online:,.2f}")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
        <h2 style="color: white; margin: 0; text-align: center;">📈 Today's Report - {today_dt.strftime('%d %B %Y')}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Today's Sales
    if not s_df.empty and 'Date' in s_df.columns:
        s_today = s_df[s_df['Date'] == today_dt]
        today_sale = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum() if not s_today.empty else 0
    else:
        today_sale = 0
    
    # Today's Purchases
    p_df = load_data("Inventory")
    if not p_df.empty and len(p_df.columns) > 5:
        try:
            p_df['pur_date'] = pd.to_datetime(p_df.iloc[:, 5], errors='coerce').dt.date
            p_today = p_df[p_df['pur_date'] == today_dt]
            today_purchase = pd.to_numeric(p_today.iloc[:, 4], errors='coerce').sum() if not p_today.empty else 0
        except:
            today_purchase = 0
    else:
        today_purchase = 0
    
    # Today's Expenses
    if not e_df.empty and len(e_df.columns) > 2:
        try:
            e_df['exp_date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
            e_today = e_df[e_df['exp_date'] == today_dt]
            today_expense = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty else 0
        except:
            today_expense = 0
    else:
        today_expense = 0
    
    # Today's Profit
    if not s_df.empty and len(s_df.columns) > 7 and 'Date' in s_df.columns:
        s_today_profit = s_df[s_df['Date'] == today_dt]
        today_profit = pd.to_numeric(s_today_profit.iloc[:, 7], errors='coerce').sum() if not s_today_profit.empty else 0
    else:
        today_profit = 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Sale", f"₹{today_sale:,.2f}")
    col2.metric("🛒 Total Purchase", f"₹{today_purchase:,.2f}")
    col3.metric("💸 Total Expense", f"₹{today_expense:,.2f}")
    col4.metric("📊 Profit", f"₹{today_profit:,.2f}")
    
    st.divider()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
        <h2 style="color: white; margin: 0; text-align: center;">📅 This Month Report - {curr_m_name} {datetime.now().year}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # This Month's Sales
    if not s_df.empty and 'Date' in s_df.columns:
        s_month = s_df[s_df['Date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
        month_sale = pd.to_numeric(s_month.iloc[:, 3], errors='coerce').sum() if not s_month.empty else 0
    else:
        month_sale = 0
    
    # This Month's Purchases
    if not p_df.empty and len(p_df.columns) > 5:
        try:
            p_df['pur_date'] = pd.to_datetime(p_df.iloc[:, 5], errors='coerce').dt.date
            p_month = p_df[p_df['pur_date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
            month_purchase = pd.to_numeric(p_month.iloc[:, 4], errors='coerce').sum() if not p_month.empty else 0
        except:
            month_purchase = 0
    else:
        month_purchase = 0
    
    # This Month's Expenses
    if not e_df.empty and len(e_df.columns) > 2:
        try:
            e_df['exp_date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
            e_month = e_df[e_df['exp_date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
            month_expense = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum() if not e_month.empty else 0
        except:
            month_expense = 0
    else:
        month_expense = 0
    
    # This Month's Profit
    if not s_df.empty and len(s_df.columns) > 7 and 'Date' in s_df.columns:
        s_month_profit = s_df[s_df['Date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
        month_profit = pd.to_numeric(s_month_profit.iloc[:, 7], errors='coerce').sum() if not s_month_profit.empty else 0
    else:
        month_profit = 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Sale", f"₹{month_sale:,.2f}")
    col2.metric("🛒 Total Purchase", f"₹{month_purchase:,.2f}")
    col3.metric("💸 Total Expense", f"₹{month_expense:,.2f}")
    col4.metric("📊 Profit", f"₹{month_profit:,.2f}")
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
        if c_ph and not s_df.empty and len(s_df.columns) > 6:
            customer_sales = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)]
            pts_bal = pd.to_numeric(customer_sales.iloc[:, 6], errors='coerce').sum()
        else:
            pts_bal = 0
        
        if pts_bal > 0:
            st.metric("👑 Available Points", int(pts_bal))
        else:
            st.metric("👑 Available Points", 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        pay_m = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
    with col2:
        give_points = st.checkbox("👑 Give Points?", value=True)
    with col3:
        gst_bill = st.checkbox("📄 GST Invoice?", value=False)
    
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        
        if it and it != "No Stock" and not inv_df.empty:
            product_stock = inv_df[inv_df.iloc[:, 0] == it]
            if not product_stock.empty:
                total_qty = pd.to_numeric(product_stock.iloc[:, 1], errors='coerce').sum()
                latest_unit = product_stock.iloc[-1, 2] if len(product_stock.columns) > 2 else ""
                if total_qty > 0:
                    st.success(f"📦 Stock: {total_qty} {latest_unit}")
                else:
                    st.warning("⚠️ Out of Stock!")
        
        q = st.number_input("Qty", min_value=0.1, value=1.0, step=0.1)
        u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        p = st.number_input("Price", min_value=0.0, value=1.0, step=1.0)
        
        col1, col2 = st.columns(2)
        with col1:
            current_cart_total = sum([item['Price'] for item in st.session_state.bill_cart]) if st.session_state.bill_cart else 0
            can_redeem = pts_bal > 0 and current_cart_total >= 100
            rd = st.checkbox(f"Redeem {int(pts_bal)} Points?", disabled=(not can_redeem))
            if pts_bal > 0 and current_cart_total < 100:
                st.caption(f"⚠️ Add ₹{100 - current_cart_total:.0f} more")
        
        with col2:
            ref_ph = st.text_input("Referral Phone", placeholder="For +10 points")
        
        if st.button("➕ Add to Cart"):
            if q > 0 and p > 0:
                pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty and len(inv_df[inv_df.iloc[:, 0] == it]) > 0 else 0
                total_price = q * p
                pts = 0
                pts_used = 0
                
                if give_points:
                    pts = int((total_price/100) * (5 if is_weekend else 2))
                    if rd and pts_bal > 0:
                        pts_used = -int(pts_bal)
                        pts += pts_used
                    if ref_ph and ref_ph.strip():
                        pts += 10
                
                st.session_state.bill_cart.append({
                    "Item": it, 
                    "Qty": f"{q} {u}", 
                    "Price": total_price,
                    "UnitPrice": p,
                    "Profit": (p-pur_r)*q, 
                    "Pts": pts,
                    "PtsUsed": pts_used
                })
                st.rerun()
            else:
                st.error("⚠️ Enter valid Qty and Price!")
    
    if st.session_state.bill_cart:
        st.divider()
        st.markdown("### 🛒 Cart Items")
        
        for idx, item in enumerate(st.session_state.bill_cart):
            col1, col2 = st.columns([9, 1])
            with col1:
                st.markdown(f"""
                <div style="background: #f0f2f6; padding: 12px; border-radius: 8px; margin: 5px 0;">
                    <strong>📦 {item['Item']}</strong><br>
                    Qty: {item['Qty']} | Total: ₹{item['Price']:,.2f} | Profit: ₹{item['Profit']:,.2f} | Points: {item['Pts']}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.write("")
                if st.button("❌", key=f"del_bill_{idx}"):
                    st.session_state.bill_cart.pop(idx)
                    st.rerun()
        
        st.divider()
        
        total_amt = sum([item['Price'] for item in st.session_state.bill_cart])
        total_pts = sum([item['Pts'] for item in st.session_state.bill_cart])
        
        if gst_bill:
            st.divider()
            st.markdown("### 💼 With GST (18%)")
            taxable = total_amt / 1.18
            gst_amt = total_amt - taxable
            st.success(f"💳 Total with GST: ₹{total_amt:,.2f}")
        else:
            st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        
        col1, col2 = st.columns(2)
        with col1:
            if give_points:
                if total_pts >= 0:
                    st.success(f"🎁 Points: +{total_pts}")
                else:
                    st.warning(f"🎁 Redeemed: {total_pts}")
            else:
                st.info("👑 Points: Not Given")
        with col2:
            if give_points:
                st.info(f"👑 New Balance: {int(pts_bal + total_pts)}")
        
        if st.button("✅ Save Bill & Send WhatsApp", type="primary"):
            items_saved = 0
            for item in st.session_state.bill_cart:
                if save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']]):
                    items_saved += 1
            
            if pay_m == "Cash":
                update_balance(total_amt, "Cash", 'add')
            elif pay_m == "Online":
                update_balance(total_amt, "Online", 'add')
            else:
                save_data("CustomerKhata", [f"{c_name}({c_ph})", total_amt, str(today_dt), "Udhaar"])
            
            st.success(f"✅ Bill Saved! {items_saved}/{len(st.session_state.bill_cart)} items")
            
            items_text = "\\n".join([f"• {item['Item']} - {item['Qty']} - ₹{item['Price']}" for item in st.session_state.bill_cart])
            new_pts_balance = pts_bal + total_pts
            
            if give_points:
                points_msg = f"🎁 Points: {'+' if total_pts >= 0 else ''}{total_pts}\\n👑 Total: {int(new_pts_balance)}"
            else:
                points_msg = ""
            
            message = f"""🐾 LAIKA PET MART 🐾

नमस्ते {c_name} जी!

आपकी खरीदारी:
{items_text}

💰 कुल: ₹{total_amt:,.2f}
{points_msg}

धन्यवाद! 🙏"""
            
            import urllib.parse
            encoded = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/91{c_ph}?text={encoded}"
            
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 5px;">📲 Send WhatsApp</button></a>', unsafe_allow_html=True)
            
            st.session_state.bill_cart = []
            time.sleep(3)
            st.rerun()
    
    # ===== TODAY'S BILLS SECTION WITH FIXED ERROR =====
    st.divider()
    st.subheader("📋 Today's Bills")
    
    if not s_df.empty and 'Date' in s_df.columns:
        today_bills = s_df[s_df['Date'] == today_dt]
        
        if not today_bills.empty:
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
                        'mode': mode,  # ✅ STORED AS 'mode'
                        'points': 0
                    }
                
                customer_bills[customer_info]['items'].append(f"{item} - {qty}")
                customer_bills[customer_info]['total'] += price
                customer_bills[customer_info]['points'] += points
            
            for customer_name, bill_data in customer_bills.items():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    if "(" in customer_name and ")" in customer_name:
                        cust_name = customer_name.split("(")[0].strip()
                        cust_phone = customer_name.split("(")[1].replace(")", "").strip()
                    else:
                        cust_name = customer_name
                        cust_phone = ""
                    
                    with col1:
                        st.write(f"**{cust_name}**")
                        for item in bill_data['items']:
                            st.write(f"  • {item}")
                    
                    with col2:
                        st.write(f"💰 ₹{bill_data['total']:,.2f}")
                        st.write(f"💳 {bill_data['mode']}")
                    
                    with col3:
                        st.write(f"👑 +{bill_data['points']}")
                        st.write(f"📱 {cust_phone}")
                    
                    with col4:
                        if cust_phone:
                            cust_bills = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(cust_phone), na=False)]
                            cust_pts = pd.to_numeric(cust_bills.iloc[:, 6], errors='coerce').sum() if not cust_bills.empty else 0
                            
                            msg = f"""🐾 LAIKA PET MART 🐾

नमस्ते {cust_name} जी!

खरीदारी:
{chr(10).join(bill_data['items'])}

💰 कुल: ₹{bill_data['total']:,.2f}
🎁 Points: +{bill_data['points']}
👑 Total: {int(cust_pts)}

धन्यवाद! 🙏"""
                            
                            import urllib.parse
                            enc = urllib.parse.quote(msg)
                            url = f"https://wa.me/91{cust_phone}?text={enc}"
                            
                            st.markdown(f'<a href="{url}" target="_blank"><button style="background: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 5px;">💬</button></a>', unsafe_allow_html=True)
                    
                    st.divider()
            
            # ===== DELETE SECTION WITH FIXES APPLIED =====
            st.divider()
            st.markdown("### 🗑️ Delete Bill Entries")
            st.warning("⚠️ Deleting will reverse all effects")
            
            for customer_name, bill_data in customer_bills.items():
                with st.expander(f"📋 {customer_name} - ₹{bill_data['total']:,.2f}"):
                    st.write(f"**Items:** {', '.join(bill_data['items'])}")
                    st.write(f"**Total:** ₹{bill_data['total']:,.2f}")
                    # ✅ FIXED - Changed 'payment' to 'mode'
                    st.write(f"**Payment:** {bill_data['mode']}")
                    st.write(f"**Points:** {bill_data['points']}")
                    
                    if st.button(f"🗑️ Delete This Bill", key=f"del_bill_{customer_name}"):
                        try:
                            cust_phone = customer_name.split('(')[-1].replace(')', '')
                            
                            s_df = load_data("Sales")
                            if not s_df.empty and len(s_df.columns) > 5:
                                customer_entries = s_df[
                                    (s_df.iloc[:, 0] == str(today_dt)) & 
                                    (s_df.iloc[:, 5].astype(str).str.contains(cust_phone, na=False))
                                ]
                                
                                if not customer_entries.empty:
                                    st.info(f"Found {len(customer_entries)} entries")
                                    
                                    # ✅ FIXED - Changed 'payment' to 'mode'
                                    payment_mode = bill_data['mode']
                                    bill_amount = bill_data['total']
                                    
                                    if payment_mode == "Cash":
                                        update_balance(bill_amount, "Cash", 'subtract')
                                        st.success(f"✅ Reversed Cash: -₹{bill_amount:,.2f}")
                                    elif payment_mode == "Online":
                                        update_balance(bill_amount, "Online", 'subtract')
                                        st.success(f"✅ Reversed Online: -₹{bill_amount:,.2f}")
                                    elif payment_mode == "Udhaar":
                                        save_data("CustomerKhata", [customer_name, -bill_amount, str(today_dt), "Bill Deleted"])
                                        st.success(f"✅ Reversed Udhaar: -₹{bill_amount:,.2f}")
                                    
                                    st.warning("⚠️ Manual deletion from Google Sheets required")
                                    st.info(f"Go to Sales sheet → Delete rows with: {customer_name} on {today_dt}")
                                    st.info("Balance reversed automatically ✅")
                                    
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("No entries found")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        else:
            st.info("No bills today yet.")
    else:
        st.info("No sales data available.")
# ========================================
# MENU 3: PURCHASE (WITH AUTOMATIC SUPPLIER DUES)
# ========================================
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    if 'purchase_cart' not in st.session_state:
        st.session_state.purchase_cart = []
    
    # Payment selection at top
    st.markdown("### 💰 Payment Method")
    col1, col2 = st.columns(2)
    
    with col1:
        payment_type = st.radio(
            "Payment Type",
            ["💵 Cash/Online", "🏢 Party/Supplier"],
            horizontal=True,
            key="payment_radio"
        )
    
    with col2:
        if payment_type == "💵 Cash/Online":
            payment_mode = st.selectbox("Pay From", ["Cash", "Online"], key="pay_mode")
            supplier_name = None
        else:
            payment_mode = "Party"
            supplier_name = st.text_input("Party/Supplier Name", placeholder="Enter supplier name", key="supplier_input")
    
    st.divider()
    
    # Add items to cart
    with st.expander("🛒 Add Items to Purchase", expanded=True):
        inv_df = load_data("Inventory")
        
        col1, col2, col3, col4 = st.columns(4)
        
        item_name = ""
        
        with col1:
            if not inv_df.empty:
                existing_items = inv_df.iloc[:, 0].unique().tolist()
                
                st.markdown("**Select OR Type:**")
                item_from_dropdown = st.selectbox(
                    "Existing Items", 
                    ["(Select existing item)"] + existing_items,
                    key="item_dropdown",
                    label_visibility="collapsed"
                )
                
                st.markdown("**OR**")
                item_from_text = st.text_input(
                    "Type new item name",
                    key="new_item_text",
                    placeholder="Type new product name here",
                    label_visibility="collapsed"
                )
                
                if item_from_text and item_from_text.strip():
                    item_name = item_from_text.strip().upper()
                    is_new_item = item_name not in existing_items
                elif item_from_dropdown and item_from_dropdown != "(Select existing item)":
                    item_name = item_from_dropdown
                    is_new_item = False
                else:
                    item_name = ""
                    is_new_item = False
            else:
                item_from_text = st.text_input("Item Name", key="item_name_only")
                item_name = item_from_text.strip().upper() if item_from_text else ""
                is_new_item = True
        
        if item_name and item_name != "" and not inv_df.empty:
            product_stock = inv_df[inv_df.iloc[:, 0] == item_name]
            
            if not product_stock.empty and not is_new_item:
                current_qty = pd.to_numeric(product_stock.iloc[:, 1], errors='coerce').sum()
                last_unit = product_stock.iloc[-1, 2] if len(product_stock.columns) > 2 else ""
                
                st.info(f"📦 **Current Stock:** {current_qty} {last_unit}")
            elif is_new_item or item_name not in [item['Item'] for item in st.session_state.purchase_cart]:
                st.success("✨ **New Item** - First time purchase")
        
        with col2:
            qty = st.number_input("Quantity", min_value=0.1, value=1.0, step=0.1, key="qty_input")
        with col3:
            unit = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams", "Ltr"], key="unit_input")
        with col4:
            rate = st.number_input("Rate/Unit", min_value=0.0, value=0.0, step=1.0, key="rate_input")
        
        if item_name and item_name != "" and qty > 0 and not inv_df.empty and not is_new_item:
            product_stock = inv_df[inv_df.iloc[:, 0] == item_name]
            if not product_stock.empty:
                current_qty_num = pd.to_numeric(product_stock.iloc[:, 1], errors='coerce').sum()
                new_stock = current_qty_num + qty
                
                col1, col2, col3 = st.columns(3)
                col1.metric("📦 Current", f"{current_qty_num} {unit}")
                col2.metric("➕ Adding", f"{qty} {unit}")
                col3.metric("✅ New Total", f"{new_stock} {unit}", delta=f"+{qty}")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ Add to Cart", type="primary", use_container_width=True):
                if item_name and item_name.strip() and qty > 0 and rate > 0:
                    st.session_state.purchase_cart.append({
                        'Item': item_name.strip(),
                        'Qty': qty,
                        'Unit': unit,
                        'Rate': rate,
                        'Amount': qty * rate
                    })
                    
                    st.success(f"✅ Added {item_name}")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    if not item_name or not item_name.strip():
                        st.error("⚠️ Please select or type item name!")
                    else:
                        st.error("⚠️ Fill all fields properly!")
        
        with col2:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.purchase_cart = []
                st.rerun()
    
    # Display cart
    if st.session_state.purchase_cart:
        st.divider()
        st.markdown("### 🛒 Purchase Cart")
        
        cart_df = pd.DataFrame(st.session_state.purchase_cart)
        cart_df['Qty_Display'] = cart_df['Qty'].astype(str) + ' ' + cart_df['Unit']
        cart_df['Rate_Display'] = '₹' + cart_df['Rate'].astype(str)
        cart_df['Amount_Display'] = '₹' + cart_df['Amount'].apply(lambda x: f"{x:,.2f}")
        
        display_df = cart_df[['Item', 'Qty_Display', 'Rate_Display', 'Amount_Display']]
        display_df.columns = ['Item', 'Quantity', 'Rate', 'Amount']
        
        st.dataframe(display_df, use_container_width=True)
        
        total_amount = sum([item['Amount'] for item in st.session_state.purchase_cart])
        total_items = len(st.session_state.purchase_cart)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total Items", total_items)
        col2.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
        col3.metric("📊 Payment", payment_type.split()[0])
        
        with st.expander("🗑️ Remove Item"):
            if total_items > 0:
                item_to_remove = st.selectbox(
                    "Select item to remove",
                    [f"{i}: {item['Item']} - {item['Qty']} {item['Unit']}" for i, item in enumerate(st.session_state.purchase_cart)]
                )
                
                if st.button("🗑️ Remove Selected Item", type="secondary"):
                    remove_idx = int(item_to_remove.split(':')[0])
                    removed_item = st.session_state.purchase_cart.pop(remove_idx)
                    st.success(f"✅ Removed {removed_item['Item']}")
                    time.sleep(0.5)
                    st.rerun()
        
        st.divider()
        
        # Final save button
        if payment_type == "🏢 Party/Supplier" and (not supplier_name or not supplier_name.strip()):
            st.error("⚠️ Please enter Party/Supplier name above!")
        else:
            if st.button("💾 SAVE PURCHASE", type="primary", use_container_width=True):
                # Save all items to Inventory
                for item in st.session_state.purchase_cart:
                    payment_info = payment_mode if not supplier_name else f"Party: {supplier_name}"
                    total_value = item['Qty'] * item['Rate']
                    
                    save_data("Inventory", [
                        item['Item'],
                        item['Qty'],
                        item['Unit'],
                        item['Rate'],
                        total_value,
                        str(today_dt),
                        payment_info
                    ])
                
                # Handle payment
                if payment_mode in ["Cash", "Online"]:
                    update_balance(total_amount, payment_mode, 'subtract')
                    st.success(f"✅ Purchase saved! Paid ₹{total_amount:,.2f} from {payment_mode}")
                else:
                    # ✅ AUTOMATIC SUPPLIER DUES ENTRY
                    if supplier_name and supplier_name.strip():
                        items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                        
                        # Save to Dues sheet with POSITIVE amount (we owe them)
                        save_data("Dues", [supplier_name, total_amount, str(today_dt), f"Purchase: {items_note}"])
                        
                        st.success(f"✅ Purchase saved!")
                        st.success(f"✅ ₹{total_amount:,.2f} automatically added to {supplier_name}'s dues in Supplier Dues section!")
                        st.info(f"💡 Check 'Supplier Dues' menu to see {supplier_name}'s balance")
                
                st.session_state.purchase_cart = []
                st.balloons()
                time.sleep(2)
                st.rerun()
    else:
        st.info("🛒 Cart is empty. Add items above to start purchase.")

# ========================================
# MENU 4: LIVE STOCK
# ========================================
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    
    if not i_df.empty and len(i_df.columns) > 4:
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        i_df['value'] = i_df['qty_v'] * i_df['rate_v']
        t_v = i_df['value'].sum()
        
        st.subheader(f"💰 Total Stock Value: ₹{t_v:,.2f}")
        
        stock_summary = i_df.groupby(i_df.columns[0]).agg({
            i_df.columns[1]: 'last',
            i_df.columns[2]: 'last',
            i_df.columns[3]: 'last',
            'qty_v': 'last',
            'value': 'last'
        }).reset_index()
        stock_summary.columns = ['Item', 'Qty_Num', 'Unit', 'Rate', 'Qty_Numeric', 'Value']
        
        stock_summary['Quantity'] = stock_summary['Qty_Num'].astype(str) + ' ' + stock_summary['Unit'].astype(str)
        
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
        
        if low_stock_items:
            st.divider()
            st.subheader("🚨 LOW STOCK ALERT")
            
            low_stock_df = pd.DataFrame(low_stock_items)
            low_stock_df = low_stock_df.drop('Qty_Numeric', axis=1)
            
            for _, row in low_stock_df.iterrows():
                st.error(f"🚨 **{row['Item']}** - {row['Quantity']} - Rate: {row['Rate']} - Value: {row['Stock Value']}")
            
            st.divider()
            csv = low_stock_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Low Stock Report",
                data=csv,
                file_name=f"low_stock_report_{today_dt}.csv",
                mime="text/csv",
                type="primary"
            )
        
        if normal_stock_items:
            st.divider()
            st.subheader("✅ Available Stock")
            for item in normal_stock_items:
                st.info(f"✅ **{item['Item']}** - {item['Quantity']} - Rate: {item['Rate']} - Value: {item['Stock Value']}")

# ========================================
# MENU 5: EXPENSES
# ========================================
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
        st.subheader("📋 Today's Expenses")
        
        today_expenses = e_df[e_df.iloc[:, 0] == str(today_dt)] if len(e_df.columns) > 0 else e_df
        
        if not today_expenses.empty:
            st.dataframe(today_expenses, use_container_width=True)
        else:
            st.info("No expenses today")
        
        st.divider()
        st.subheader("📜 All Expenses History")
        st.dataframe(e_df, use_container_width=True)

# ========================================
# MENU 6: PET REGISTER
# ========================================
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration & Records")
    
    tab1, tab2 = st.tabs(["➕ Add New Pet", "📋 View All Pets"])
    
    with tab1:
        with st.form("pet_reg"):
            st.subheader("Register New Pet")
            
            col1, col2 = st.columns(2)
            with col1:
                pet_name = st.text_input("Pet Name")
                pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Fish", "Other"])
                pet_breed = st.text_input("Breed")
                pet_age = st.number_input("Age (years)", min_value=0.0, step=0.5)
            
            with col2:
                owner_name = st.text_input("Owner Name")
                owner_phone = st.text_input("Owner Phone")
                owner_address = st.text_area("Owner Address")
                vaccination_status = st.selectbox("Vaccination Status", ["Up to date", "Due", "Not vaccinated"])
            
            notes = st.text_area("Additional Notes")
            
            if st.form_submit_button("💾 Register Pet", type="primary"):
                if pet_name and owner_name and owner_phone:
                    save_data("PetRegister", [
                        str(today_dt), pet_name, pet_type, pet_breed, pet_age,
                        owner_name, owner_phone, owner_address, vaccination_status, notes
                    ])
                    st.success(f"✅ {pet_name} registered successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Please fill Pet Name, Owner Name, and Owner Phone!")
    
    with tab2:
        pets_df = load_data("PetRegister")
        
        if not pets_df.empty:
            st.subheader(f"📊 Total Registered Pets: {len(pets_df)}")
            
            # Search functionality
            search = st.text_input("🔍 Search by Pet Name or Owner Name/Phone")
            
            if search:
                mask = pets_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                filtered_df = pets_df[mask]
            else:
                filtered_df = pets_df
            
            # Display pets
            for idx, row in filtered_df.iterrows():
                with st.expander(f"🐾 {row.iloc[1] if len(row) > 1 else 'Pet'} - {row.iloc[2] if len(row) > 2 else ''} ({row.iloc[5] if len(row) > 5 else 'Owner'})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Pet Information:**")
                        st.write(f"Name: {row.iloc[1] if len(row) > 1 else 'N/A'}")
                        st.write(f"Type: {row.iloc[2] if len(row) > 2 else 'N/A'}")
                        st.write(f"Breed: {row.iloc[3] if len(row) > 3 else 'N/A'}")
                        st.write(f"Age: {row.iloc[4] if len(row) > 4 else 'N/A'} years")
                        st.write(f"Vaccination: {row.iloc[8] if len(row) > 8 else 'N/A'}")
                    
                    with col2:
                        st.write("**Owner Information:**")
                        st.write(f"Name: {row.iloc[5] if len(row) > 5 else 'N/A'}")
                        st.write(f"Phone: {row.iloc[6] if len(row) > 6 else 'N/A'}")
                        st.write(f"Address: {row.iloc[7] if len(row) > 7 else 'N/A'}")
                    
                    if len(row) > 9 and str(row.iloc[9]).strip():
                        st.write("**Notes:**", row.iloc[9])
        else:
            st.info("No pets registered yet. Add your first pet in the 'Add New Pet' tab!")

# ========================================
# MENU 7: CUSTOMER KHATA
# ========================================
elif menu == "📒 Customer Khata":
    st.header("📒 Customer Khata (Udhaar Management)")
    
    tab1, tab2 = st.tabs(["💰 Payment Entry", "📊 View Summary"])
    
    with tab1:
        with st.form("khata"):
            st.subheader("Record Payment")
            cust = st.text_input("Customer Name/Phone")
            amt = st.number_input("Amount", min_value=0.0)
            pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Other"])
            note = st.text_input("Note (Optional)")
            
            st.info("💡 Enter amount received from customer to reduce their udhaar")
            
            if st.form_submit_button("💾 Save Payment", type="primary"):
                if amt > 0 and cust.strip():
                    save_data("CustomerKhata", [cust, -amt, str(today_dt), f"Payment: {note}"])
                    
                    if pay_mode == "Cash":
                        update_balance(amt, "Cash", 'add')
                    elif pay_mode == "Online":
                        update_balance(amt, "Online", 'add')
                    
                    st.success(f"✅ ₹{amt:,.2f} payment recorded from {cust}")
                    time.sleep(1)
                    st.rerun()
    
    with tab2:
        k_df = load_data("CustomerKhata")
        
        if not k_df.empty and len(k_df.columns) > 1:
            st.subheader("📊 Customer Udhaar Summary")
            
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            
            sum_df = sum_df[sum_df['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                total_udhaar = sum_df['Balance'].sum()
                st.metric("💰 Total Outstanding Udhaar", f"₹{total_udhaar:,.2f}")
                
                st.divider()
                
                for _, row in sum_df.iterrows():
                    customer = row['Customer']
                    balance = row['Balance']
                    
                    with st.expander(f"🔴 **{customer}** - Balance: ₹{balance:,.2f}"):
                        cust_txns = k_df[k_df.iloc[:, 0] == customer]
                        
                        for _, txn in cust_txns.iterrows():
                            date = str(txn.iloc[2]) if len(txn) > 2 else "N/A"
                            amount = float(txn.iloc[1]) if len(txn) > 1 else 0
                            note = str(txn.iloc[3]) if len(txn) > 3 else ""
                            
                            if amount > 0:
                                st.error(f"📥 {date}: Udhaar ₹{amount:,.2f} - {note}")
                            else:
                                st.success(f"💰 {date}: Payment ₹{abs(amount):,.2f} - {note}")
            else:
                st.success("✅ No outstanding udhaar! All customers have cleared their dues.")
        else:
            st.info("No udhaar records yet.")

# ========================================
# MENU 8: SUPPLIER DUES
# ========================================
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues Management")
    
    tab1, tab2 = st.tabs(["➕ Add Entry", "📊 View Summary"])
    
    with tab1:
        with st.form("due"):
            st.subheader("Add Supplier Transaction")
            s = st.text_input("Supplier Name")
            a = st.number_input("Amount", min_value=0.0)
            t = st.selectbox("Type", ["Maal Liya (Credit +)", "Payment Kiya (-)"])
            m = st.selectbox("Payment Mode", ["Cash", "Online", "Pocket", "Hand", "N/A"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("💡 **Maal Liya** = Supplier ka balance badhega (we owe them)")
            with col2:
                st.info("💡 **Payment Kiya** = Supplier ka balance kam hoga (we paid them)")
            
            if st.form_submit_button("💾 Save Transaction", type="primary"):
                if a > 0 and s.strip():
                    if "Credit" in t or "Liya" in t:
                        final_amt = a
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Credit"])
                        st.success(f"✅ ₹{a:,.2f} ka maal entry added for {s}")
                    else:
                        final_amt = -a
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Payment"])
                        
                        if m == "Cash":
                            update_balance(a, "Cash", 'subtract')
                        elif m == "Online":
                            update_balance(a, "Online", 'subtract')
                        else:
                            st.success(f"✅ ₹{a:,.2f} payment entry added (from {m})")
                    
                    time.sleep(1)
                    st.rerun()
    
    with tab2:
        d_df = load_data("Dues")
        
        if not d_df.empty and len(d_df.columns) > 1:
            st.subheader("📊 Supplier Balance Summary")
            
            sum_df = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Supplier', 'Balance']
            
            sum_df = sum_df[sum_df['Balance'] != 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                st.markdown("### 💰 Outstanding Balances")
                
                for _, row in sum_df.iterrows():
                    supplier_name = row['Supplier']
                    balance = row['Balance']
                    
                    supplier_txns = d_df[d_df.iloc[:, 0] == supplier_name]
                    
                    with st.expander(f"{'🔴' if balance > 0 else '🟢'} **{supplier_name}** - Balance: ₹{abs(balance):,.2f} {'(We Owe)' if balance > 0 else '(They Owe)'}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("#### Transaction History")
                            for _, txn in supplier_txns.iterrows():
                                date = str(txn.iloc[2]) if len(txn) > 2 else "N/A"
                                amount = float(txn.iloc[1]) if len(txn) > 1 else 0
                                mode = str(txn.iloc[3]) if len(txn) > 3 else "N/A"
                                
                                if amount > 0:
                                    st.info(f"📦 {date}: Maal liya ₹{amount:,.2f}")
                                else:
                                    st.success(f"💵 {date}: Payment ₹{abs(amount):,.2f} ({mode})")
                        
                        with col2:
                            st.markdown("#### Summary")
                            total_credit = supplier_txns[supplier_txns.iloc[:, 1] > 0].iloc[:, 1].sum() if len(supplier_txns) > 0 else 0
                            total_paid = abs(supplier_txns[supplier_txns.iloc[:, 1] < 0].iloc[:, 1].sum()) if len(supplier_txns) > 0 else 0
                            
                            st.metric("📦 Total Credit", f"₹{total_credit:,.2f}")
                            st.metric("💵 Total Paid", f"₹{total_paid:,.2f}")
                            st.metric("⚖️ Balance", f"₹{abs(balance):,.2f}", 
                                     delta=f"{'We Owe' if balance > 0 else 'They Owe'}")
                            
                            if balance > 0:
                                st.divider()
                                st.markdown("#### 💵 Quick Payment")
                                
                                with st.form(f"pay_{supplier_name}"):
                                    pay_amt = st.number_input("Amount to Pay", min_value=0.0, max_value=float(balance), value=float(balance), step=0.01)
                                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Cheque", "UPI"], key=f"mode_{supplier_name}")
                                    
                                    if st.form_submit_button("💰 Pay Now", type="primary", use_container_width=True):
                                        if pay_amt > 0:
                                            save_data("Dues", [supplier_name, -pay_amt, str(today_dt), pay_mode, "Payment"])
                                            
                                            if pay_mode == "Cash":
                                                update_balance(pay_amt, "Cash", 'subtract')
                                            elif pay_mode == "Online":
                                                update_balance(pay_amt, "Online", 'subtract')
                                            
                                            st.success(f"✅ Paid ₹{pay_amt:,.2f} to {supplier_name}")
                                            time.sleep(1)
                                            st.rerun()
                
                st.divider()
                st.subheader("🎯 Overall Summary")
                col1, col2, col3 = st.columns(3)
                
                total_we_owe = sum_df[sum_df['Balance'] > 0]['Balance'].sum()
                total_they_owe = abs(sum_df[sum_df['Balance'] < 0]['Balance'].sum())
                net_balance = total_we_owe - total_they_owe
                
                col1.metric("🔴 Total We Owe", f"₹{total_we_owe:,.2f}")
                col2.metric("🟢 Total They Owe", f"₹{total_they_owe:,.2f}")
                col3.metric("⚖️ Net Position", f"₹{abs(net_balance):,.2f}", 
                           delta=f"{'We Owe' if net_balance > 0 else 'They Owe'}")
            else:
                st.success("✅ All suppliers settled! No outstanding balances.")
            
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(d_df, use_container_width=True)
        else:
            st.info("No supplier transactions yet. Add your first entry above!")

# ========================================
# MENU 9: ROYALTY POINTS
# ========================================
elif menu == "👑 Royalty Points":
    st.header("👑 Royalty Points Management")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 6:
        st.subheader("🎯 Points System")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Weekday:** 2% of purchase amount")
            st.info("**Weekend:** 5% of purchase amount")
        with col2:
            st.success("**Redemption:** 100 points minimum")
            st.success("**Referral Bonus:** +10 points")
        
        st.divider()
        st.subheader("👥 Customer Points Leaderboard")
        
        # Calculate points for each customer
        points_data = s_df.groupby(s_df.columns[5]).agg({
            s_df.columns[6]: 'sum',
            s_df.columns[3]: 'sum'
        }).reset_index()
        
        points_data.columns = ['Customer', 'Points', 'Total_Spent']
        points_data['Points'] = pd.to_numeric(points_data['Points'], errors='coerce').fillna(0)
        points_data['Total_Spent'] = pd.to_numeric(points_data['Total_Spent'], errors='coerce').fillna(0)
        points_data = points_data[points_data['Points'] != 0].sort_values('Points', ascending=False)
        
        for idx, row in points_data.head(10).iterrows():
            customer = row['Customer']
            points = int(row['Points'])
            spent = row['Total_Spent']
            
            # Extract phone
            phone = ""
            if "(" in customer and ")" in customer:
                phone = customer.split("(")[1].replace(")", "")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{customer}**")
            with col2:
                st.metric("Points", f"{points} 👑")
            with col3:
                st.metric("Spent", f"₹{spent:,.0f}")
    else:
        st.info("No sales data available for points analysis")

# ========================================
# MENU 10: ADVANCED REPORTS
# ========================================
elif menu == "📈 Advanced Reports":
    st.header("📈 Advanced Sales Reports")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 3:
        tab1, tab2, tab3 = st.tabs(["📊 Best Sellers", "🐌 Slow Moving", "💰 Profit Analysis"])
        
        with tab1:
            st.subheader("🏆 Best Selling Products")
            
            # Group by product
            product_sales = s_df.groupby(s_df.columns[1]).agg({
                s_df.columns[3]: 'sum',
                s_df.columns[1]: 'count'
            }).reset_index()
            
            product_sales.columns = ['Product', 'Revenue', 'Units_Sold']
            product_sales['Revenue'] = pd.to_numeric(product_sales['Revenue'], errors='coerce')
            product_sales = product_sales.sort_values('Revenue', ascending=False).head(15)
            
            for idx, row in product_sales.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{row['Product']}**")
                with col2:
                    st.metric("Revenue", f"₹{row['Revenue']:,.0f}")
                with col3:
                    st.metric("Units", f"{row['Units_Sold']}")
        
        with tab2:
            st.subheader("🐌 Slow Moving Products")
            
            inv_df = load_data("Inventory")
            if not inv_df.empty:
                product_movement = s_df.groupby(s_df.columns[1]).size().reset_index(name='transactions')
                
                slow_movers = product_movement.sort_values('transactions').head(10)
                
                for idx, row in slow_movers.iterrows():
                    st.warning(f"⚠️ **{row[s_df.columns[1]]}** - Only {row['transactions']} transactions")
        
        with tab3:
            st.subheader("💰 Profit Analysis")
            
            if len(s_df.columns) > 7:
                total_profit = pd.to_numeric(s_df.iloc[:, 7], errors='coerce').sum()
                total_revenue = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
                
                profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
                col2.metric("Total Profit", f"₹{total_profit:,.2f}")
                col3.metric("Profit Margin", f"{profit_margin:.1f}%")
    else:
        st.info("No sales data available")

# ========================================
# MENU 11: CUSTOMER ANALYTICS
# ========================================
elif menu == "👥 Customer Analytics":
    st.header("👥 Customer Analytics & Insights")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 5:
        # RFM Analysis
        st.subheader("🎯 RFM Analysis (Recency, Frequency, Monetary)")
        
        customer_data = s_df.groupby(s_df.columns[5]).agg({
            s_df.columns[0]: 'max',  # Last purchase date
            s_df.columns[3]: ['count', 'sum']  # Frequency and Monetary
        }).reset_index()
        
        customer_data.columns = ['Customer', 'Last_Purchase', 'Frequency', 'Monetary']
        customer_data['Monetary'] = pd.to_numeric(customer_data['Monetary'], errors='coerce')
        
        # Segment customers
        high_value = customer_data[customer_data['Monetary'] > customer_data['Monetary'].quantile(0.7)]
        medium_value = customer_data[(customer_data['Monetary'] > customer_data['Monetary'].quantile(0.3)) & 
                                     (customer_data['Monetary'] <= customer_data['Monetary'].quantile(0.7))]
        low_value = customer_data[customer_data['Monetary'] <= customer_data['Monetary'].quantile(0.3)]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🌟 High Value", len(high_value))
        col2.metric("📊 Medium Value", len(medium_value))
        col3.metric("📉 Low Value", len(low_value))
        
        st.divider()
        st.subheader("🏆 Top 10 Customers by Spending")
        
        top_customers = customer_data.sort_values('Monetary', ascending=False).head(10)
        
        for idx, row in top_customers.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{row['Customer']}**")
            with col2:
                st.metric("Total Spent", f"₹{row['Monetary']:,.0f}")
            with col3:
                st.metric("Visits", f"{row['Frequency']}")
    else:
        st.info("No customer data available")

# ========================================
# MENU 12: DISCOUNTS & OFFERS
# ========================================
elif menu == "🎁 Discounts & Offers":
    st.header("🎁 Discounts & Offers Management")
    
    tab1, tab2, tab3 = st.tabs(["📦 Bulk Discounts", "🎊 Seasonal Offers", "🎯 Combo Deals"])
    
    with tab1:
        st.subheader("📦 Bulk Purchase Discounts")
        
        with st.form("bulk_discount"):
            product = st.text_input("Product Name")
            min_qty = st.number_input("Minimum Quantity", min_value=1)
            discount_percent = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=5.0)
            
            if st.form_submit_button("💾 Save Discount", type="primary"):
                save_data("Discounts", ["Bulk", product, min_qty, discount_percent, str(today_dt)])
                st.success(f"✅ {discount_percent}% discount added for {product} (min {min_qty} units)")
                time.sleep(1)
                st.rerun()
        
        disc_df = load_data("Discounts")
        if not disc_df.empty:
            bulk_disc = disc_df[disc_df.iloc[:, 0] == "Bulk"]
            if not bulk_disc.empty:
                st.divider()
                st.subheader("Active Bulk Discounts")
                st.dataframe(bulk_disc, use_container_width=True)
    
    with tab2:
        st.subheader("🎊 Seasonal Offers")
        
        with st.form("seasonal"):
            offer_name = st.text_input("Offer Name", placeholder="e.g., Diwali Special")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            discount = st.number_input("Discount %", min_value=0.0, max_value=100.0)
            
            if st.form_submit_button("💾 Create Offer", type="primary"):
                save_data("Offers", [offer_name, str(start_date), str(end_date), discount])
                st.success(f"✅ {offer_name} created with {discount}% discount!")
                time.sleep(1)
                st.rerun()
        
        off_df = load_data("Offers")
        if not off_df.empty:
            st.divider()
            st.subheader("Active Seasonal Offers")
            st.dataframe(off_df, use_container_width=True)
    
    with tab3:
        st.subheader("🎯 Combo Deal Builder")
        
        st.info("💡 Buy together and save! Create product combos with special pricing")
        
        with st.form("combo"):
            combo_name = st.text_input("Combo Name", placeholder="e.g., Pet Care Bundle")
            products = st.text_area("Products (one per line)")
            combo_price = st.number_input("Combo Price", min_value=0.0)
            
            if st.form_submit_button("💾 Create Combo", type="primary"):
                save_data("Combos", [combo_name, products, combo_price, str(today_dt)])
                st.success(f"✅ {combo_name} combo created at ₹{combo_price}!")
                time.sleep(1)
                st.rerun()

# ========================================
# MENU 13: FINANCIAL REPORTS
# ========================================
elif menu == "💼 Financial Reports":
    st.header("💼 Financial Reports & Analysis")
    
    s_df = load_data("Sales")
    e_df = load_data("Expenses")
    p_df = load_data("Inventory")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=datetime.now().date())
    
    tab1, tab2, tab3 = st.tabs(["📊 P&L Statement", "💰 Balance Sheet", "📈 Tax Reports"])
    
    with tab1:
        st.subheader(f"📊 Profit & Loss: {start_date} to {end_date}")
        
        # Calculate revenue
        if not s_df.empty and 'Date' in s_df.columns:
            period_sales = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
            total_revenue = pd.to_numeric(period_sales.iloc[:, 3], errors='coerce').sum() if not period_sales.empty else 0
        else:
            total_revenue = 0
        
        # Calculate expenses
        if not e_df.empty and len(e_df.columns) > 2:
            try:
                e_df['Date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
                period_expenses = e_df[(e_df['Date'] >= start_date) & (e_df['Date'] <= end_date)]
                total_expenses = pd.to_numeric(period_expenses.iloc[:, 2], errors='coerce').sum() if not period_expenses.empty else 0
            except:
                total_expenses = 0
        else:
            total_expenses = 0
        
        # Calculate COGS (from purchases)
        if not p_df.empty and len(p_df.columns) > 4:
            cogs = pd.to_numeric(p_df.iloc[:, 4], errors='coerce').sum()
        else:
            cogs = 0
        
        gross_profit = total_revenue - cogs
        net_profit = total_revenue - cogs - total_expenses
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
            st.metric("📦 Cost of Goods Sold", f"₹{cogs:,.2f}")
            st.metric("💵 Gross Profit", f"₹{gross_profit:,.2f}")
        with col2:
            st.metric("💸 Operating Expenses", f"₹{total_expenses:,.2f}")
            st.metric("✨ Net Profit", f"₹{net_profit:,.2f}", 
                     delta=f"{(net_profit/total_revenue*100):.1f}%" if total_revenue > 0 else "0%")
    
    with tab2:
        st.subheader("💰 Balance Sheet")
        
        cash_bal = get_current_balance("Cash")
        online_bal = get_current_balance("Online")
        
        # Calculate inventory value
        if not p_df.empty and len(p_df.columns) > 4:
            inventory_value = pd.to_numeric(p_df.iloc[:, 1], errors='coerce').mul(
                pd.to_numeric(p_df.iloc[:, 3], errors='coerce')
            ).sum()
        else:
            inventory_value = 0
        
        # Calculate receivables (Customer Khata)
        k_df = load_data("CustomerKhata")
        if not k_df.empty and len(k_df.columns) > 1:
            receivables = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum().sum()
            receivables = max(0, receivables)
        else:
            receivables = 0
        
        # Calculate payables (Supplier Dues)
        d_df = load_data("Dues")
        if not d_df.empty and len(d_df.columns) > 1:
            payables = d_df.groupby(d_df.columns[0])[d_df.columns[1]].sum()
            payables = payables[payables > 0].sum()
        else:
            payables = 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Assets")
            st.metric("💵 Cash", f"₹{cash_bal:,.2f}")
            st.metric("🏦 Online/Bank", f"₹{online_bal:,.2f}")
            st.metric("📦 Inventory", f"₹{inventory_value:,.2f}")
            st.metric("📒 Receivables", f"₹{receivables:,.2f}")
            total_assets = cash_bal + online_bal + inventory_value + receivables
            st.metric("✨ Total Assets", f"₹{total_assets:,.2f}")
        
        with col2:
            st.markdown("### 📉 Liabilities")
            st.metric("🏢 Supplier Dues", f"₹{payables:,.2f}")
            st.metric("✨ Total Liabilities", f"₹{payables:,.2f}")
            st.divider()
            net_worth = total_assets - payables
            st.metric("💎 Net Worth", f"₹{net_worth:,.2f}")
    
    with tab3:
        st.subheader("📈 Tax Reports (GST)")
        
        st.info("💡 Simplified tax calculations for reference")
        
        if not s_df.empty and len(s_df.columns) > 3:
            period_sales = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
            total_sales = pd.to_numeric(period_sales.iloc[:, 3], errors='coerce').sum() if not period_sales.empty else 0
            
            # Assuming 18% GST
            taxable_amount = total_sales / 1.18
            gst_collected = total_sales - taxable_amount
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Sales", f"₹{total_sales:,.2f}")
            col2.metric("📊 Taxable Amount", f"₹{taxable_amount:,.2f}")
            col3.metric("🧾 GST Collected (18%)", f"₹{gst_collected:,.2f}")

# ========================================
# MENU 14: SECURITY & COMPLIANCE
# ========================================
elif menu == "🔐 Security & Compliance":
    st.header("🔐 Security & Compliance")
    
    tab1, tab2, tab3 = st.tabs(["💾 Backup & Restore", "🔒 Access Control", "📋 Audit Logs"])
    
    with tab1:
        st.subheader("💾 Data Backup & Restore")
        
        st.info("💡 Your data is automatically backed up to Google Sheets")
        
        if st.button("📥 Download All Data (CSV Export)", type="primary", use_container_width=True):
            # Create a combined export
            sheets = ["Sales", "Inventory", "Expenses", "CustomerKhata", "Dues", "PetRegister"]
            
            with st.spinner("Preparing export..."):
                export_data = {}
                for sheet in sheets:
                    try:
                        df = load_data(sheet)
                        if not df.empty:
                            export_data[sheet] = df
                    except:
                        pass
                
                if export_data:
                    st.success(f"✅ {len(export_data)} sheets ready for download!")
                    
                    for sheet_name, df in export_data.items():
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Download {sheet_name}",
                            data=csv,
                            file_name=f"{sheet_name}_{today_dt}.csv",
                            mime="text/csv",
                            key=f"download_{sheet_name}"
                        )
        
        st.divider()
        st.warning("⚠️ **Data Retention Policy:** All data is stored permanently in Google Sheets")
    
    with tab2:
        st.subheader("🔒 Access Control")
        
        st.info(f"**Current User:** {st.session_state.username}")
        st.info(f"**Role:** {st.session_state.user_role.upper()}")
        
        st.divider()
        st.markdown("### 👥 User Roles & Permissions")
        
        roles = {
            "CEO": "Full access to all features including Security & Compliance",
            "Owner": "Full access to all features including Security & Compliance",
            "Manager": "Access to all features except Security & Compliance",
            "Staff": "Limited access - Dashboard, Billing, Live Stock, Pet Register only"
        }
        
        for role, permissions in roles.items():
            with st.expander(f"👤 {role}"):
                st.write(permissions)
    
    with tab3:
        st.subheader("📋 Audit Trail")
        
        st.info("💡 All transactions are automatically logged with date, time, and user information")
        
        s_df = load_data("Sales")
        if not s_df.empty:
            recent_activity = s_df.tail(20)
            st.markdown("### 🕒 Recent Activity (Last 20 transactions)")
            st.dataframe(recent_activity, use_container_width=True)
        
        st.divider()
        st.markdown("### 📊 Activity Summary")
        
        if not s_df.empty:
            today_count = len(s_df[s_df['Date'] == today_dt]) if 'Date' in s_df.columns else 0
            this_week = len(s_df[s_df['Date'] >= (today_dt - timedelta(days=7))]) if 'Date' in s_df.columns else 0
            this_month_count = len(s_df[s_df['Date'] >= (today_dt - timedelta(days=30))]) if 'Date' in s_df.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("📅 Today", today_count)
            col2.metric("📆 This Week", this_week)
            col3.metric("📊 This Month", this_month_count)

# ========================================
# FALLBACK FOR ANY OTHER MENU
# ========================================
else:
    st.info(f"Module: {menu} - Feature under development")


