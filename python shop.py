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

def update_stock_in_sheet(item_name, new_qty):
    """Update stock directly in Google Sheets"""
    try:
        item_name = str(item_name).strip().upper()
        
        payload = {
            "action": "update_stock",
            "sheet": "Inventory",
            "item_name": item_name,
            "new_qty": float(new_qty)
        }
        
        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
        response_text = response.text.strip()
        
        if "Stock Updated" in response_text:
            return True
        else:
            st.warning(f"Update response: {response_text}")
            return False
            
    except Exception as e:
        st.error(f"Stock update error: {str(e)}")
        return False

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

# --- 4. SIDEBAR MENU ---
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

# Define menu structure based on role
if user_role in ["ceo", "owner"]:
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📦 Purchase", 
        "📋 Live Stock", 
        "💰 Expenses",
        "🐾 Pet Register",
        "📒 Customer Due",
        "🏢 Supplier Dues",
        "👑 Royalty Points",
        "📈 Advanced Reports"
    ]
elif user_role == "manager":
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📦 Purchase", 
        "📋 Live Stock", 
        "💰 Expenses",
        "🐾 Pet Register",
        "📒 Customer Due",
        "🏢 Supplier Dues",
        "👑 Royalty Points",
        "📈 Advanced Reports"
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
    
    # Customer Due Calculation
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        customer_due = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum()
        total_customer_due = customer_due[customer_due > 0].sum()
    else:
        total_customer_due = 0
    
    # Stock Value Calculation
    inv_df = load_data("Inventory")
    if not inv_df.empty and len(inv_df.columns) > 3:
        inv_df['qty_val'] = pd.to_numeric(inv_df.iloc[:, 1], errors='coerce').fillna(0)
        inv_df['rate_val'] = pd.to_numeric(inv_df.iloc[:, 3], errors='coerce').fillna(0)
        inv_df['total_val'] = inv_df['qty_val'] * inv_df['rate_val']
        total_stock_value = inv_df['total_val'].sum()
    else:
        total_stock_value = 0
    
    # Hand Investment Calculation
    total_hand_investment = 0
    try:
        hand_df = load_data("HandInvestments")
        if not hand_df.empty and len(hand_df.columns) > 2:
            hand_amounts = pd.to_numeric(hand_df.iloc[:, 2], errors='coerce').fillna(0)
            total_hand_investment = hand_amounts.sum()
    except:
        total_hand_investment = 0
    
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
            <p style="margin: 0; font-size: 16px;">⚡ Total Shop</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_bal:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">👋 Hand Investment</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_hand_investment:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📒 Customer Due</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_customer_due:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">📦 Stock Value</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{total_stock_value:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔧 Balance Settings"):
        st.success("✅ Balance auto-loads from Google Sheets")
        
        tab1, tab2, tab3 = st.tabs(["💰 Cash & Online", "👋 Hand Investments", "📊 Summary"])
        
        with tab1:
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
        
        with tab2:
            st.subheader("👋 Hand Investments (Pocket Money)")
            st.metric("Total Personal Investment", f"₹{total_hand_investment:,.2f}")
            st.divider()
            
            try:
                hand_df = load_data("HandInvestments")
                if not hand_df.empty:
                    st.markdown("### 📋 Investment History")
                    st.dataframe(hand_df, use_container_width=True)
                    st.info("💡 Columns: Date | Supplier | Amount | Items | Note")
                else:
                    st.info("No hand investments yet.")
            except:
                st.info("No hand investments yet.")
        
        with tab3:
            st.subheader("📊 Total Business Capital")
            total_capital = cash_bal + online_bal + total_hand_investment
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Shop Cash", f"₹{cash_bal:,.2f}")
            col2.metric("Shop Online", f"₹{online_bal:,.2f}")
            col3.metric("Hand Investment", f"₹{total_hand_investment:,.2f}")
            col4.metric("Total Capital", f"₹{total_capital:,.2f}")
    
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
    today_purchase = 0
    
    if not p_df.empty and len(p_df.columns) > 6:
        try:
            p_df['pur_date'] = pd.to_datetime(p_df.iloc[:, 5], errors='coerce').dt.date
            p_today = p_df[
                (p_df['pur_date'] == today_dt) & 
                (p_df.iloc[:, 6].str.contains('Cash|Online|Hand|Udhaar|Supplier', case=False, na=False))
            ]
            if not p_today.empty:
                today_purchase = pd.to_numeric(p_today.iloc[:, 4], errors='coerce').sum()
        except:
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
    today_profit = today_sale - today_purchase - today_expense
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_sale:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">🛒 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_purchase:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📊 Net Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_profit:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========================================
# MENU 2: BILLING
# ========================================
elif menu == "🧾 Billing":
    st.header("🧾 Billing System")
    
    inv_df = load_data("Inventory")
    
    with st.expander("🛒 Add Items to Cart", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if not inv_df.empty:
                latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
                items_list = latest_stock.iloc[:, 0].unique().tolist()
                item = st.selectbox("Select Item", items_list, key="bill_item")
            else:
                st.error("⚠️ No items in inventory!")
                item = None
        
        if item and not inv_df.empty:
            product_stock = inv_df[inv_df.iloc[:, 0] == item].tail(1)
            
            if not product_stock.empty:
                available_qty = pd.to_numeric(product_stock.iloc[-1, 1], errors='coerce')
                last_unit = product_stock.iloc[-1, 2] if len(product_stock.columns) > 2 else "Pcs"
                last_rate = pd.to_numeric(product_stock.iloc[-1, 3], errors='coerce') if len(product_stock.columns) > 3 else 0
                
                st.info(f"📦 **Available Stock:** {available_qty} {last_unit}")
                
                with col2:
                    max_qty = max(float(available_qty), 0.1) if available_qty > 0 else 1000.0
                    default_qty = min(1.0, float(available_qty)) if available_qty > 0 else 1.0
                    qty = st.number_input("Quantity", min_value=0.1, max_value=max_qty, value=default_qty, step=0.1, key="bill_qty")
                
                with col3:
                    selected_unit = st.selectbox("Unit *", ["Kg", "Pcs", "Pkt", "Grams", "Ltr"], key="bill_unit")
                    st.caption(f"Last: {last_unit}")
                
                with col4:
                    rate = st.number_input("Rate/Unit", min_value=0.0, value=float(last_rate), step=1.0, key="bill_rate")
                
                with col5:
                    st.write("**Amount**")
                    st.success(f"₹{qty * rate:,.2f}")
                
                remaining = available_qty - qty
                if remaining < 2:
                    st.warning(f"⚠️ Low stock alert! Only {remaining} {last_unit} will remain after this sale")
                else:
                    st.success(f"✅ Stock after sale: {remaining} {last_unit}")
                
                if st.button("➕ Add to Cart", type="primary", use_container_width=True):
                    if qty > 0 and rate > 0:
                        if qty <= available_qty:
                            st.session_state.bill_cart.append({
                                'Item': item,
                                'Qty': qty,
                                'Unit': selected_unit,
                                'Rate': rate,
                                'Amount': qty * rate
                            })
                            st.success(f"✅ Added {item} ({qty} {selected_unit})")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"❌ Not enough stock!")
                    else:
                        st.error("⚠️ Enter valid quantity and rate!")
    
    if st.session_state.bill_cart:
        st.divider()
        st.markdown("### 🛒 Shopping Cart")
        
        cart_df = pd.DataFrame(st.session_state.bill_cart)
        cart_df['Qty_Display'] = cart_df['Qty'].astype(str) + ' ' + cart_df['Unit']
        cart_df['Rate_Display'] = '₹' + cart_df['Rate'].astype(str)
        cart_df['Amount_Display'] = '₹' + cart_df['Amount'].apply(lambda x: f"{x:,.2f}")
        
        display_df = cart_df[['Item', 'Qty_Display', 'Rate_Display', 'Amount_Display']]
        display_df.columns = ['Item', 'Quantity', 'Rate', 'Amount']
        
        st.dataframe(display_df, use_container_width=True)
        
        total = sum([i['Amount'] for i in st.session_state.bill_cart])
        
        with st.expander("🗑️ Remove Item"):
            if len(st.session_state.bill_cart) > 0:
                item_to_remove = st.selectbox(
                    "Select item to remove",
                    [f"{i}: {item['Item']} - {item['Qty']} {item['Unit']}" for i, item in enumerate(st.session_state.bill_cart)]
                )
                
                if st.button("🗑️ Remove Selected", type="secondary"):
                    remove_idx = int(item_to_remove.split(':')[0])
                    st.session_state.bill_cart.pop(remove_idx)
                    st.rerun()
        
        st.divider()
        st.markdown("### 👤 Customer Details")
        
        col1, col2 = st.columns(2)
        with col1:
            cust_name = st.text_input("Customer Name *", key="cust_name")
        with col2:
            cust_phone = st.text_input("Customer Phone", key="cust_phone")
        
        st.divider()
        st.markdown("### 💰 Payment Details")
        
        st.info(f"💵 **Total Bill Amount:** ₹{total:,.2f}")
        
        payment_split = st.radio(
            "Payment Type:",
            ["Single Payment Mode", "Multiple Payment Modes (Split Payment)"],
            horizontal=True,
            key="payment_split_type"
        )
        
        cash_amount = 0
        online_amount = 0
        udhaar_amount = 0
        
        if payment_split == "Single Payment Mode":
            st.markdown("#### 💳 Select Payment Mode")
            
            single_mode = st.selectbox(
                "Payment Mode",
                ["Cash", "Online", "Udhaar (Credit)"],
                key="single_pay_mode"
            )
            
            if single_mode == "Cash":
                cash_amount = total
                st.success(f"💵 **Cash Payment:** ₹{cash_amount:,.2f}")
            elif single_mode == "Online":
                online_amount = total
                st.success(f"🏦 **Online Payment:** ₹{online_amount:,.2f}")
            else:
                udhaar_amount = total
                st.warning(f"📒 **Credit (Udhaar):** ₹{udhaar_amount:,.2f}")
        
        else:
            st.markdown("#### 💳 Split Payment")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**💵 Cash**")
                cash_amount = st.number_input("Cash Amount", min_value=0.0, max_value=float(total), value=0.0, step=10.0, key="split_cash")
                if cash_amount > 0:
                    st.success(f"✅ Cash: ₹{cash_amount:,.2f}")
            
            with col2:
                st.markdown("**🏦 Online**")
                max_online = float(total - cash_amount)
                online_amount = st.number_input("Online Amount", min_value=0.0, max_value=max_online, value=0.0, step=10.0, key="split_online")
                if online_amount > 0:
                    st.success(f"✅ Online: ₹{online_amount:,.2f}")
            
            with col3:
                st.markdown("**📒 Udhaar**")
                max_udhaar = float(total - cash_amount - online_amount)
                udhaar_amount = st.number_input("Udhaar Amount", min_value=0.0, max_value=max_udhaar, value=max_udhaar, step=10.0, key="split_udhaar")
                if udhaar_amount > 0:
                    st.warning(f"⚠️ Udhaar: ₹{udhaar_amount:,.2f}")
            
            total_paid = cash_amount + online_amount + udhaar_amount
            remaining = total - total_paid
            
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Bill", f"₹{total:,.2f}")
            col2.metric("✅ Total Entered", f"₹{total_paid:,.2f}")
            
            if remaining > 0.01:
                col3.metric("⚠️ Remaining", f"₹{remaining:,.2f}", delta="Incomplete")
                st.error(f"❌ Payment incomplete!")
            elif remaining < -0.01:
                col3.metric("⚠️ Excess", f"₹{abs(remaining):,.2f}", delta="Too much")
                st.error(f"❌ Payment exceeds bill!")
            else:
                col3.metric("✅ Status", "Complete")
                st.success("✅ Payment matched!")
        
        st.divider()
        st.markdown("### 📊 Final Summary")
        
        payment_summary_cols = st.columns(4)
        payment_summary_cols[0].metric("💰 Bill", f"₹{total:,.2f}")
        payment_summary_cols[1].metric("💵 Cash", f"₹{cash_amount:,.2f}" if cash_amount > 0 else "₹0")
        payment_summary_cols[2].metric("🏦 Online", f"₹{online_amount:,.2f}" if online_amount > 0 else "₹0")
        payment_summary_cols[3].metric("📒 Udhaar", f"₹{udhaar_amount:,.2f}" if udhaar_amount > 0 else "₹0")
        
        can_save = True
        error_msg = ""
        
        if not cust_name.strip():
            can_save = False
            error_msg = "⚠️ Enter customer name!"
        
        if payment_split == "Multiple Payment Modes (Split Payment)":
            total_paid = cash_amount + online_amount + udhaar_amount
            if abs(total_paid - total) > 0.01:
                can_save = False
                error_msg = f"⚠️ Payment mismatch!"
        
        if not can_save:
            st.error(error_msg)
        
        if st.button("💾 COMPLETE SALE", type="primary", use_container_width=True, disabled=not can_save):
            customer_info = f"{cust_name} ({cust_phone})" if cust_phone else cust_name
            
            payment_modes_used = []
            if cash_amount > 0:
                payment_modes_used.append(f"Cash: ₹{cash_amount:,.2f}")
            if online_amount > 0:
                payment_modes_used.append(f"Online: ₹{online_amount:,.2f}")
            if udhaar_amount > 0:
                payment_modes_used.append(f"Udhaar: ₹{udhaar_amount:,.2f}")
            
            payment_info = " | ".join(payment_modes_used)
            
            for cart_item in st.session_state.bill_cart:
                item_name = cart_item['Item']
                sold_qty = cart_item['Qty']
                unit = cart_item['Unit']
                rate = cart_item['Rate']
                amount = cart_item['Amount']
                
                save_data("Sales", [
                    str(today_dt),
                    item_name,
                    f"{sold_qty} {unit}",
                    amount,
                    payment_info,
                    customer_info,
                    0,
                    0,
                    "No GST"
                ])
                
                # Update stock in Google Sheets
                inv_df_update = load_data("Inventory")
                if not inv_df_update.empty:
                    product_rows = inv_df_update[inv_df_update.iloc[:, 0] == item_name]
                    
                    if not product_rows.empty:
                        current_stock = pd.to_numeric(product_rows.iloc[-1, 1], errors='coerce')
                        current_unit = product_rows.iloc[-1, 2]
                        new_stock = current_stock - sold_qty
                        
                        if update_stock_in_sheet(item_name, new_stock):
                            st.success(f"✅ {item_name}: {current_stock} → {new_stock} {current_unit}")
                        else:
                            st.warning(f"⚠️ Please manually update {item_name} stock in Google Sheets")
            
            if cash_amount > 0:
                update_balance(cash_amount, "Cash", 'add')
                st.success(f"💵 Cash: ₹{cash_amount:,.2f} added")
            
            if online_amount > 0:
                update_balance(online_amount, "Online", 'add')
                st.success(f"🏦 Online: ₹{online_amount:,.2f} added")
            
            if udhaar_amount > 0:
                save_data("CustomerKhata", [customer_info, udhaar_amount, str(today_dt), "Sale on credit"])
                st.warning(f"📒 Udhaar: ₹{udhaar_amount:,.2f} added to due")
            
            st.success(f"✅ Sale completed!")
            
            st.session_state.bill_cart = []
            st.balloons()
            time.sleep(2)
            st.rerun()
    
    else:
        st.info("🛒 Cart is empty. Add items to start billing.")

# ========================================
# MENU 3: PURCHASE
# ========================================
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    if 'purchase_cart' not in st.session_state:
        st.session_state.purchase_cart = []
    
    st.markdown("### 👤 Party/Supplier Details")
    col1, col2 = st.columns(2)
    
    with col1:
        supplier_name = st.text_input("📝 Party/Supplier Name *", key="supplier_name_input")
    
    with col2:
        supplier_phone = st.text_input("📞 Party Phone *", key="supplier_phone_input")
    
    st.divider()
    
    st.markdown("### 💰 Payment Method")
    col1, col2 = st.columns(2)
    
    with col1:
        payment_type = st.radio(
            "Payment Type",
            ["💵 Cash (Shop)", "🏦 Online (Shop)", "🏢 Udhaar (Credit)", "👋 By Hand (Pocket Money)"],
            horizontal=False,
            key="payment_radio"
        )
    
    with col2:
        if payment_type == "💵 Cash (Shop)":
            payment_mode = "Cash"
            st.info(f"✅ Payment from Shop Cash")
        elif payment_type == "🏦 Online (Shop)":
            payment_mode = "Online"
            st.info(f"✅ Payment from Shop Online")
        elif payment_type == "🏢 Udhaar (Credit)":
            payment_mode = "Udhaar"
            st.warning("⚠️ Added to Supplier Dues")
        else:
            payment_mode = "By Hand"
            st.success("✅ Personal investment")
    
    st.divider()
    
    with st.expander("🛒 Add Items to Purchase", expanded=True):
        inv_df = load_data("Inventory")
        
        col1, col2, col3, col4 = st.columns(4)
        
        item_name = ""
        
        with col1:
            if not inv_df.empty:
                existing_items = inv_df.iloc[:, 0].unique().tolist()
                
                item_from_dropdown = st.selectbox(
                    "Existing Items", 
                    ["(Select existing item)"] + existing_items,
                    key="item_dropdown"
                )
                
                item_from_text = st.text_input(
                    "OR Type new item",
                    key="new_item_text",
                    placeholder="New product name"
                )
                
                if item_from_text and item_from_text.strip():
                    item_name = item_from_text.strip().upper()
                elif item_from_dropdown and item_from_dropdown != "(Select existing item)":
                    item_name = item_from_dropdown
                else:
                    item_name = ""
            else:
                item_from_text = st.text_input("Item Name", key="item_name_only")
                item_name = item_from_text.strip().upper() if item_from_text else ""
        
        with col2:
            qty = st.number_input("Quantity", min_value=0.1, value=1.0, step=0.1, key="qty_input")
        with col3:
            unit = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams", "Ltr"], key="unit_input")
        with col4:
            rate = st.number_input("Rate/Unit", min_value=0.0, value=0.0, step=1.0, key="rate_input")
        
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
                    st.error("⚠️ Fill all fields!")
        
        with col2:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.purchase_cart = []
                st.rerun()
    
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
        
        st.divider()
        
        can_save = supplier_name and supplier_name.strip() and supplier_phone and supplier_phone.strip()
        
        if not can_save:
            st.error("⚠️ Please enter Supplier Name and Phone!")
        
        if st.button("💾 SAVE PURCHASE", type="primary", use_container_width=True, disabled=not can_save):
            supplier_full_info = f"{supplier_name} ({supplier_phone})"
            
            for item in st.session_state.purchase_cart:
                payment_info = f"{payment_mode} - {supplier_full_info}"
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
            
            if payment_mode == "Cash":
                update_balance(total_amount, "Cash", 'subtract')
                st.success(f"✅ ₹{total_amount:,.2f} deducted from Cash")
            elif payment_mode == "Online":
                update_balance(total_amount, "Online", 'subtract')
                st.success(f"✅ ₹{total_amount:,.2f} deducted from Online")
            elif payment_mode == "By Hand":
                items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                save_data("HandInvestments", [str(today_dt), supplier_full_info, total_amount, items_note, "Purchase by hand"])
                st.success(f"✅ ₹{total_amount:,.2f} invested from pocket!")
            else:
                items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                save_data("Dues", [supplier_full_info, total_amount, str(today_dt), f"Purchase: {items_note}"])
                st.success(f"✅ ₹{total_amount:,.2f} added to {supplier_name}'s dues!")
            
            st.session_state.purchase_cart = []
            st.balloons()
            time.sleep(2)
            st.rerun()
    else:
        st.info("🛒 Cart is empty.")

# ========================================
# MENU 4: LIVE STOCK
# ========================================
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    
    if not i_df.empty and len(i_df.columns) > 4:
        latest_stock = i_df.groupby(i_df.columns[0]).tail(1).copy()
        
        latest_stock['qty_v'] = pd.to_numeric(latest_stock.iloc[:, 1], errors='coerce').fillna(0)
        latest_stock['rate_v'] = pd.to_numeric(latest_stock.iloc[:, 3], errors='coerce').fillna(0)
        latest_stock['value'] = latest_stock['qty_v'] * latest_stock['rate_v']
        t_v = latest_stock['value'].sum()
        
        st.subheader(f"💰 Total Stock Value: ₹{t_v:,.2f}")
        
        stock_summary = latest_stock[[latest_stock.columns[0], latest_stock.columns[1], latest_stock.columns[2], latest_stock.columns[3], 'qty_v', 'value']].copy()
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
            for item in low_stock_items:
                st.error(f"🚨 **{item['Item']}** - {item['Quantity']} - Rate: {item['Rate']} - Value: {item['Stock Value']}")
        
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
        st.subheader("📋 Recent Expenses")
        st.dataframe(e_df.tail(10), use_container_width=True)

# ========================================
# MENU 6: PET REGISTER
# ========================================
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register - Pets for Sale")
    
    tab1, tab2 = st.tabs(["➕ Add Pet", "📋 Available Pets"])
    
    with tab1:
        with st.form("pet_reg"):
            st.subheader("Register Pet for Sale")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit", "Bird", "Hamster", "Other"])
                pet_breed = st.text_input("Breed *")
                pet_age = st.number_input("Age (months)", min_value=0, max_value=120, step=1)
                pet_price = st.number_input("Selling Price (₹) *", min_value=0, step=100)
            
            with col2:
                pet_gender = st.selectbox("Gender", ["Male", "Female"])
                pet_color = st.text_input("Color")
            
            notes = st.text_area("Additional Notes")
            
            if st.form_submit_button("💾 Add Pet", type="primary"):
                if pet_breed and pet_price > 0:
                    save_data("PetRegister", [
                        str(today_dt),
                        pet_type,
                        pet_breed,
                        pet_age,
                        pet_gender,
                        pet_color,
                        pet_price,
                        "Available",
                        notes
                    ])
                    st.success(f"✅ {pet_type} ({pet_breed}) added!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Fill Breed and Price!")
    
    with tab2:
        pets_df = load_data("PetRegister")
        
        if not pets_df.empty:
            st.subheader(f"📊 Total Pets: {len(pets_df)}")
            
            for idx, row in pets_df.iterrows():
                pet_type = row.iloc[1] if len(row) > 1 else "Pet"
                pet_breed = row.iloc[2] if len(row) > 2 else "Unknown"
                pet_price = row.iloc[6] if len(row) > 6 else 0
                
                with st.expander(f"🐾 {pet_type} - {pet_breed} - ₹{pet_price:,.0f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {pet_type}")
                        st.write(f"**Breed:** {pet_breed}")
                        st.write(f"**Age:** {row.iloc[3] if len(row) > 3 else 'N/A'} months")
                    
                    with col2:
                        st.write(f"**Gender:** {row.iloc[4] if len(row) > 4 else 'N/A'}")
                        st.write(f"**Color:** {row.iloc[5] if len(row) > 5 else 'N/A'}")
                        st.write(f"**Price:** ₹{pet_price:,.0f}")
        else:
            st.info("No pets registered yet.")

# ========================================
# MENU 7: CUSTOMER DUE
# ========================================
elif menu == "📒 Customer Due":
    st.header("📒 Customer Due Management")
    
    tab1, tab2 = st.tabs(["💰 Transaction Entry", "📊 View Summary"])
    
    with tab1:
        with st.form("khata"):
            st.subheader("Record Transaction")
            cust = st.text_input("Customer Name/Phone *")
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=10.0)
            
            transaction_type = st.radio(
                "Transaction Type:",
                ["Payment Received (Customer paid)", "Credit Given (Gave udhaar)"],
                horizontal=False
            )
            
            pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Other"])
            note = st.text_input("Note (Optional)")
            
            if st.form_submit_button("💾 Save Transaction", type="primary"):
                if amt > 0 and cust.strip():
                    if "Payment Received" in transaction_type:
                        save_data("CustomerKhata", [cust, -amt, str(today_dt), f"Payment: {note}"])
                        
                        if pay_mode == "Cash":
                            update_balance(amt, "Cash", 'add')
                        elif pay_mode == "Online":
                            update_balance(amt, "Online", 'add')
                        
                        st.success(f"✅ Payment Rs.{amt:,.2f} received")
                    else:
                        save_data("CustomerKhata", [cust, amt, str(today_dt), f"Credit: {note}"])
                        st.success(f"✅ Credit Rs.{amt:,.2f} given")
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Fill all fields!")
    
    with tab2:
        k_df = load_data("CustomerKhata")
        
        if not k_df.empty and len(k_df.columns) > 1:
            st.subheader("📊 Customer Due Summary")
            
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            sum_df = sum_df[sum_df['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                total_due = sum_df['Balance'].sum()
                
                col1, col2 = st.columns(2)
                col1.metric("💰 Total Due", f"Rs.{total_due:,.2f}")
                col2.metric("👥 Customers", len(sum_df))
                
                st.divider()
                
                for idx, row in sum_df.iterrows():
                    st.error(f"🔴 **{row['Customer']}** - Due: Rs.{row['Balance']:,.2f}")
            else:
                st.success("✅ No outstanding dues!")
            
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(k_df, use_container_width=True)
        else:
            st.info("No due records yet.")

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
            m = st.selectbox("Payment Mode", ["Cash", "Online", "Hand", "N/A"])
            
            if st.form_submit_button("💾 Save", type="primary"):
                if a > 0 and s.strip():
                    if "Credit" in t or "Liya" in t:
                        final_amt = a
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Credit"])
                        st.success(f"✅ ₹{a:,.2f} credit added")
                    else:
                        final_amt = -a
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Payment"])
                        
                        if m == "Cash":
                            update_balance(a, "Cash", 'subtract')
                        elif m == "Online":
                            update_balance(a, "Online", 'subtract')
                        
                        st.success(f"✅ ₹{a:,.2f} payment recorded")
                    
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
                for _, row in sum_df.iterrows():
                    supplier_name = row['Supplier']
                    balance = row['Balance']
                    
                    if balance > 0:
                        st.error(f"🔴 **{supplier_name}** - We Owe: ₹{balance:,.2f}")
                    else:
                        st.success(f"🟢 **{supplier_name}** - They Owe: ₹{abs(balance):,.2f}")
            else:
                st.success("✅ All settled!")
            
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(d_df, use_container_width=True)
        else:
            st.info("No supplier transactions yet.")

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
            st.info("**Weekday:** 2% of purchase")
            st.info("**Weekend:** 5% of purchase")
        with col2:
            st.success("**Redemption:** 100 points min")
            st.success("**Referral:** +10 points")
        
        st.divider()
        st.subheader("👥 Customer Points Leaderboard")
        
        points_data = s_df.groupby(s_df.columns[5]).agg({
            s_df.columns[6]: 'sum',
            s_df.columns[3]: 'sum'
        }).reset_index()
        
        points_data.columns = ['Customer', 'Points', 'Total_Spent']
        points_data['Points'] = pd.to_numeric(points_data['Points'], errors='coerce').fillna(0)
        points_data['Total_Spent'] = pd.to_numeric(points_data['Total_Spent'], errors='coerce').fillna(0)
        points_data = points_data[points_data['Points'] != 0].sort_values('Points', ascending=False)
        
        for idx, row in points_data.head(10).iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{row['Customer']}**")
            with col2:
                st.metric("Points", f"{int(row['Points'])} 👑")
            with col3:
                st.metric("Spent", f"₹{row['Total_Spent']:,.0f}")
    else:
        st.info("No sales data available.")

# ========================================
# MENU 10: ADVANCED REPORTS
# ========================================
elif menu == "📈 Advanced Reports":
    st.header("📈 Advanced Sales Reports")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 3:
        tab1, tab2 = st.tabs(["📊 Best Sellers", "🐌 Slow Moving"])
        
        with tab1:
            st.subheader("🏆 Best Selling Products")
            
            try:
                product_sales = s_df.groupby(s_df.columns[1], as_index=False).agg({
                    s_df.columns[3]: 'sum'
                })
                
                product_sales['Units_Sold'] = s_df.groupby(s_df.columns[1]).size().values
                product_sales.columns = ['Product', 'Revenue', 'Units_Sold']
                product_sales['Revenue'] = pd.to_numeric(product_sales['Revenue'], errors='coerce')
                product_sales = product_sales.sort_values('Revenue', ascending=False).head(10)
                
                if not product_sales.empty:
                    for idx, row in product_sales.iterrows():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{row['Product']}**")
                        with col2:
                            st.metric("Revenue", f"₹{row['Revenue']:,.0f}")
                        with col3:
                            st.metric("Units", f"{row['Units_Sold']}")
                else:
                    st.info("No data")
            except:
                st.info("No data")
        
        with tab2:
            st.subheader("🐌 Slow Moving Products")
            
            try:
                inv_df = load_data("Inventory")
                if not inv_df.empty:
                    product_movement = s_df.groupby(s_df.columns[1]).size()
                    product_movement_df = product_movement.reset_index()
                    product_movement_df.columns = ['Product', 'Transactions']
                    slow_movers = product_movement_df.sort_values('Transactions').head(10)
                    
                    if not slow_movers.empty:
                        for idx, row in slow_movers.iterrows():
                            st.warning(f"⚠️ **{row['Product']}** - {row['Transactions']} transactions")
                    else:
                        st.info("No slow movers")
                else:
                    st.info("No data")
            except:
                st.info("No data")
    else:
        st.info("No sales data")
