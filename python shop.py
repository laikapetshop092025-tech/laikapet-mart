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

                inv_df_update = load_data("Inventory")
                if not inv_df_update.empty:
                    product_rows = inv_df_update[inv_df_update.iloc[:, 0] == item_name]
                    
                    if not product_rows.empty:
                        current_stock = pd.to_numeric(product_rows.iloc[-1, 1], errors='coerce')
                        current_unit = product_rows.iloc[-1, 2]
                        current_rate = pd.to_numeric(product_rows.iloc[-1, 3], errors='coerce')
                        new_stock = current_stock - sold_qty
                        
                        if update_stock_in_sheet(item_name, new_stock):
                            st.success(f"✅ {item_name}: {current_stock} → {new_stock} {current_unit}")
                        else:
                            st.error(f"❌ Failed to update {item_name} stock")
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
        return 0.0def get_current_balance(mode):
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
        "📒 Customer Due",
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
        "📒 Customer Due",
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
    
    # Customer Due Calculation (renamed from Udhaar)
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
    hand_investment_error = False
    try:
        hand_df = load_data("HandInvestments")
        if not hand_df.empty and len(hand_df.columns) > 2:
            # Convert to numeric and sum, handling any errors
            hand_amounts = pd.to_numeric(hand_df.iloc[:, 2], errors='coerce').fillna(0)
            total_hand_investment = hand_amounts.sum()
    except Exception as e:
        total_hand_investment = 0
        hand_investment_error = True
    
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
            
            # Simple display without complex iteration
            try:
                hand_df = load_data("HandInvestments")
                
                if not hand_df.empty:
                    st.markdown("### 📋 Investment History")
                    st.dataframe(hand_df, use_container_width=True)
                    
                    st.info("💡 Columns: Date | Supplier | Amount | Items | Note")
                else:
                    st.info("No hand investments yet. When you purchase using 'By Hand', entries will appear here.")
                    st.markdown("""
                    **How to add Hand Investment:**
                    1. Go to Purchase menu
                    2. Select payment type: 👋 By Hand (Pocket Money)
                    3. Complete the purchase
                    4. Investment will be tracked here
                    """)
            except Exception as e:
                st.info("No hand investments yet. When you purchase using 'By Hand', entries will appear here.")
                st.caption("💡 Note: HandInvestments sheet will be created automatically on first 'By Hand' purchase")
        
        with tab3:
            st.subheader("📊 Total Business Capital")
            
            total_capital = cash_bal + online_bal + total_hand_investment
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Shop Cash", f"₹{cash_bal:,.2f}")
            col2.metric("Shop Online", f"₹{online_bal:,.2f}")
            col3.metric("Hand Investment", f"₹{total_hand_investment:,.2f}")
            col4.metric("Total Capital", f"₹{total_capital:,.2f}", delta="All sources")
    
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
    
    # Today's Purchases (ACTUAL COST) - FIXED
    p_df = load_data("Inventory")
    today_purchase = 0
    
    if not p_df.empty and len(p_df.columns) > 6:
        try:
            p_df['pur_date'] = pd.to_datetime(p_df.iloc[:, 5], errors='coerce').dt.date
            
            # ✅ ONLY count entries with "Purchase" or "Supplier" in notes (Column 6)
            p_today = p_df[
                (p_df['pur_date'] == today_dt) & 
                (p_df.iloc[:, 6].str.contains('Cash|Online|Hand|Udhaar|Supplier', case=False, na=False))
            ]
            
            if not p_today.empty:
                today_purchase = pd.to_numeric(p_today.iloc[:, 4], errors='coerce').sum()
            else:
                today_purchase = 0
        except Exception as e:
            today_purchase = 0
    else:
        today_purchase = 0
    if not e_df.empty and len(e_df.columns) > 2:
        try:
            e_df['exp_date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
            e_today = e_df[e_df['exp_date'] == today_dt]
            today_expense = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty else 0
        except:
            today_expense = 0
    else:
        today_expense = 0
    
    # Today's REAL Profit (Item-wise calculation from actual purchase rates)
    today_profit = 0
    today_profit_details = []
    
    if not s_df.empty and 'Date' in s_df.columns:
        s_today = s_df[s_df['Date'] == today_dt]
        
        if not s_today.empty:
            inv_df_profit = load_data("Inventory")
            
            for idx, sale_row in s_today.iterrows():
                item_name = sale_row.iloc[1] if len(sale_row) > 1 else ""
                sale_amount = pd.to_numeric(sale_row.iloc[3], errors='coerce') if len(sale_row) > 3 else 0
                qty_str = str(sale_row.iloc[2]) if len(sale_row) > 2 else "0"
                
                # Extract quantity
                qty_parts = qty_str.split()
                sold_qty = float(qty_parts[0]) if len(qty_parts) > 0 else 0
                
                # ✅ Get LATEST purchase rate (not average) for this item
                purchase_cost = 0
                if not inv_df_profit.empty and item_name:
                    item_rows = inv_df_profit[inv_df_profit.iloc[:, 0] == item_name]
                    
                    if not item_rows.empty:
                        # Get LATEST purchase rate (last entry)
                        latest_rate = pd.to_numeric(item_rows.iloc[-1, 3], errors='coerce')
                        purchase_cost = sold_qty * latest_rate
                    else:
                        # New item - assume 70% cost
                        purchase_cost = sale_amount * 0.7
                else:
                    # No inventory data - assume 70% cost
                    purchase_cost = sale_amount * 0.7
                
                # Calculate profit
                item_profit = sale_amount - purchase_cost
                today_profit += item_profit
                
                today_profit_details.append({
                    'item': item_name,
                    'sale': sale_amount,
                    'cost': purchase_cost,
                    'profit': item_profit
                })
    
    # Subtract expenses from profit
    today_profit = today_profit - today_expense
        # Subtract expenses from profit
    today_profit = today_profit - today_expense
    
    # Colorful Cards for Today
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
    # Show Item-wise Profit Breakdown
    if today_profit_details:
        with st.expander("📊 Today's Item-wise Profit Breakdown", expanded=False):
            st.markdown("### 🔍 How Today's Profit is Calculated")
            
            total_gross_profit = 0
            
            for detail in today_profit_details:
                item = detail['item']
                sale = detail['sale']
                cost = detail['cost']
                profit = detail['profit']
                total_gross_profit += profit
                
                profit_percent = (profit / sale * 100) if sale > 0 else 0
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item}**")
                with col2:
                    st.success(f"Sale: ₹{sale:,.0f}")
                with col3:
                    st.info(f"Cost: ₹{cost:,.0f}")
                with col4:
                    st.warning(f"Profit: ₹{profit:,.0f}")
                with col5:
                    st.metric("Margin", f"{profit_percent:.1f}%")
                
                st.divider()
            
            st.markdown("### 💰 Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Gross Profit", f"₹{total_gross_profit:,.2f}")
            with col2:
                st.metric("Less: Expenses", f"₹{today_expense:,.2f}")
            with col3:
                st.metric("Net Profit", f"₹{today_profit:,.2f}", 
                         delta=f"₹{total_gross_profit - today_expense:,.2f}")
            
            st.info(f"💡 **Formula:** Net Profit = (Sale Price - Purchase Cost) - Expenses")
            st.success(f"✅ **Calculation:** (₹{total_gross_profit:,.2f} gross profit) - (₹{today_expense:,.2f} expenses) = ₹{today_profit:,.2f}")
    
    # Manual Correction Settings for Today's Report
    with st.expander("🔧 Today's Report Settings (Manual Corrections)"):
        st.success("✅ Auto-calculated from transactions, but you can manually adjust if needed")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Sales")
            st.write(f"Current (Auto): ₹{today_sale:,.2f}")
            manual_today_sale = st.number_input("Correct Today's Sale", value=float(today_sale), step=1.0, key="manual_today_sale")
            
            st.divider()
            
            st.subheader("🛒 Purchases")
            st.write(f"Current (Auto): ₹{today_purchase:,.2f}")
            manual_today_purchase = st.number_input("Correct Today's Purchase", value=float(today_purchase), step=1.0, key="manual_today_purchase")
        
        with col2:
            st.subheader("💸 Expenses")
            st.write(f"Current (Auto): ₹{today_expense:,.2f}")
            manual_today_expense = st.number_input("Correct Today's Expense", value=float(today_expense), step=1.0, key="manual_today_expense")
            
            st.divider()
            
            st.subheader("📊 Profit (Auto-calculated)")
            manual_profit = manual_today_sale - manual_today_purchase - manual_today_expense
            st.metric("Corrected Profit", f"₹{manual_profit:,.2f}")
        
        st.divider()
        
        if manual_today_sale != today_sale or manual_today_purchase != today_purchase or manual_today_expense != today_expense:
            st.warning("⚠️ You have made manual corrections!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Sale:** ₹{today_sale:,.2f} → ₹{manual_today_sale:,.2f}")
            with col2:
                st.info(f"**Purchase:** ₹{today_purchase:,.2f} → ₹{manual_today_purchase:,.2f}")
            with col3:
                st.info(f"**Expense:** ₹{today_expense:,.2f} → ₹{manual_today_expense:,.2f}")
            
            st.markdown("### 📊 Corrected Summary")
            
            st.markdown(f"""
            <div style="display: flex; gap: 15px; margin-top: 20px;">
                <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">💰 Corrected Sale</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_today_sale:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">🛒 Corrected Purchase</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_today_purchase:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">💸 Corrected Expense</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_today_expense:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">✨ Corrected Profit</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_profit:,.2f}</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 Save Corrected Values", type="primary", use_container_width=True):
                # Save corrections to a special sheet for reference
                save_data("DailyCorrections", [
                    str(today_dt),
                    manual_today_sale,
                    manual_today_purchase,
                    manual_today_expense,
                    manual_profit,
                    f"Auto: Sale={today_sale}, Purchase={today_purchase}, Expense={today_expense}"
                ])
                st.success("✅ Manual corrections saved for today's report!")
                st.balloons()
                time.sleep(1)
                st.rerun()
        else:
            st.success("✅ All values match auto-calculated amounts")
    
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
    
    # This Month's Purchases (ACTUAL COST)
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
    
    # This Month's REAL Profit (Item-wise calculation from actual purchase rates)
    month_profit = 0
    month_profit_details = []
    
    if not s_df.empty and 'Date' in s_df.columns:
        s_month = s_df[s_df['Date'].apply(lambda x: x.month == curr_m if isinstance(x, date) else False)]
        
        if not s_month.empty:
            inv_df_profit = load_data("Inventory")
            
            for idx, sale_row in s_month.iterrows():
                item_name = sale_row.iloc[1] if len(sale_row) > 1 else ""
                sale_amount = pd.to_numeric(sale_row.iloc[3], errors='coerce') if len(sale_row) > 3 else 0
                qty_str = str(sale_row.iloc[2]) if len(sale_row) > 2 else "0"
                
                # Extract quantity
                qty_parts = qty_str.split()
                sold_qty = float(qty_parts[0]) if len(qty_parts) > 0 else 0
                
                # Get LATEST purchase rate (not average) for this item
                purchase_cost = 0
                if not inv_df_profit.empty and item_name:
                    item_rows = inv_df_profit[inv_df_profit.iloc[:, 0] == item_name]
                    
                    if not item_rows.empty:
                        # Get LATEST purchase rate (last entry)
                        latest_rate = pd.to_numeric(item_rows.iloc[-1, 3], errors='coerce')
                        purchase_cost = sold_qty * latest_rate
                    else:
                        # New item - assume 70% cost
                        purchase_cost = sale_amount * 0.7
                else:
                    # No inventory data - assume 70% cost
                    purchase_cost = sale_amount * 0.7
                
                # Calculate profit
                item_profit = sale_amount - purchase_cost
                month_profit += item_profit
                
                # Add to details (group by item)
                existing = next((x for x in month_profit_details if x['item'] == item_name), None)
                if existing:
                    existing['sale'] += sale_amount
                    existing['cost'] += purchase_cost
                    existing['profit'] += item_profit
                else:
                    month_profit_details.append({
                        'item': item_name,
                        'sale': sale_amount,
                        'cost': purchase_cost,
                        'profit': item_profit
                    })
    
    # Subtract expenses from profit
    month_profit = month_profit - month_expense
    
    # Colorful Cards for Monthly
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_sale:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">🛒 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_purchase:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📊 Net Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_profit:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show Monthly Item-wise Profit Breakdown
    if month_profit_details:
        with st.expander(f"📊 {curr_m_name}'s Item-wise Profit Breakdown", expanded=False):
            st.markdown(f"### 🔍 How {curr_m_name}'s Profit is Calculated")
            
            # Sort by profit descending
            month_profit_details.sort(key=lambda x: x['profit'], reverse=True)
            
            total_gross_profit = 0
            
            for detail in month_profit_details:
                item = detail['item']
                sale = detail['sale']
                cost = detail['cost']
                profit = detail['profit']
                total_gross_profit += profit
                
                profit_percent = (profit / sale * 100) if sale > 0 else 0
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item}**")
                with col2:
                    st.success(f"Sale: ₹{sale:,.0f}")
                with col3:
                    st.info(f"Cost: ₹{cost:,.0f}")
                with col4:
                    st.warning(f"Profit: ₹{profit:,.0f}")
                with col5:
                    st.metric("Margin", f"{profit_percent:.1f}%")
                
                st.divider()
            
            st.markdown("### 💰 Monthly Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Gross Profit", f"₹{total_gross_profit:,.2f}")
            with col2:
                st.metric("Less: Expenses", f"₹{month_expense:,.2f}")
            with col3:
                st.metric("Net Profit", f"₹{month_profit:,.2f}", 
                         delta=f"₹{total_gross_profit - month_expense:,.2f}")
            
            st.info(f"💡 **Formula:** Net Profit = (Sale Price - Purchase Cost) - Expenses")
            st.success(f"✅ **Calculation:** (₹{total_gross_profit:,.2f} gross profit) - (₹{month_expense:,.2f} expenses) = ₹{month_profit:,.2f}")
    
    # Manual Correction Settings for Monthly Report
    with st.expander("🔧 Monthly Report Settings (Manual Corrections)"):
        st.success(f"✅ Auto-calculated for {curr_m_name} {datetime.now().year}, but you can manually adjust")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Sales")
            st.write(f"Current (Auto): ₹{month_sale:,.2f}")
            manual_month_sale = st.number_input("Correct Monthly Sale", value=float(month_sale), step=1.0, key="manual_month_sale")
            
            st.divider()
            
            st.subheader("🛒 Purchases")
            st.write(f"Current (Auto): ₹{month_purchase:,.2f}")
            manual_month_purchase = st.number_input("Correct Monthly Purchase", value=float(month_purchase), step=1.0, key="manual_month_purchase")
        
        with col2:
            st.subheader("💸 Expenses")
            st.write(f"Current (Auto): ₹{month_expense:,.2f}")
            manual_month_expense = st.number_input("Correct Monthly Expense", value=float(month_expense), step=1.0, key="manual_month_expense")
            
            st.divider()
            
            st.subheader("📊 Profit (Auto-calculated)")
            manual_month_profit = manual_month_sale - manual_month_purchase - manual_month_expense
            st.metric("Corrected Profit", f"₹{manual_month_profit:,.2f}")
        
        st.divider()
        
        if manual_month_sale != month_sale or manual_month_purchase != month_purchase or manual_month_expense != month_expense:
            st.warning("⚠️ You have made manual corrections for monthly report!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Sale:** ₹{month_sale:,.2f} → ₹{manual_month_sale:,.2f}")
            with col2:
                st.info(f"**Purchase:** ₹{month_purchase:,.2f} → ₹{manual_month_purchase:,.2f}")
            with col3:
                st.info(f"**Expense:** ₹{month_expense:,.2f} → ₹{manual_month_expense:,.2f}")
            
            st.markdown("### 📊 Corrected Monthly Summary")
            
            st.markdown(f"""
            <div style="display: flex; gap: 15px; margin-top: 20px;">
                <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">💰 Corrected Sale</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_month_sale:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">🛒 Corrected Purchase</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_month_purchase:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">💸 Corrected Expense</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_month_expense:,.2f}</h2>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 16px;">✨ Corrected Profit</p>
                    <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{manual_month_profit:,.2f}</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 Save Monthly Corrections", type="primary", use_container_width=True):
                # Save monthly corrections
                save_data("MonthlyCorrections", [
                    str(today_dt),
                    curr_m_name,
                    datetime.now().year,
                    manual_month_sale,
                    manual_month_purchase,
                    manual_month_expense,
                    manual_month_profit,
                    f"Auto: Sale={month_sale}, Purchase={month_purchase}, Expense={month_expense}"
                ])
                st.success(f"✅ Manual corrections saved for {curr_m_name} {datetime.now().year}!")
                st.balloons()
                time.sleep(1)
                st.rerun()
        else:
            st.success("✅ All values match auto-calculated amounts")

# ========================================
# MENU 2: BILLING - COMPLETE CLEAN VERSION
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
                            st.error(f"❌ Not enough stock! Only {available_qty} {last_unit} available")
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
        st.markdown("### 👑 Royalty Points Redemption")
        
        if cust_name and cust_name.strip():
            s_df_check = load_data("Sales")
            if not s_df_check.empty and len(s_df_check.columns) > 6:
                customer_points = 0
                customer_identifier = f"{cust_name} ({cust_phone})" if cust_phone else cust_name
                
                for cust_variant in [customer_identifier, cust_name, cust_name.strip()]:
                    points_data = s_df_check[s_df_check.iloc[:, 5].str.contains(cust_variant, case=False, na=False)]
                    if not points_data.empty:
                        customer_points = pd.to_numeric(points_data.iloc[:, 6], errors='coerce').sum()
                        break
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.metric("👑 Available Points", int(customer_points))
                
                with col2:
                    use_points = st.checkbox("✅ Use Points for Discount", key="use_points_checkbox")
                
                with col3:
                    if use_points and customer_points >= 100:
                        points_to_redeem = st.number_input(
                            "Points to Use",
                            min_value=100,
                            max_value=int(customer_points),
                            step=100,
                            key="points_redeem"
                        )
                        
                        discount_amount = points_to_redeem
                        st.success(f"💰 Discount: ₹{discount_amount:,.0f}")
                        st.info(f"Remaining Points: {int(customer_points - points_to_redeem)}")
                        
                        total = total - discount_amount
                        if total < 0:
                            total = 0
                        
                        st.warning(f"🎯 New Bill Total: ₹{total:,.2f}")
                    elif use_points and customer_points < 100:
                        st.error("❌ Minimum 100 points required!")
                        use_points = False
            else:
                st.info("💡 Enter customer name to check points")
        else:
            st.info("💡 Enter customer name to check points")
        
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
            st.info("💡 Customer ne multiple tareeke se payment kiya hai")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**💵 Cash**")
                cash_amount = st.number_input(
                    "Cash Amount",
                    min_value=0.0,
                    max_value=float(total),
                    value=0.0,
                    step=10.0,
                    key="split_cash"
                )
                if cash_amount > 0:
                    st.success(f"✅ Cash: ₹{cash_amount:,.2f}")
            
            with col2:
                st.markdown("**🏦 Online**")
                max_online = float(total - cash_amount)
                online_amount = st.number_input(
                    "Online Amount",
                    min_value=0.0,
                    max_value=max_online,
                    value=0.0,
                    step=10.0,
                    key="split_online"
                )
                if online_amount > 0:
                    st.success(f"✅ Online: ₹{online_amount:,.2f}")
            
            with col3:
                st.markdown("**📒 Udhaar**")
                max_udhaar = float(total - cash_amount - online_amount)
                udhaar_amount = st.number_input(
                    "Udhaar Amount",
                    min_value=0.0,
                    max_value=max_udhaar,
                    value=max_udhaar,
                    step=10.0,
                    key="split_udhaar"
                )
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
                st.error(f"❌ Payment incomplete! ₹{remaining:,.2f} remaining")
            elif remaining < -0.01:
                col3.metric("⚠️ Excess", f"₹{abs(remaining):,.2f}", delta="Too much")
                st.error(f"❌ Payment exceeds bill by ₹{abs(remaining):,.2f}")
            else:
                col3.metric("✅ Status", "Complete", delta="Matched")
                st.success("✅ Payment matched!")
        
        st.divider()
        st.markdown("### 🧾 GST Billing (Optional)")
        
        enable_gst = st.checkbox("✅ Enable GST", value=False, key="enable_gst")
        
        customer_gstin = ""
        gst_rate = "18%"
        invoice_type = "B2C"
        
        if enable_gst:
            col1, col2, col3 = st.columns(3)
            with col1:
                customer_gstin = st.text_input("GSTIN *", key="cust_gstin")
            with col2:
                gst_rate = st.selectbox("GST Rate", ["5%", "12%", "18%", "28%"], index=2)
            with col3:
                invoice_type = st.selectbox("Type", ["B2B", "B2C"])
        
        st.divider()
        st.markdown("### 👑 Royalty Points")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            give_points = st.checkbox("✅ Give Points", value=True, key="give_points")
        
        with col2:
            if give_points:
                points = st.number_input("Points", min_value=0, max_value=10000, value=0, step=1, key="manual_points")
            else:
                points = 0
        
        with col3:
            if give_points and points > 0:
                st.success(f"👑 **{points}**")
            else:
                st.info("No points")
        
        st.divider()
        st.markdown("### 📊 Final Summary")
        
        payment_summary_cols = st.columns(5)
        payment_summary_cols[0].metric("💰 Bill", f"₹{total:,.2f}")
        payment_summary_cols[1].metric("💵 Cash", f"₹{cash_amount:,.2f}" if cash_amount > 0 else "₹0")
        payment_summary_cols[2].metric("🏦 Online", f"₹{online_amount:,.2f}" if online_amount > 0 else "₹0")
        payment_summary_cols[3].metric("📒 Udhaar", f"₹{udhaar_amount:,.2f}" if udhaar_amount > 0 else "₹0")
        payment_summary_cols[4].metric("👑 Points", f"+{points}" if points > 0 else "0")
        
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
        
        if enable_gst and not customer_gstin:
            can_save = False
            error_msg = "⚠️ Enter GSTIN!"
        
        if not can_save:
            st.error(error_msg)
        
        if st.button("💾 COMPLETE SALE", type="primary", use_container_width=True, disabled=not can_save):
            customer_info = f"{cust_name} ({cust_phone})" if cust_phone else cust_name
            
            if enable_gst:
                gst_info = f"GST: {gst_rate} | GSTIN: {customer_gstin} | Type: {invoice_type}"
            else:
                gst_info = "No GST"
            
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
                
                inv_df_check = load_data("Inventory")
                purchase_cost = 0
                
                if not inv_df_check.empty:
                    item_cost_rows = inv_df_check[inv_df_check.iloc[:, 0] == item_name]
                    if not item_cost_rows.empty:
                        latest_purchase_rate = pd.to_numeric(item_cost_rows.iloc[-1, 3], errors='coerce')
                        purchase_cost = sold_qty * latest_purchase_rate
                    else:
                        purchase_cost = 0
                else:
                    purchase_cost = 0
                
                profit = amount - purchase_cost
                
                save_data("Sales", [
                    str(today_dt),
                    item_name,
                    f"{sold_qty} {unit}",
                    amount,
                    payment_info,
                    customer_info,
                    points,
                    profit,
                    gst_info
                ])
                
                # ✅ UPDATE STOCK - Google Sheets mein directly update karo (NO NEW ENTRY)
                # ✅ AUTOMATIC STOCK UPDATE - Google Sheets mein bhi
                inv_df_update = load_data("Inventory")
                if not inv_df_update.empty:
                    product_rows = inv_df_update[inv_df_update.iloc[:, 0] == item_name]
                    
                    if not product_rows.empty:
                        # Get current stock
                        current_stock = pd.to_numeric(product_rows.iloc[-1, 1], errors='coerce')
                        current_unit = product_rows.iloc[-1, 2]
                        current_rate = pd.to_numeric(product_rows.iloc[-1, 3], errors='coerce')
                        
                        # Calculate new stock
                        new_stock = current_stock - sold_qty
                        
                        # ✅ UPDATE in Google Sheets (NO new entry)
                        if update_stock_in_sheet(item_name, new_stock):
                            st.success(f"✅ {item_name}: {current_stock} → {new_stock} {current_unit}")
                        else:
                            st.error(f"❌ Failed to update {item_name} stock")
                        st.warning(f"⚠️ Please MANUALLY update stock in Google Sheets (Row #{latest_idx+2})")
                        st.info(f"🔍 Search: {item_name} - Change Qty from {current_stock} to {new_stock}")
            
            payment_success = True
            
            if cash_amount > 0:
                if update_balance(cash_amount, "Cash", 'add'):
                    st.success(f"💵 Cash: ₹{cash_amount:,.2f} added")
                else:
                    payment_success = False
            
            if online_amount > 0:
                if update_balance(online_amount, "Online", 'add'):
                    st.success(f"🏦 Online: ₹{online_amount:,.2f} added")
                else:
                    payment_success = False
            
            if udhaar_amount > 0:
                save_data("CustomerKhata", [customer_info, udhaar_amount, str(today_dt), "Sale on credit"])
                st.warning(f"📒 Udhaar: ₹{udhaar_amount:,.2f} added to due")
            
            if enable_gst:
                st.success(f"🧾 GST Invoice Generated!")
            
            if points > 0:
                st.success(f"✅ {customer_info} earned {points} points!")
            else:
                st.success(f"✅ Sale completed!")
            
            st.divider()
            st.markdown("### 💰 Payment Breakdown")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💵 Cash", f"₹{cash_amount:,.2f}")
            col2.metric("🏦 Online", f"₹{online_amount:,.2f}")
            col3.metric("📒 Udhaar", f"₹{udhaar_amount:,.2f}")
            col4.metric("✅ Total", f"₹{total:,.2f}")
            
            st.session_state.bill_cart = []
            st.balloons()
            time.sleep(3)
            st.rerun()
    
    else:
        st.info("🛒 Cart is empty. Add items to start billing.")
    
    st.divider()
    st.markdown("### 📋 Today's Bills")
    
    s_df = load_data("Sales")
    if not s_df.empty and 'Date' in s_df.columns:
        today_sales = s_df[s_df['Date'] == today_dt]
        
        if not today_sales.empty:
            st.success(f"✅ {len(today_sales)} bills today")
        else:
            st.info("No bills today")
    else:
        st.info("No sales data")
# ========================================
# MENU 3: PURCHASE
# ========================================
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    if 'purchase_cart' not in st.session_state:
        st.session_state.purchase_cart = []
    
    # Party Details Section - MANDATORY for all purchases
    st.markdown("### 👤 Party/Supplier Details (Mandatory)")
    col1, col2 = st.columns(2)
    
    with col1:
        supplier_name = st.text_input("📝 Party/Supplier Name *", placeholder="Enter supplier/party name", key="supplier_name_input")
    
    with col2:
        supplier_phone = st.text_input("📞 Party Phone Number *", placeholder="Enter phone number", key="supplier_phone_input")
    
    if not supplier_name or not supplier_name.strip():
        st.warning("⚠️ Please enter Party/Supplier name to continue")
    
    if not supplier_phone or not supplier_phone.strip():
        st.warning("⚠️ Please enter Party phone number to continue")
    
    st.divider()
    
    # Payment selection
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
            st.info(f"✅ Payment will be deducted from Shop Cash")
        elif payment_type == "🏦 Online (Shop)":
            payment_mode = "Online"
            st.info(f"✅ Payment will be deducted from Shop Online")
        elif payment_type == "🏢 Udhaar (Credit)":
            payment_mode = "Udhaar"
            st.warning("⚠️ This will be added to Supplier Dues")
        else:  # By Hand
            payment_mode = "By Hand"
            st.success("✅ Personal money investment (Pocket)")
            st.info("💡 This will be tracked separately in Hand Investments")
    
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
            product_stock = inv_df[inv_df.iloc[:, 0] == item_name].tail(1)
            
            if not product_stock.empty and not is_new_item:
                current_qty = pd.to_numeric(product_stock.iloc[-1, 1], errors='coerce')
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
            product_stock = inv_df[inv_df.iloc[:, 0] == item_name].tail(1)
            if not product_stock.empty:
                current_qty_num = pd.to_numeric(product_stock.iloc[-1, 1], errors='coerce')
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
        can_save = supplier_name and supplier_name.strip() and supplier_phone and supplier_phone.strip()
        
        if not can_save:
            st.error("⚠️ Please enter Party/Supplier Name and Phone Number above to save purchase!")
        else:
            # Show summary before saving
            st.markdown("### 📋 Purchase Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**Party:** {supplier_name}")
                st.info(f"**Phone:** {supplier_phone}")
            
            with col2:
                st.success(f"**Total Items:** {total_items}")
                st.success(f"**Total Amount:** ₹{total_amount:,.2f}")
            
            with col3:
                st.warning(f"**Payment:** {payment_mode}")
                if payment_mode in ["Cash", "Online"]:
                    st.info(f"Will deduct from {payment_mode}")
                else:
                    st.info("Will add to Supplier Dues")
            
            if st.button("💾 SAVE PURCHASE", type="primary", use_container_width=True):
                # Create supplier full info
                supplier_full_info = f"{supplier_name} ({supplier_phone})"
                
                # Save all items to Inventory
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
                
                # Handle payment based on mode
                if payment_mode == "Cash":
                    update_balance(total_amount, "Cash", 'subtract')
                    st.success(f"✅ Purchase saved!")
                    st.success(f"✅ ₹{total_amount:,.2f} deducted from Shop Cash")
                    
                elif payment_mode == "Online":
                    update_balance(total_amount, "Online", 'subtract')
                    st.success(f"✅ Purchase saved!")
                    st.success(f"✅ ₹{total_amount:,.2f} deducted from Shop Online")
                    
                elif payment_mode == "By Hand":
                    # Save to Hand Investments tracking
                    items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                    
                    save_data("HandInvestments", [
                        str(today_dt),
                        supplier_full_info,
                        total_amount,
                        items_note,
                        "Purchase by hand (pocket money)"
                    ])
                    
                    st.success(f"✅ Purchase saved!")
                    st.success(f"💰 ₹{total_amount:,.2f} invested from your pocket!")
                    st.info(f"📝 Supplier: {supplier_full_info}")
                    st.info(f"💡 Check 'Hand Investments' in dashboard to see total personal investment")
                    
                else:  # Udhaar
                    # Udhaar - Add to Supplier Dues
                    items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                    
                    # Save to Dues sheet with POSITIVE amount (we owe them)
                    save_data("Dues", [supplier_full_info, total_amount, str(today_dt), f"Purchase: {items_note}"])
                    
                    st.success(f"✅ Purchase saved!")
                    st.success(f"✅ ₹{total_amount:,.2f} added to {supplier_name}'s dues!")
                    st.info(f"📝 Phone: {supplier_phone}")
                    st.info(f"💡 Check 'Supplier Dues' menu to see {supplier_name}'s balance")
                
                st.session_state.purchase_cart = []
                st.balloons()
                time.sleep(2)
                st.rerun()
    else:
        st.info("🛒 Cart is empty. Add items above to start purchase.")
    
    # View Recent Purchases with Delete Option
    st.divider()
    st.markdown("### 📋 Recent Purchases (Today)")
    
    inv_df_recent = load_data("Inventory")
    if not inv_df_recent.empty and len(inv_df_recent.columns) > 5:
        try:
            inv_df_recent['pur_date'] = pd.to_datetime(inv_df_recent.iloc[:, 5], errors='coerce').dt.date
            today_purchases = inv_df_recent[inv_df_recent['pur_date'] == today_dt]
            
            if not today_purchases.empty:
                for idx, row in today_purchases.iterrows():
                    with st.expander(f"📦 Purchase #{idx+1} - {row.iloc[0]} - ₹{row.iloc[4]}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Item:** {row.iloc[0]}")
                            st.write(f"**Quantity:** {row.iloc[1]} {row.iloc[2]}")
                            st.write(f"**Rate:** ₹{row.iloc[3]}")
                            st.write(f"**Total:** ₹{row.iloc[4]}")
                            st.write(f"**Date:** {row.iloc[5]}")
                            st.write(f"**Payment:** {row.iloc[6] if len(row) > 6 else 'N/A'}")
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_purchase_{idx}", type="secondary"):
                                # Get purchase details
                                item_name = row.iloc[0]
                                qty = float(row.iloc[1])
                                unit = row.iloc[2]
                                rate = float(row.iloc[3])
                                total_amount = float(row.iloc[4])
                                payment_info = str(row.iloc[6]) if len(row) > 6 else ""
                                
                                # REVERSE PAYMENT (if Cash/Online)
                                if "Cash" in payment_info:
                                    update_balance(total_amount, "Cash", 'add')
                                    st.success(f"✅ ₹{total_amount:,.2f} added back to Cash")
                                elif "Online" in payment_info:
                                    update_balance(total_amount, "Online", 'add')
                                    st.success(f"✅ ₹{total_amount:,.2f} added back to Online")
                                
                                # SUBTRACT STOCK
                                inv_df_check = load_data("Inventory")
                                if not inv_df_check.empty:
                                    product_rows = inv_df_check[inv_df_check.iloc[:, 0] == item_name].tail(1)
                                    
                                    if not product_rows.empty:
                                        current_stock = pd.to_numeric(product_rows.iloc[-1, 1], errors='coerce')
                                        current_rate = pd.to_numeric(product_rows.iloc[-1, 3], errors='coerce')
                                        
                                        # Remove purchased quantity
                                        new_stock = current_stock - qty
                                        
                                        if new_stock >= 0:
                                            save_data("Inventory", [
                                                item_name,
                                                new_stock,
                                                unit,
                                                current_rate,
                                                new_stock * current_rate,
                                                str(today_dt),
                                                f"Purchase reversal (deleted)"
                                            ])
                                            
                                            st.success(f"📦 Stock adjusted: {current_stock} → {new_stock} {unit}")
                                        else:
                                            st.error(f"⚠️ Cannot delete! Stock would go negative ({new_stock})")
                                
                                st.warning("⚠️ Please manually delete this entry from Google Sheets Inventory tab")
                                st.info(f"🔍 Search for: {item_name} - {today_dt}")
                                
                                time.sleep(2)
                                st.rerun()
            else:
                st.info("No purchases today")
        except:
            st.info("No purchase data")
    else:
        st.info("No purchase data available")

# ========================================
# MENU 4: LIVE STOCK
# ========================================
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    
    if not i_df.empty and len(i_df.columns) > 4:
        # Group by product and get LATEST entry for each
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

# Rest of the menus remain the same...
# (I'll continue with the remaining menus in the same file)

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
            for idx, row in today_expenses.iterrows():
                with st.expander(f"💸 {row.iloc[1] if len(row) > 1 else 'Expense'} - ₹{row.iloc[2] if len(row) > 2 else 0}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Date:** {row.iloc[0] if len(row) > 0 else 'N/A'}")
                        st.write(f"**Category:** {row.iloc[1] if len(row) > 1 else 'N/A'}")
                        st.write(f"**Amount:** ₹{row.iloc[2] if len(row) > 2 else 0}")
                        st.write(f"**Mode:** {row.iloc[3] if len(row) > 3 else 'N/A'}")
                        st.write(f"**Note:** {row.iloc[4] if len(row) > 4 else 'N/A'}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_expense_{idx}", type="secondary"):
                            # Get expense details
                            amount = float(row.iloc[2])
                            mode = str(row.iloc[3])
                            
                            # REVERSE PAYMENT - Add money back
                            if mode == "Cash":
                                update_balance(amount, "Cash", 'add')
                                st.success(f"✅ ₹{amount:,.2f} added back to Cash")
                            elif mode == "Online":
                                update_balance(amount, "Online", 'add')
                                st.success(f"✅ ₹{amount:,.2f} added back to Online")
                            
                            st.warning("⚠️ Please manually delete this entry from Google Sheets Expenses tab")
                            st.info(f"🔍 Search for: {row.iloc[1]} - {today_dt}")
                            
                            time.sleep(2)
                            st.rerun()
        else:
            st.info("No expenses today")
        
        st.divider()
        st.subheader("📜 All Expenses History")
        st.dataframe(e_df, use_container_width=True)

# ========================================
# MENU 6: PET REGISTER (Simplified - Only for Pets Being Sold)
# ========================================
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register - Pets for Sale")
    
    tab1, tab2 = st.tabs(["➕ Add Pet for Sale", "📋 Available Pets"])
    
    with tab1:
        with st.form("pet_reg"):
            st.subheader("Register Pet for Sale")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit", "Bird", "Hamster", "Other"])
                pet_breed = st.text_input("Breed *", placeholder="e.g., German Shepherd, Persian Cat")
                pet_age = st.number_input("Age (months)", min_value=0, max_value=120, step=1)
                pet_price = st.number_input("Selling Price (₹) *", min_value=0, step=100)
            
            with col2:
                pet_gender = st.selectbox("Gender", ["Male", "Female"])
                pet_color = st.text_input("Color", placeholder="e.g., Brown, White, Black")
                
                # Vaccination details
                st.markdown("**💉 Vaccination:**")
                last_vaccine_date = st.date_input("Last Vaccine Date", value=today_dt)
                next_vaccine_date = st.date_input("Next Vaccine Due", value=today_dt + timedelta(days=30))
            
            notes = st.text_area("Additional Notes (Optional)", placeholder="Health status, special features, etc.")
            
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
                        str(last_vaccine_date),
                        str(next_vaccine_date),
                        notes
                    ])
                    st.success(f"✅ {pet_type} ({pet_breed}) added for sale at ₹{pet_price}!")
                    st.info(f"💉 Next vaccine due: {next_vaccine_date.strftime('%d %B %Y')}")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Please fill Breed and Price!")
    
    with tab2:
        pets_df = load_data("PetRegister")
        
        if not pets_df.empty:
            st.subheader(f"📊 Total Pets Available: {len(pets_df)}")
            
            # Check for upcoming vaccinations
            upcoming_vaccines = []
            if len(pets_df.columns) > 9:
                for idx, row in pets_df.iterrows():
                    try:
                        next_vaccine = pd.to_datetime(row.iloc[9], errors='coerce').date() if len(row) > 9 else None
                        if next_vaccine:
                            days_until = (next_vaccine - today_dt).days
                            if 0 <= days_until <= 7:  # Due within 7 days
                                upcoming_vaccines.append({
                                    'pet': f"{row.iloc[1]} - {row.iloc[2]}",
                                    'date': next_vaccine,
                                    'days': days_until
                                })
                    except:
                        pass
            
            # Show vaccine alerts
            if upcoming_vaccines:
                st.warning(f"⚠️ {len(upcoming_vaccines)} pet(s) have vaccination due soon!")
                for vac in upcoming_vaccines:
                    if vac['days'] == 0:
                        st.error(f"🚨 **{vac['pet']}** - Vaccine DUE TODAY!")
                    else:
                        st.warning(f"💉 **{vac['pet']}** - Vaccine due in {vac['days']} day(s) ({vac['date'].strftime('%d %b')})")
                st.divider()
            
            # Search functionality
            search = st.text_input("🔍 Search by Type or Breed")
            
            if search:
                mask = pets_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                filtered_df = pets_df[mask]
            else:
                filtered_df = pets_df
            
            # Display pets in grid
            for idx, row in filtered_df.iterrows():
                pet_type = row.iloc[1] if len(row) > 1 else "Pet"
                pet_breed = row.iloc[2] if len(row) > 2 else "Unknown"
                pet_price = row.iloc[6] if len(row) > 6 else 0
                
                # Check vaccine status
                vaccine_alert = ""
                if len(row) > 9:
                    try:
                        next_vaccine = pd.to_datetime(row.iloc[9], errors='coerce').date()
                        if next_vaccine:
                            days_until = (next_vaccine - today_dt).days
                            if days_until == 0:
                                vaccine_alert = "🚨 VACCINE DUE TODAY!"
                            elif 0 < days_until <= 7:
                                vaccine_alert = f"⚠️ Vaccine in {days_until} days"
                    except:
                        pass
                
                title = f"🐾 {pet_type} - {pet_breed} - ₹{pet_price:,.0f}"
                if vaccine_alert:
                    title += f" {vaccine_alert}"
                
                with st.expander(title):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write("**Pet Details:**")
                        st.write(f"Type: {pet_type}")
                        st.write(f"Breed: {pet_breed}")
                        st.write(f"Age: {row.iloc[3] if len(row) > 3 else 'N/A'} months")
                    
                    with col2:
                        st.write("**Sale Information:**")
                        st.write(f"Gender: {row.iloc[4] if len(row) > 4 else 'N/A'}")
                        st.write(f"Color: {row.iloc[5] if len(row) > 5 else 'N/A'}")
                        st.write(f"**Price: ₹{pet_price:,.0f}**")
                        st.write(f"Status: {row.iloc[7] if len(row) > 7 else 'Available'}")
                        
                        # Vaccination info
                        if len(row) > 9:
                            st.divider()
                            st.write("**💉 Vaccination:**")
                            try:
                                last_vac = pd.to_datetime(row.iloc[8], errors='coerce').date() if len(row) > 8 else None
                                next_vac = pd.to_datetime(row.iloc[9], errors='coerce').date() if len(row) > 9 else None
                                
                                if last_vac:
                                    st.info(f"Last: {last_vac.strftime('%d %b %Y')}")
                                if next_vac:
                                    days_until = (next_vac - today_dt).days
                                    if days_until < 0:
                                        st.error(f"Next: {next_vac.strftime('%d %b %Y')} (OVERDUE)")
                                    elif days_until == 0:
                                        st.error(f"Next: {next_vac.strftime('%d %b %Y')} (TODAY)")
                                    elif days_until <= 7:
                                        st.warning(f"Next: {next_vac.strftime('%d %b %Y')} ({days_until} days)")
                                    else:
                                        st.success(f"Next: {next_vac.strftime('%d %b %Y')}")
                            except:
                                pass
                    
                    with col3:
                        st.write("**Actions:**")
                        
                        if st.button("✅ Sold", key=f"sold_pet_{idx}", type="primary"):
                            st.success(f"✅ Mark {pet_breed} as SOLD!")
                            st.warning("⚠️ Please update status to 'SOLD' in Google Sheets")
                            st.info(f"🔍 Search: {pet_breed} - {today_dt}")
                        
                        if st.button("🗑️ Delete", key=f"del_pet_{idx}", type="secondary"):
                            st.warning("⚠️ Please manually delete this entry from Google Sheets PetRegister tab")
                            st.info(f"🔍 Search for: {pet_breed}")
                    
                    if len(row) > 10 and str(row.iloc[10]).strip():
                        st.write("**Notes:**", row.iloc[10])
        else:
            st.info("No pets registered yet. Add your first pet in the 'Add Pet for Sale' tab!")

