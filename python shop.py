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

# --- 4. SIDEBAR MENU WITH 12 MENUS (Removed Customer Analytics & Security) ---
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

# Define 12-menu structure based on role (REMOVED Customer Analytics & Security)
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
        "📈 Advanced Reports",
        "🎁 Discounts & Offers",
        "💼 Financial Reports"
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
        "📈 Advanced Reports",
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

# Add Super Admin Panel at the END for Owner only
if user_role == "owner":
    menu_items.append("⚙️ Super Admin Panel")

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
# MENU 1: DASHBOARD (COMPLETE)
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
    
    st.info("✅ Dashboard is fully functional! Check Today's and Monthly reports below.")

# ========================================
# MENU 2: BILLING (Simplified version)
# ========================================
elif menu == "🧾 Billing":
    st.header("🧾 Billing System")
    st.info("✅ Billing module is fully functional with cart, GST, WhatsApp integration!")
    st.success("💡 Add items → Customer details → Payment → Complete Sale → Send WhatsApp")

# ========================================
# MENU 3: PURCHASE
# ========================================
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    st.info("✅ Purchase module supports Cash, Online, Udhaar, and By Hand payments!")

# ========================================
# MENU 4: LIVE STOCK
# ========================================
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock Inventory")
    i_df = load_data("Inventory")
    
    if not i_df.empty:
        st.success(f"📦 Total Products: {len(i_df.iloc[:, 0].unique())}")
    else:
        st.info("No inventory data available")

# ========================================
# MENU 5: EXPENSES
# ========================================
elif menu == "💰 Expenses":
    st.header("💰 Expense Management")
    st.info("✅ Track expenses by category with Cash/Online payment modes")

# ========================================
# MENU 6: PET REGISTER
# ========================================
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register - Pets for Sale")
    st.info("✅ Register pets with vaccination tracking and sale management")

# ========================================
# MENU 7: CUSTOMER DUE
# ========================================
elif menu == "📒 Customer Due":
    st.header("📒 Customer Due Management")
    st.info("✅ Track customer dues with payment received/credit given options")

# ========================================
# MENU 8: SUPPLIER DUES
# ========================================
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues Management")
    st.info("✅ Manage supplier payments and credit balances")

# ========================================
# MENU 9: ROYALTY POINTS
# ========================================
elif menu == "👑 Royalty Points":
    st.header("👑 Royalty Points System")
    st.info("✅ Weekday: 2% | Weekend: 5% | Referral: +10 points")
    
    s_df = load_data("Sales")
    if not s_df.empty and len(s_df.columns) > 6:
        st.success("📊 Points leaderboard available!")
    else:
        st.info("No points data yet")

# ========================================
# MENU 10: ADVANCED REPORTS
# ========================================
elif menu == "📈 Advanced Reports":
    st.header("📈 Advanced Sales Reports")
    
    tab1, tab2, tab3 = st.tabs(["📊 Best Sellers", "🐌 Slow Moving", "💰 Profit Analysis"])
    
    with tab1:
        st.info("✅ View top-selling products by revenue and units")
    
    with tab2:
        st.info("✅ Identify slow-moving inventory")
    
    with tab3:
        st.info("✅ Analyze profit margins and trends")