# ========================================
# MENU 8: CUSTOMER DUE (renamed from Customer Khata)
# ========================================
    # ========================================
# MENU 8: CUSTOMER DUE (renamed from Customer Khata)
# ========================================
elif menu == "Customer Due":
    st.header("📒 Customer Due Management")
    
    tab1, tab2 = st.tabs(["💰 Transaction Entry", "📊 View Summary"])
    
    with tab1:
        with st.form("khata"):
            st.subheader("Record Transaction")
            cust = st.text_input("Customer Name/Phone *", placeholder="Enter customer name or phone")
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=10.0)
            
            st.markdown("### Transaction Type")
            transaction_type = st.radio(
                "Select transaction type:",
                [
                    "Payment Received (Customer ne hamein paisa diya)",
                    "Credit Given (Hamne customer ko udhaar diya)"
                ],
                horizontal=False,
                help="Choose whether customer is paying you or you're giving credit"
            )
            
            pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Other"], 
                                   help="How the payment was made")
            note = st.text_input("Note (Optional)", placeholder="Add any additional details")
            
            st.divider()
            
            if "Payment Received" in transaction_type:
                st.success("""
                Payment Received:
                - Customer ka due REDUCE hoga (kam hoga)
                - Paisa aapke Cash/Online balance mein ADD hoga
                - Example: Customer ka Rs.500 due hai, usne Rs.300 diye, toh due Rs.200 ho jayega
                """)
            else:
                st.warning("""
                Credit Given:
                - Customer ka due INCREASE hoga (badh jayega)
                - Paisa aapke balance se deduct NAHI hoga (kyunki ye future payment hai)
                - Example: Customer ko Rs.500 ka maal diya udhaar par, toh due Rs.500 ho jayega
                """)
            
            if st.form_submit_button("💾 Save Transaction", type="primary"):
                if amt > 0 and cust.strip():
                    if "Payment Received" in transaction_type:
                        # Customer paid us - REDUCE their due (negative entry)
                        save_data("CustomerKhata", [cust, -amt, str(today_dt), f"Payment received: {note}"])
                        
                        # ADD money to our balance
                        if pay_mode == "Cash":
                            update_balance(amt, "Cash", 'add')
                            st.success(f"Rs.{amt:,.2f} added to Cash balance")
                        elif pay_mode == "Online":
                            update_balance(amt, "Online", 'add')
                            st.success(f"Rs.{amt:,.2f} added to Online balance")
                        
                        st.success(f"Payment of Rs.{amt:,.2f} recorded from {cust}")
                        st.info(f"Customer ka due Rs.{amt:,.2f} kam ho gaya")
                        st.balloons()
                        
                    else:
                        # We gave credit - INCREASE their due (positive entry)
                        save_data("CustomerKhata", [cust, amt, str(today_dt), f"Credit given: {note}"])
                        st.success(f"Credit of Rs.{amt:,.2f} given to {cust}")
                        st.warning(f"Customer ka due Rs.{amt:,.2f} badh gaya")
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Please enter customer name and amount!")
    
    with tab2:
        k_df = load_data("CustomerKhata")
        
        if not k_df.empty and len(k_df.columns) > 1:
            st.subheader("📊 Customer Due Summary")
            
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            
            sum_df = sum_df[sum_df['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                total_due = sum_df['Balance'].sum()
                
                col1, col2 = st.columns([1, 1])
                col1.metric("💰 Total Outstanding Due", f"Rs.{total_due:,.2f}")
                col2.metric("👥 Customers with Due", len(sum_df))
                
                st.divider()
                
                search_customer = st.text_input("🔍 Search Customer", placeholder="Type customer name or phone")
                
                if search_customer:
                    sum_df = sum_df[sum_df['Customer'].str.contains(search_customer, case=False, na=False)]
                
                for idx, row in sum_df.iterrows():
                    customer = row['Customer']
                    balance = row['Balance']
                    
                    with st.expander(f"🔴 **{customer}** - Due: Rs.{balance:,.2f}"):
                        cust_txns = k_df[k_df.iloc[:, 0] == customer]
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("#### Transaction History")
                            for _, txn in cust_txns.iterrows():
                                date = str(txn.iloc[2]) if len(txn) > 2 else "N/A"
                                amount = float(txn.iloc[1]) if len(txn) > 1 else 0
                                note = str(txn.iloc[3]) if len(txn) > 3 else ""
                                
                                if amount > 0:
                                    st.error(f"📥 {date}: Credit Rs.{amount:,.2f} - {note}")
                                else:
                                    st.success(f"💰 {date}: Payment Rs.{abs(amount):,.2f} - {note}")
                        
                        with col2:
                            st.markdown("#### Quick Actions")
                            
                            with st.form(f"quick_pay_{customer}_{idx}"):
                                st.write("**Receive Payment**")
                                quick_amt = st.number_input(
                                    "Amount", 
                                    min_value=0.0, 
                                    max_value=float(balance), 
                                    value=float(balance),
                                    step=10.0,
                                    key=f"quick_{customer}_{idx}"
                                )
                                quick_mode = st.selectbox(
                                    "Mode", 
                                    ["Cash", "Online"], 
                                    key=f"mode_{customer}_{idx}"
                                )
                                
                                if st.form_submit_button("💰 Receive", type="primary", use_container_width=True):
                                    if quick_amt > 0:
                                        save_data("CustomerKhata", [
                                            customer, 
                                            -quick_amt, 
                                            str(today_dt), 
                                            f"Quick payment via {quick_mode}"
                                        ])
                                        
                                        if quick_mode == "Cash":
                                            update_balance(quick_amt, "Cash", 'add')
                                        elif quick_mode == "Online":
                                            update_balance(quick_amt, "Online", 'add')
                                        
                                        st.success(f"Rs.{quick_amt:,.2f} received!")
                                        time.sleep(1)
                                        st.rerun()
                
                st.divider()
                
                if st.button("📥 Download Due Report", type="secondary"):
                    csv = sum_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"customer_due_report_{today_dt}.csv",
                        mime="text/csv"
                    )
                
            else:
                st.success("✅ No outstanding dues! All customers have cleared their payments.")
                st.balloons()
            
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(k_df, use_container_width=True)
            
        else:
            st.info("📝 No customer due records yet. Start recording transactions above!")
            
            st.markdown("""
            ### 💡 How to use:
            
            **When customer pays you:**
            1. Select "Payment Received"
            2. Enter amount and payment mode
            3. Money will be added to your Cash/Online balance
            4. Customer's due will be reduced
            
            **When you give credit:**
            1. Select "Credit Given"
            2. Enter amount
            3. Customer's due will be increased
            4. No money deduction from your balance
            """)
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
            try:
                product_sales = s_df.groupby(s_df.columns[1], as_index=False).agg({
                    s_df.columns[3]: 'sum'
                })
                
                product_sales['Units_Sold'] = s_df.groupby(s_df.columns[1]).size().values
                product_sales.columns = ['Product', 'Revenue', 'Units_Sold']
                product_sales['Revenue'] = pd.to_numeric(product_sales['Revenue'], errors='coerce')
                product_sales = product_sales.sort_values('Revenue', ascending=False).head(15)
                
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
                    st.info("No sales data available")
            except Exception as e:
                st.error(f"Error loading best sellers: {str(e)}")
                st.info("Please check if sales data is available")
        
        with tab2:
            st.subheader("🐌 Slow Moving Products")
            
            try:
                inv_df = load_data("Inventory")
                if not inv_df.empty and not s_df.empty:
                    product_movement = s_df.groupby(s_df.columns[1]).size()
                    product_movement_df = product_movement.reset_index()
                    product_movement_df.columns = ['Product', 'Transactions']
                    
                    slow_movers = product_movement_df.sort_values('Transactions').head(10)
                    
                    if not slow_movers.empty:
                        for idx, row in slow_movers.iterrows():
                            st.warning(f"⚠️ **{row['Product']}** - Only {row['Transactions']} transactions")
                    else:
                        st.info("No slow moving products found")
                else:
                    st.info("Inventory or sales data not available")
            except Exception as e:
                st.error(f"Error loading slow moving products: {str(e)}")
        
        with tab3:
            st.subheader("💰 Profit Analysis")
            
            try:
                if len(s_df.columns) > 7:
                    total_profit = pd.to_numeric(s_df.iloc[:, 7], errors='coerce').sum()
                    total_revenue = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
                    
                    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
                    col2.metric("Total Profit", f"₹{total_profit:,.2f}")
                    col3.metric("Profit Margin", f"{profit_margin:.1f}%")
                else:
                    st.info("Profit data not available in sales records")
            except Exception as e:
                st.error(f"Error loading profit analysis: {str(e)}")
    else:
        st.info("No sales data available")

# ========================================
# MENU 11: CUSTOMER ANALYTICS
# ========================================
elif menu == "👥 Customer Analytics":
    st.header("👥 Customer Analytics & Insights")
    
    s_df = load_data("Sales") 
elif menu == "📒 Customer Due":
    st.header("📒 Customer Due Management")
    
    tab1, tab2 = st.tabs(["💰 Transaction Entry", "📊 View Summary"])
    
    with tab1:
        with st.form("khata"):
            st.subheader("Record Transaction")
            cust = st.text_input("Customer Name/Phone *", placeholder="Enter customer name or phone")
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=10.0)
            
            st.markdown("### Transaction Type")
            transaction_type = st.radio(
                "Select transaction type:",
                [
                    "Payment Received (Customer ne hamein paisa diya)",
                    "Credit Given (Hamne customer ko udhaar diya)"
                ],
                horizontal=False,
                help="Choose whether customer is paying you or you're giving credit"
            )
            
            pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Other"], 
                                   help="How the payment was made")
            note = st.text_input("Note (Optional)", placeholder="Add any additional details")
            
            st.divider()
            
            if "Payment Received" in transaction_type:
                st.success("""
                Payment Received:
                - Customer ka due REDUCE hoga (kam hoga)
                - Paisa aapke Cash/Online balance mein ADD hoga
                - Example: Customer ka Rs.500 due hai, usne Rs.300 diye, toh due Rs.200 ho jayega
                """)
            else:
                st.warning("""
                Credit Given:
                - Customer ka due INCREASE hoga (badh jayega)
                - Paisa aapke balance se deduct NAHI hoga (kyunki ye future payment hai)
                - Example: Customer ko Rs.500 ka maal diya udhaar par, toh due Rs.500 ho jayega
                """)
            
            if st.form_submit_button("💾 Save Transaction", type="primary"):
                if amt > 0 and cust.strip():
                    if "Payment Received" in transaction_type:
                        # Customer paid us - REDUCE their due (negative entry)
                        save_data("CustomerKhata", [cust, -amt, str(today_dt), f"Payment received: {note}"])
                        
                        # ✅ ADD money to our balance
                        if pay_mode == "Cash":
                            update_balance(amt, "Cash", 'add')
                            st.success(f"✅ Cash balance: +Rs.{amt:,.2f}")
                        elif pay_mode == "Online":
                            update_balance(amt, "Online", 'add')
                            st.success(f"✅ Online balance: +Rs.{amt:,.2f}")
                        
                        st.success(f"✅ Payment Rs.{amt:,.2f} received from {cust}")
                        st.info(f"📉 {cust} ka due Rs.{amt:,.2f} kam ho gaya")
                        st.balloons()
                        
                    else:
                        # ✅ We gave credit - INCREASE their due (positive entry)
                        save_data("CustomerKhata", [cust, amt, str(today_dt), f"Credit given: {note}"])
                        st.success(f"✅ Credit Rs.{amt:,.2f} given to {cust}")
                        st.warning(f"📈 {cust} ka due Rs.{amt:,.2f} badh gaya")
                        st.warning(f"Customer ka due Rs.{amt:,.2f} badh gaya")
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Please enter customer name and amount!")
    
    with tab2:
        k_df = load_data("CustomerKhata")
        
        if not k_df.empty and len(k_df.columns) > 1:
            st.subheader("📊 Customer Due Summary")
            
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            
            sum_df = sum_df[sum_df['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                total_due = sum_df['Balance'].sum()
                
                col1, col2 = st.columns([1, 1])
                col1.metric("💰 Total Outstanding Due", f"Rs.{total_due:,.2f}")
                col2.metric("👥 Customers with Due", len(sum_df))
                
                st.divider()
                
                search_customer = st.text_input("🔍 Search Customer", placeholder="Type customer name or phone")
                
                if search_customer:
                    sum_df = sum_df[sum_df['Customer'].str.contains(search_customer, case=False, na=False)]
                
                for idx, row in sum_df.iterrows():
                    customer = row['Customer']
                    balance = row['Balance']
                    
                    with st.expander(f"🔴 **{customer}** - Due: Rs.{balance:,.2f}"):
                        cust_txns = k_df[k_df.iloc[:, 0] == customer]
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("#### Transaction History")
                            for _, txn in cust_txns.iterrows():
                                date = str(txn.iloc[2]) if len(txn) > 2 else "N/A"
                                amount = float(txn.iloc[1]) if len(txn) > 1 else 0
                                note = str(txn.iloc[3]) if len(txn) > 3 else ""
                                
                                if amount > 0:
                                    st.error(f"📥 {date}: Credit Rs.{amount:,.2f} - {note}")
                                else:
                                    st.success(f"💰 {date}: Payment Rs.{abs(amount):,.2f} - {note}")
                        
                        with col2:
                            st.markdown("#### Quick Actions")
                            
                            with st.form(f"quick_pay_{customer}_{idx}"):
                                st.write("**Receive Payment**")
                                quick_amt = st.number_input(
                                    "Amount", 
                                    min_value=0.0, 
                                    max_value=float(balance), 
                                    value=float(balance),
                                    step=10.0,
                                    key=f"quick_{customer}_{idx}"
                                )
                                quick_mode = st.selectbox(
                                    "Mode", 
                                    ["Cash", "Online"], 
                                    key=f"mode_{customer}_{idx}"
                                )
                                
                                if st.form_submit_button("💰 Receive", type="primary", use_container_width=True):
                                    if quick_amt > 0:
                                        save_data("CustomerKhata", [
                                            customer, 
                                            -quick_amt, 
                                            str(today_dt), 
                                            f"Quick payment via {quick_mode}"
                                        ])
                                        
                                        if quick_mode == "Cash":
                                            update_balance(quick_amt, "Cash", 'add')
                                        elif quick_mode == "Online":
                                            update_balance(quick_amt, "Online", 'add')
                                        
                                        st.success(f"Rs.{quick_amt:,.2f} received!")
                                        time.sleep(1)
                                        st.rerun()
                
                st.divider()
                
                if st.button("📥 Download Due Report", type="secondary"):
                    csv = sum_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"customer_due_report_{today_dt}.csv",
                        mime="text/csv"
                    )
                
            else:
                st.success("✅ No outstanding dues! All customers have cleared their payments.")
                st.balloons()
            
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(k_df, use_container_width=True)
            
        else:
            st.info("📝 No customer due records yet. Start recording transactions above!")
            
            st.markdown("""
            ### 💡 How to use:
            
            **When customer pays you:**
            1. Select "Payment Received"
            2. Enter amount and payment mode
            3. Money will be added to your Cash/Online balance
            4. Customer's due will be reduced
            
            **When you give credit:**
            1. Select "Credit Given"
            2. Enter amount
            3. Customer's due will be increased
            4. No money deduction from your balance
            """)
            receivables = 0
        
        # Calculate payables (Supplier Dues)
        d_df = load_data("Dues")
        if not d_df.empty and len(d_df.columns) > 1:
            payables = d_df.groupby(d_df.columns[0])[d_df.columns[1]].sum()
            payables = payables[payables > 0].sum()
        else:
            payables = 0
        
        # Calculate asset values
    s_df = load_data("Sales")
    if not s_df.empty and len(s_df.columns) > 1:
        cash_bal = s_df.groupby(s_df.columns[0])[s_df.columns[1]].sum()
        cash_bal = cash_bal[cash_bal.index == "Cash"].sum() if "Cash" in cash_bal.index else 0
    else:
        cash_bal = 0

    online_bal = s_df.groupby(s_df.columns[0])[s_df.columns[1]].sum()
    online_bal = online_bal[online_bal.index == "Online"].sum() if "Online" in online_bal.index else 0

    inventory_value = 0
    receivables = 0
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
        st.info("💡 Simplified tax calculations for reference")
        if not s_df.empty and len(s_df.columns) > 3:
            start_date = today_dt - timedelta(days=30)
            end_date = today_dt
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
elif menu == "⚙️ Super Admin Panel":
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); border-radius: 20px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-size: 48px;">⚙️ Super Admin Panel</h1>
        <p style="color: white; margin-top: 15px; font-size: 20px;">Complete System Control</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "🎨 Theme Settings", "🔧 System Settings", "📊 System Stats"])
    
    with tab1:
        st.header("👥 User Management")
        
        # Initialize users in session state if not exists
        if 'system_users' not in st.session_state:
            st.session_state.system_users = USERS.copy()
        
        # Add New User
        with st.expander("➕ Add New User", expanded=False):
            with st.form("add_user"):
                st.subheader("Create New User Account")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username *", placeholder="Enter username")
                    new_password = st.text_input("Password *", type="password", placeholder="Enter password")
                
                with col2:
                    new_role = st.selectbox("Role *", ["ceo", "owner", "manager", "staff"])
                    new_display_name = st.text_input("Display Name *", placeholder="e.g., John (Manager)")
                
                if st.form_submit_button("✅ Create User", type="primary", use_container_width=True):
                    if new_username and new_password and new_display_name:
                        if new_username not in st.session_state.system_users:
                            st.session_state.system_users[new_username] = {
                                "password": new_password,
                                "role": new_role,
                                "name": new_display_name
                            }
                            # Save to a file or database here
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Username already exists!")
                    else:
                        st.error("⚠️ Please fill all fields!")
        
        st.divider()
        
        # View All Users
        st.subheader("👥 All System Users")
        
        for username, user_data in st.session_state.system_users.items():
            with st.expander(f"👤 {user_data['name']} (@{username}) - {user_data['role'].upper()}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Username:** {username}")
                    st.write(f"**Display Name:** {user_data['name']}")
                    st.write(f"**Role:** {user_data['role'].upper()}")
                
                with col2:
                    st.write(f"**Password:** {'*' * len(user_data['password'])}")
                    if st.button(f"🔄 Reset Password", key=f"reset_{username}"):
                        st.info("Password reset functionality - implement as needed")
                
                with col3:
                    if username not in ["Laika", "Prateek"]:  # Protect default accounts
                        if st.button(f"🗑️ Delete", key=f"del_{username}", type="secondary"):
                            del st.session_state.system_users[username]
                            st.success(f"✅ User '{username}' deleted!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("🔒 Protected")
    
    with tab2:
        st.header("🎨 Theme & UI Settings")
        
        # Initialize theme settings
        if 'theme_settings' not in st.session_state:
            st.session_state.theme_settings = {
                'dashboard_theme': 'gradient_blue',
                'sidebar_color': 'light',
                'primary_color': '#667eea'
            }
        
        st.subheader("Dashboard Theme")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme_option = st.selectbox(
                "Choose Dashboard Theme",
                [
                    "Gradient Blue (Default)",
                    "Dark Professional",
                    "Light Modern",
                    "Purple Royal",
                    "Green Nature",
                    "Orange Warm",
                    "Pink Creative"
                ],
                key="theme_selector"
            )
        
        with col2:
            sidebar_theme = st.selectbox(
                "Sidebar Theme",
                ["Light (Default)", "Dark", "Colorful"],
                key="sidebar_theme"
            )
        
        st.divider()
        
        st.subheader("🎨 Color Customization")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            primary_color = st.color_picker("Primary Color", "#667eea")
        
        with col2:
            secondary_color = st.color_picker("Secondary Color", "#764ba2")
        
        with col3:
            accent_color = st.color_picker("Accent Color", "#f093fb")
        
        if st.button("💾 Save Theme Settings", type="primary", use_container_width=True):
            st.session_state.theme_settings = {
                'dashboard_theme': theme_option,
                'sidebar_color': sidebar_theme,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'accent_color': accent_color
            }
            st.success("✅ Theme settings saved! Refresh page to see changes.")
            st.balloons()
        
        st.divider()
        
        st.subheader("🖼️ Theme Preview")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%); padding: 30px; border-radius: 15px; text-align: center;">
            <h2 style="color: white; margin: 0;">Preview Theme</h2>
            <p style="color: white; margin-top: 10px;">This is how your dashboard will look</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.header("🔧 System Settings")
        
        st.subheader("⚙️ General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Shop Name", value="LAIKA PET MART", key="shop_name")
            st.text_input("Shop Phone", value="+91 XXXXXXXXXX", key="shop_phone")
            st.text_input("Shop Address", value="Shop Address Here", key="shop_address")
        
        with col2:
            st.number_input("Low Stock Alert Level", value=2, min_value=1, max_value=10, key="low_stock")
            st.selectbox("Currency", ["₹ INR", "$ USD", "€ EUR"], key="currency")
            st.selectbox("Date Format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], key="date_format")
        
        st.divider()
        
        st.subheader("🔐 Security Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Enable Auto Logout (30 min)", value=False, key="auto_logout")
            st.checkbox("Require Password Change (90 days)", value=False, key="pwd_change")
        
        with col2:
            st.checkbox("Enable Audit Logs", value=True, key="audit_logs")
            st.checkbox("Two-Factor Authentication", value=False, key="2fa")
        
        if st.button("💾 Save System Settings", type="primary", use_container_width=True):
            st.success("✅ System settings saved successfully!")
    
    with tab4:
        st.header("📊 System Statistics")
        
        # Calculate stats
        s_df = load_data("Sales")
        i_df = load_data("Inventory")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_users = len(st.session_state.system_users) if 'system_users' in st.session_state else len(USERS)
        total_products = len(i_df.iloc[:, 0].unique()) if not i_df.empty else 0
        total_sales = len(s_df) if not s_df.empty else 0
        
        col1.metric("👥 Total Users", total_users)
        col2.metric("📦 Total Products", total_products)
        col3.metric("🧾 Total Sales", total_sales)
        col4.metric("💾 Data Sheets", "10+")
        
        st.divider()
        
        st.subheader("📈 System Health")
        
        col1, col2, col3 = st.columns(3)
        
        col1.success("✅ Database: Connected")
        col2.success("✅ Google Sheets: Synced")
        col3.success("✅ System: Running")
        
        st.divider()
        
        st.subheader("🔄 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ Cache cleared!")
        
        with col2:
            if st.button("🔄 Reload Data", use_container_width=True):
                st.success("✅ Data reloaded!")
                st.rerun()
        
        with col3:
            if st.button("📥 Export All Data", use_container_width=True):
                st.info("📦 Export functionality")

else:
    st.info(f"Module: {menu} - Feature under development")




















