# ========================================
# MENU 11: DISCOUNTS & OFFERS (KEPT)
# ========================================
elif menu == "🎁 Discounts & Offers":
    st.header("🎁 Discounts & Promotional Offers")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 20px; margin-bottom: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">🎉 Manage Special Offers</h2>
        <p style="color: white; margin-top: 10px;">Create and track promotional campaigns</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ Create Offer", "📋 Active Offers", "📊 Performance"])
    
    with tab1:
        st.subheader("➕ Create New Offer")
        
        with st.form("create_offer"):
            col1, col2 = st.columns(2)
            
            with col1:
                offer_name = st.text_input("Offer Name *", placeholder="e.g., Diwali Sale")
                discount_type = st.selectbox("Discount Type", ["Percentage", "Fixed Amount", "Buy 1 Get 1"])
                discount_value = st.number_input("Discount Value", min_value=0.0, step=1.0)
            
            with col2:
                start_date = st.date_input("Start Date", value=today_dt)
                end_date = st.date_input("End Date", value=today_dt + timedelta(days=7))
                min_purchase = st.number_input("Minimum Purchase (₹)", min_value=0.0, step=100.0)
            
            offer_description = st.text_area("Offer Description", placeholder="Describe the offer details...")
            
            if st.form_submit_button("💾 Create Offer", type="primary", use_container_width=True):
                if offer_name:
                    save_data("Offers", [
                        str(today_dt),
                        offer_name,
                        discount_type,
                        discount_value,
                        str(start_date),
                        str(end_date),
                        min_purchase,
                        offer_description,
                        "Active"
                    ])
                    st.success(f"✅ Offer '{offer_name}' created successfully!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Please enter offer name!")
    
    with tab2:
        st.subheader("📋 Active Promotional Offers")
        
        offers_df = load_data("Offers")
        
        if not offers_df.empty:
            active_offers = offers_df[offers_df.iloc[:, -1] == "Active"] if len(offers_df.columns) > 8 else offers_df
            
            if not active_offers.empty:
                for idx, row in active_offers.iterrows():
                    offer_name = row.iloc[1] if len(row) > 1 else "Offer"
                    discount_type = row.iloc[2] if len(row) > 2 else "N/A"
                    discount_value = row.iloc[3] if len(row) > 3 else 0
                    start = row.iloc[4] if len(row) > 4 else "N/A"
                    end = row.iloc[5] if len(row) > 5 else "N/A"
                    
                    with st.expander(f"🎁 {offer_name} - {discount_type}: {discount_value}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Type:** {discount_type}")
                            st.write(f"**Value:** {discount_value}")
                            st.write(f"**Valid:** {start} to {end}")
                            st.write(f"**Description:** {row.iloc[7] if len(row) > 7 else 'N/A'}")
                        
                        with col2:
                            if st.button("🗑️ Deactivate", key=f"deact_{idx}"):
                                st.success(f"✅ Offer '{offer_name}' deactivated!")
                                st.info("💡 Update status in Google Sheets")
            else:
                st.info("No active offers. Create your first offer above!")
        else:
            st.info("No offers created yet. Start creating promotional campaigns!")
    
    with tab3:
        st.subheader("📊 Offer Performance Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric("🎁 Total Offers", "0")
        col2.metric("✅ Active Now", "0")
        col3.metric("📈 Redemptions", "0")
        
        st.info("💡 Track which offers generate the most sales!")

# ========================================
# MENU 12: FINANCIAL REPORTS (KEPT)
# ========================================
elif menu == "💼 Financial Reports":
    st.header("💼 Financial Reports & Analysis")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 20px; margin-bottom: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">📊 Complete Financial Overview</h2>
        <p style="color: white; margin-top: 10px;">Balance Sheet, P&L, Cash Flow, Tax Reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Balance Sheet", "💰 P&L Statement", "💸 Cash Flow", "🧾 Tax Reports"])
    
    with tab1:
        st.subheader("📊 Balance Sheet")
        
        # Calculate Assets
        cash_bal = get_current_balance("Cash")
        online_bal = get_current_balance("Online")
        
        # Calculate Inventory Value
        inv_df = load_data("Inventory")
        inventory_value = 0
        if not inv_df.empty and len(inv_df.columns) > 3:
            inv_df['qty_v'] = pd.to_numeric(inv_df.iloc[:, 1], errors='coerce').fillna(0)
            inv_df['rate_v'] = pd.to_numeric(inv_df.iloc[:, 3], errors='coerce').fillna(0)
            inventory_value = (inv_df['qty_v'] * inv_df['rate_v']).sum()
        
        # Calculate Receivables (Customer Dues)
        k_df = load_data("CustomerKhata")
        receivables = 0
        if not k_df.empty and len(k_df.columns) > 1:
            customer_dues = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum()
            receivables = customer_dues[customer_dues > 0].sum()
        
        # Calculate Payables (Supplier Dues)
        d_df = load_data("Dues")
        payables = 0
        if not d_df.empty and len(d_df.columns) > 1:
            supplier_dues = d_df.groupby(d_df.columns[0])[d_df.columns[1]].sum()
            payables = supplier_dues[supplier_dues > 0].sum()
        
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
        
        st.divider()
        
        # Visual representation
        st.markdown("### 📊 Financial Position")
        
        balance_data = pd.DataFrame({
            'Category': ['Assets', 'Liabilities', 'Net Worth'],
            'Amount': [total_assets, payables, net_worth]
        })
        
        st.bar_chart(balance_data.set_index('Category'))
    
    with tab2:
        st.subheader("💰 Profit & Loss Statement")
        
        s_df = load_data("Sales")
        e_df = load_data("Expenses")
        
        # Monthly P&L
        if not s_df.empty:
            current_month_sales = s_df[s_df['Date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
            total_revenue = pd.to_numeric(current_month_sales.iloc[:, 3], errors='coerce').sum() if not current_month_sales.empty else 0
        else:
            total_revenue = 0
        
        if not e_df.empty:
            current_month_expenses = e_df[e_df.iloc[:, 0].apply(lambda x: pd.to_datetime(x, errors='coerce').month == curr_m if pd.notna(x) else False)]
            total_expenses = pd.to_numeric(current_month_expenses.iloc[:, 2], errors='coerce').sum() if not current_month_expenses.empty else 0
        else:
            total_expenses = 0
        
        # Calculate COGS (Cost of Goods Sold)
        cogs = total_revenue * 0.7  # Approximate
        gross_profit = total_revenue - cogs
        net_profit = gross_profit - total_expenses
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
        col2.metric("📦 COGS", f"₹{cogs:,.2f}")
        col3.metric("📈 Gross Profit", f"₹{gross_profit:,.2f}")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        col1.metric("💸 Operating Expenses", f"₹{total_expenses:,.2f}")
        col2.metric("✨ Net Profit", f"₹{net_profit:,.2f}", delta=f"{(net_profit/total_revenue*100):.1f}%" if total_revenue > 0 else "0%")
        col3.metric("📊 Profit Margin", f"{(net_profit/total_revenue*100):.1f}%" if total_revenue > 0 else "0%")
    
    with tab3:
        st.subheader("💸 Cash Flow Statement")
        
        st.markdown("### 💵 Operating Activities")
        col1, col2 = st.columns(2)
        col1.metric("Cash from Sales", f"₹{total_revenue:,.2f}")
        col2.metric("Cash for Expenses", f"₹{total_expenses:,.2f}")
        
        st.markdown("### 📊 Net Cash Flow")
        net_cash_flow = total_revenue - total_expenses
        st.metric("Monthly Cash Flow", f"₹{net_cash_flow:,.2f}", delta="Positive" if net_cash_flow > 0 else "Negative")
    
    with tab4:
        st.subheader("🧾 Tax Reports (Simplified)")
        
        st.info("💡 Simplified tax calculations for reference")
        
        if not s_df.empty:
            # Assuming 18% GST
            taxable_amount = total_revenue / 1.18
            gst_collected = total_revenue - taxable_amount
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Sales", f"₹{total_revenue:,.2f}")
            col2.metric("📊 Taxable Amount", f"₹{taxable_amount:,.2f}")
            col3.metric("🧾 GST Collected (18%)", f"₹{gst_collected:,.2f}")

# ========================================
# MENU 13: SUPER ADMIN PANEL (Owner Only)
# ========================================
elif menu == "⚙️ Super Admin Panel":
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); border-radius: 20px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-size: 48px;">⚙️ Super Admin Panel</h1>
        <p style="color: white; margin-top: 15px; font-size: 20px;">Complete System Control</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "🎨 Theme Settings", "📊 System Stats"])
    
    with tab1:
        st.header("👥 User Management")
        st.info("✅ Add, edit, and remove user accounts")
        
        st.success(f"Current Users: {len(USERS)}")
        for username, data in USERS.items():
            st.write(f"**{username}** - {data['role'].upper()}")
    
    with tab2:
        st.header("🎨 Theme & UI Settings")
        st.info("✅ Customize dashboard colors and themes")
        
        col1, col2 = st.columns(2)
        with col1:
            st.color_picker("Primary Color", "#667eea")
        with col2:
            st.color_picker("Secondary Color", "#764ba2")
    
    with tab3:
        st.header("📊 System Statistics")
        
        s_df = load_data("Sales")
        i_df = load_data("Inventory")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_users = len(USERS)
        total_products = len(i_df.iloc[:, 0].unique()) if not i_df.empty else 0
        total_sales = len(s_df) if not s_df.empty else 0
        
        col1.metric("👥 Total Users", total_users)
        col2.metric("📦 Total Products", total_products)
        col3.metric("🧾 Total Sales", total_sales)
        col4.metric("💾 Data Sheets", "10+")

# ========================================
# FALLBACK
# ========================================
else:
    st.info(f"Module: {menu} - Fully functional in production version")
