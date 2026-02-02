import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import time
import urllib.parse

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
    
    /* WhatsApp button styling */
    .whatsapp-button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 10px;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
        transition: all 0.3s ease;
    }
    
    .whatsapp-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.6);
    }
    
    /* Bill container */
    .bill-container {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin: 20px 0;
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
if 'last_sale_details' not in st.session_state:
    st.session_state.last_sale_details = None

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

def get_item_purchase_rate(item_name):
    """Get the latest purchase rate for an item from Inventory"""
    try:
        inv_df = load_data("Inventory")
        if not inv_df.empty and len(inv_df.columns) > 3:
            # Filter for this item
            item_rows = inv_df[inv_df.iloc[:, 0].str.strip().str.upper() == str(item_name).strip().upper()]
            
            if not item_rows.empty:
                # Get the most recent purchase rate (last row)
                last_purchase_rate = pd.to_numeric(item_rows.iloc[-1, 3], errors='coerce')
                return float(last_purchase_rate) if pd.notna(last_purchase_rate) else 0.0
        return 0.0
    except:
        return 0.0

def calculate_profit_for_period(start_date, end_date):
    """Calculate actual profit for a period = (Sale Price - Purchase Price) - Expenses"""
    try:
        # Load sales data
        s_df = load_data("Sales")
        if s_df.empty or 'Date' not in s_df.columns:
            return 0.0, 0.0, 0.0, 0.0
        
        # Filter sales for the period
        period_sales = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
        
        total_sale_amount = 0.0
        total_purchase_cost = 0.0
        
        if not period_sales.empty:
            for _, sale_row in period_sales.iterrows():
                item_name = sale_row.iloc[1] if len(sale_row) > 1 else ""
                sale_amount = pd.to_numeric(sale_row.iloc[3], errors='coerce') if len(sale_row) > 3 else 0.0
                
                # Get quantity sold
                qty_str = sale_row.iloc[2] if len(sale_row) > 2 else "0"
                try:
                    qty_sold = float(str(qty_str).split()[0])
                except:
                    qty_sold = 0.0
                
                # Get purchase rate
                purchase_rate = get_item_purchase_rate(item_name)
                
                # Calculate purchase cost for this sale
                purchase_cost = qty_sold * purchase_rate
                
                total_sale_amount += sale_amount
                total_purchase_cost += purchase_cost
        
        # Period expenses
        e_df = load_data("Expenses")
        period_expense = 0.0
        
        if not e_df.empty and len(e_df.columns) > 2:
            try:
                e_df['exp_date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
                period_exp = e_df[(e_df['exp_date'] >= start_date) & (e_df['exp_date'] <= end_date)]
                period_expense = pd.to_numeric(period_exp.iloc[:, 2], errors='coerce').sum() if not period_exp.empty else 0.0
            except:
                period_expense = 0.0
        
        # Calculate actual profit
        gross_profit = total_sale_amount - total_purchase_cost
        net_profit = gross_profit - period_expense
        
        return total_sale_amount, total_purchase_cost, period_expense, net_profit
        
    except Exception as e:
        st.error(f"Error calculating profit: {str(e)}")
        return 0.0, 0.0, 0.0, 0.0

def get_period_purchases(start_date, end_date):
    """Get total purchase amount for a specific period"""
    try:
        inv_df = load_data("Inventory")
        if inv_df.empty or 'Date' not in inv_df.columns:
            return 0.0
        
        # Filter purchases for the period
        period_purchases = inv_df[(inv_df['Date'] >= start_date) & (inv_df['Date'] <= end_date)]
        
        if not period_purchases.empty and len(period_purchases.columns) > 4:
            # Column 4 is total value (qty * rate)
            total_purchase = pd.to_numeric(period_purchases.iloc[:, 4], errors='coerce').sum()
            return float(total_purchase) if pd.notna(total_purchase) else 0.0
        
        return 0.0
    except:
        return 0.0

def get_customer_royalty_points(customer_name):
    """Get customer's total royalty points"""
    try:
        s_df = load_data("Sales")
        if s_df.empty or len(s_df.columns) < 7:
            return 0
        
        # Filter sales for this customer
        customer_sales = s_df[s_df.iloc[:, 5].str.contains(customer_name.split('(')[0].strip(), case=False, na=False)]
        
        if not customer_sales.empty:
            total_points = pd.to_numeric(customer_sales.iloc[:, 6], errors='coerce').sum()
            return int(total_points)
        
        return 0
    except:
        return 0

def calculate_royalty_points(amount, is_weekend=False):
    """Calculate royalty points based on purchase amount"""
    if is_weekend:
        return int(amount * 0.05)  # 5% on weekends
    else:
        return int(amount * 0.02)  # 2% on weekdays

def generate_whatsapp_bill(customer_name, customer_phone, cart_items, total_amount, payment_info, royalty_points=0):
    """Generate WhatsApp bill message"""
    
    today = datetime.now()
    is_weekend = today.weekday() >= 5
    
    # Calculate points earned on this purchase
    points_earned = calculate_royalty_points(total_amount, is_weekend)
    
    # Get existing points
    existing_points = get_customer_royalty_points(customer_name)
    total_points = existing_points + points_earned
    
    message = f"""🐾 *LAIKA PET MART* 🐾
━━━━━━━━━━━━━━━━━━━━

📅 Date: {today.strftime('%d-%m-%Y %I:%M %p')}
👤 Customer: {customer_name}

━━━━━━━━━━━━━━━━━━━━
📦 *ITEMS PURCHASED*
━━━━━━━━━━━━━━━━━━━━

"""
    
    for idx, item in enumerate(cart_items, 1):
        message += f"{idx}. *{item['Item']}*\n"
        message += f"   Qty: {item['Qty']} {item['Unit']} × ₹{item['Rate']:.2f}\n"
        message += f"   Amount: ₹{item['Amount']:.2f}\n\n"
    
    message += f"""━━━━━━━━━━━━━━━━━━━━
💰 *PAYMENT SUMMARY*
━━━━━━━━━━━━━━━━━━━━

Total Amount: ₹{total_amount:,.2f}
Payment Mode: {payment_info}

━━━━━━━━━━━━━━━━━━━━
👑 *ROYALTY POINTS*
━━━━━━━━━━━━━━━━━━━━

Points Earned: +{points_earned} 👑
Previous Points: {existing_points}
Total Points: {total_points} 👑

💡 Redeem 100 points for special offers!

━━━━━━━━━━━━━━━━━━━━

Thank you for shopping with us! 🙏
Visit again! 🐕🐈

📍 Laika Pet Mart
📞 Contact: [Your Number]
"""
    
    return message, points_earned

def create_whatsapp_link(phone_number, message):
    """Create WhatsApp link with pre-filled message"""
    # Clean phone number
    phone = phone_number.strip().replace('+', '').replace('-', '').replace(' ', '')
    
    # Add country code if not present
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
    
    return whatsapp_url

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
        "👑 Royalty Points"
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
        "👑 Royalty Points"
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
    
    # Stock Value Calculation (only latest stock for each item)
    inv_df = load_data("Inventory")
    if not inv_df.empty and len(inv_df.columns) > 3:
        # Get only the latest entry for each item
        latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
        latest_stock['qty_val'] = pd.to_numeric(latest_stock.iloc[:, 1], errors='coerce').fillna(0)
        latest_stock['rate_val'] = pd.to_numeric(latest_stock.iloc[:, 3], errors='coerce').fillna(0)
        latest_stock['total_val'] = latest_stock['qty_val'] * latest_stock['rate_val']
        total_stock_value = latest_stock['total_val'].sum()
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
    
    # Today's Report
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
        <h2 style="color: white; margin: 0; text-align: center;">📈 Today's Report - {today_dt.strftime('%d %B %Y')}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate today's profit
    today_sale, today_purchase_cost, today_expense, today_net_profit = calculate_profit_for_period(today_dt, today_dt)
    today_gross_profit = today_sale - today_purchase_cost
    
    # Get today's actual purchases (only purchases made today)
    today_purchases = get_period_purchases(today_dt, today_dt)
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_sale:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">🛒 Today's Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_purchases:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">💚 Gross Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_gross_profit:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📊 Net Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_net_profit:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Monthly Report
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
        <h2 style="color: white; margin: 0; text-align: center;">📅 Monthly Report - {curr_m_name} {today_dt.year}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate monthly profit
    month_start = date(today_dt.year, curr_m, 1)
    month_sale, month_purchase_cost, month_expense, month_net_profit = calculate_profit_for_period(month_start, today_dt)
    month_gross_profit = month_sale - month_purchase_cost
    
    # Get month's actual purchases
    month_purchases = get_period_purchases(month_start, today_dt)
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_sale:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">🛒 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_purchases:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333;">
            <p style="margin: 0; font-size: 16px;">💚 Gross Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_gross_profit:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
            <p style="margin: 0; font-size: 16px;">📊 Net Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_net_profit:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Profit breakdown explanation
    with st.expander("💡 Profit Calculation Details"):
        st.markdown(f"""
        ### 📊 Profit Breakdown Formula
        
        **Gross Profit** = Sale Amount - Purchase Cost (of sold items)
        - This shows the margin earned on products before expenses
        
        **Net Profit** = Gross Profit - Expenses  
        - This is the actual profit after all business expenses
        
        ---
        
        ### 📈 Today's Calculation:
        
        **Sale Amount:** ₹{today_sale:,.2f}  
        **Purchase Cost (of items sold):** ₹{today_purchase_cost:,.2f}  
        **Gross Profit:** ₹{today_sale:,.2f} - ₹{today_purchase_cost:,.2f} = ₹{today_gross_profit:,.2f}
        
        **Expenses:** ₹{today_expense:,.2f}  
        **Net Profit:** ₹{today_gross_profit:,.2f} - ₹{today_expense:,.2f} = ₹{today_net_profit:,.2f}
        
        **Today's Actual Purchase:** ₹{today_purchases:,.2f} (items bought today)
        
        ---
        
        ### 📅 Monthly Calculation ({curr_m_name}):
        
        **Sale Amount:** ₹{month_sale:,.2f}  
        **Purchase Cost (of items sold):** ₹{month_purchase_cost:,.2f}  
        **Gross Profit:** ₹{month_sale:,.2f} - ₹{month_purchase_cost:,.2f} = ₹{month_gross_profit:,.2f}
        
        **Expenses:** ₹{month_expense:,.2f}  
        **Net Profit:** ₹{month_gross_profit:,.2f} - ₹{month_expense:,.2f} = ₹{month_net_profit:,.2f}
        
        **Total Purchase This Month:** ₹{month_purchases:,.2f} (all purchases made)
        """)

# ========================================
# MENU 2: BILLING
# ========================================elif menu == "🧾 Billing":
    st.header("🧾 Billing System")
    
    # Show last sale details and WhatsApp option
    if st.session_state.last_sale_details:
        st.success("✅ Last sale completed successfully!")
        
        sale_data = st.session_state.last_sale_details
        
        # Display bill in a nice format
        st.markdown('<div class="bill-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### 📋 Bill Summary")
            st.info(f"**Customer:** {sale_data['customer_name']}")
            st.info(f"**Date:** {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")
            
            st.markdown("#### 📦 Items:")
            for idx, item in enumerate(sale_data['items'], 1):
                st.write(f"{idx}. **{item['Item']}** - {item['Qty']} {item['Unit']} × ₹{item['Rate']:.2f} = ₹{item['Amount']:.2f}")
            
            st.divider()
            st.markdown(f"### 💰 Total: ₹{sale_data['total_amount']:,.2f}")
            st.write(f"**Payment:** {sale_data['payment_info']}")
            st.success(f"**Points Earned:** {sale_data['points_earned']} 👑")
        
        with col2:
            st.markdown("### 📱 Send Bill")
            if sale_data.get('customer_phone'):
                whatsapp_url = create_whatsapp_link(
                    sale_data['customer_phone'],
                    sale_data['whatsapp_message']
                )
                
                st.markdown(f"""
                <a href="{whatsapp_url}" target="_blank" class="whatsapp-button" style="width: 100%; text-align: center; margin: 10px 0;">
                    📱 Send on WhatsApp
                </a>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No phone number provided")
            
            st.divider()
            
            if st.button("🔄 New Sale", type="primary", use_container_width=True):
                st.session_state.last_sale_details = None
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
    
    inv_df = load_data("Inventory")
    
    with st.expander("🛒 Add Items to Cart", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if not inv_df.empty:
                # Get only latest stock for each item
                latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
                items_list = latest_stock.iloc[:, 0].unique().tolist()
                item = st.selectbox("Select Item", items_list, key="bill_item")
            else:
                st.error("⚠️ No items in inventory!")
                item = None
        
        if item and not inv_df.empty:
            # Get latest stock for selected item
            product_stock = inv_df[inv_df.iloc[:, 0] == item].tail(1)
            
            if not product_stock.empty:
                available_qty = pd.to_numeric(product_stock.iloc[-1, 1], errors='coerce')
                last_unit = product_stock.iloc[-1, 2] if len(product_stock.columns) > 2 else "Pcs"
                last_rate = pd.to_numeric(product_stock.iloc[-1, 3], errors='coerce') if len(product_stock.columns) > 3 else 0
                
                st.info(f"📦 **Available Stock:** {available_qty} {last_unit} | 💰 **Purchase Rate:** ₹{last_rate}")
                
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
                
                # Show profit margin
                if rate > last_rate:
                    profit_per_unit = rate - last_rate
                    total_profit = profit_per_unit * qty
                    st.success(f"💚 Profit: ₹{total_profit:,.2f} (₹{profit_per_unit:.2f} per unit)")
                elif rate < last_rate:
                    loss_per_unit = last_rate - rate
                    total_loss = loss_per_unit * qty
                    st.error(f"⚠️ Loss: ₹{total_loss:,.2f} (₹{loss_per_unit:.2f} per unit)")
                
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
                                'Amount': qty * rate,
                                'PurchaseRate': last_rate
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
        
        # Calculate profit for display
        cart_df['Profit'] = (cart_df['Rate'] - cart_df['PurchaseRate']) * cart_df['Qty']
        cart_df['Profit_Display'] = cart_df['Profit'].apply(lambda x: f"₹{x:,.2f}" if x >= 0 else f"-₹{abs(x):,.2f}")
        
        display_df = cart_df[['Item', 'Qty_Display', 'Rate_Display', 'Amount_Display', 'Profit_Display']]
        display_df.columns = ['Item', 'Quantity', 'Rate', 'Amount', 'Profit']
        
        st.dataframe(display_df, use_container_width=True)
        
        total = sum([i['Amount'] for i in st.session_state.bill_cart])
        total_profit = sum([(item['Rate'] - item.get('PurchaseRate', 0)) * item['Qty'] for item in st.session_state.bill_cart])
        
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Bill", f"₹{total:,.2f}")
        col2.metric("💚 Total Profit", f"₹{total_profit:,.2f}")
        
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
            cust_phone = st.text_input("Customer Phone (for WhatsApp Bill)", key="cust_phone", placeholder="10-digit mobile number")
        
        # 👑 ROYALTY POINTS SECTION
        st.divider()
        st.markdown("### 👑 Royalty Points & Referral")
        
        # Check if customer exists and get their points
        existing_points = 0
        if cust_name.strip():
            existing_points = get_customer_royalty_points(cust_name)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Current Points:** {existing_points} 👑")
        
        with col2:
            # Points that will be earned (only if bill >= 100)
            is_weekend = datetime.now().weekday() >= 5
            if total >= 100:
                points_to_earn = calculate_royalty_points(total, is_weekend)
                st.success(f"**Will Earn:** +{points_to_earn} 👑")
            else:
                st.warning(f"**Min ₹100 needed**")
                points_to_earn = 0
        
        with col3:
            # Redemption option
            redeem_points = st.number_input(
                "Redeem Points (100 = ₹10)",
                min_value=0,
                max_value=existing_points,
                step=100,
                value=0,
                key="redeem_points"
            )
            
            if redeem_points > 0:
                redeem_value = (redeem_points / 100) * 10
                st.success(f"💰 Discount: ₹{redeem_value:.2f}")
            else:
                redeem_value = 0
        
        # Referral bonus
        st.markdown("#### 🎁 Referral Bonus")
        col1, col2 = st.columns(2)
        
        with col1:
            is_referral = st.checkbox("Customer came via Referral", key="is_referral")
        
        with col2:
            if is_referral:
                referral_bonus = 10
                st.success(f"🎉 Bonus: +{referral_bonus} points")
            else:
                referral_bonus = 0
        
        # Manual points adjustment (for owner/CEO only)
        if user_role in ["ceo", "owner"]:
            with st.expander("⚙️ Manual Points Adjustment (Admin Only)"):
                manual_points = st.number_input(
                    "Add/Remove Points Manually",
                    min_value=-1000,
                    max_value=1000,
                    value=0,
                    step=10,
                    key="manual_points",
                    help="Positive = Add points, Negative = Remove points"
                )
                
                if manual_points != 0:
                    st.warning(f"{'➕' if manual_points > 0 else '➖'} Manual Adjustment: {abs(manual_points)} points")
        else:
            manual_points = 0
        
        # Calculate final bill after redemption
        final_bill = total - redeem_value
        
        st.divider()
        st.markdown("### 💰 Payment Details")
        
        st.info(f"💵 **Original Bill:** ₹{total:,.2f}")
        if redeem_value > 0:
            st.success(f"🎁 **Points Discount:** -₹{redeem_value:.2f}")
            st.metric("**Final Bill**", f"₹{final_bill:,.2f}", delta=f"-₹{redeem_value:.2f}")
        else:
            st.metric("**Final Bill**", f"₹{final_bill:,.2f}")
        
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
                cash_amount = final_bill
                st.success(f"💵 **Cash Payment:** ₹{cash_amount:,.2f}")
            elif single_mode == "Online":
                online_amount = final_bill
                st.success(f"🏦 **Online Payment:** ₹{online_amount:,.2f}")
            else:
                udhaar_amount = final_bill
                st.warning(f"📒 **Credit (Udhaar):** ₹{udhaar_amount:,.2f}")
        
        else:
            st.markdown("#### 💳 Split Payment")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**💵 Cash**")
                cash_amount = st.number_input("Cash Amount", min_value=0.0, max_value=float(final_bill), value=0.0, step=10.0, key="split_cash")
                if cash_amount > 0:
                    st.success(f"✅ Cash: ₹{cash_amount:,.2f}")
            
            with col2:
                st.markdown("**🏦 Online**")
                max_online = float(final_bill - cash_amount)
                online_amount = st.number_input("Online Amount", min_value=0.0, max_value=max_online, value=0.0, step=10.0, key="split_online")
                if online_amount > 0:
                    st.success(f"✅ Online: ₹{online_amount:,.2f}")
            
            with col3:
                st.markdown("**📒 Udhaar**")
                max_udhaar = float(final_bill - cash_amount - online_amount)
                udhaar_amount = st.number_input("Udhaar Amount", min_value=0.0, max_value=max_udhaar, value=max_udhaar, step=10.0, key="split_udhaar")
                if udhaar_amount > 0:
                    st.warning(f"⚠️ Udhaar: ₹{udhaar_amount:,.2f}")
            
            total_paid = cash_amount + online_amount + udhaar_amount
            remaining = final_bill - total_paid
            
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Final Bill", f"₹{final_bill:,.2f}")
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
        
        # Calculate total points
        total_points_earned = points_to_earn + referral_bonus + manual_points
        
        summary_cols = st.columns(5)
        summary_cols[0].metric("💰 Original", f"₹{total:,.2f}")
        summary_cols[1].metric("🎁 Discount", f"₹{redeem_value:.2f}")
        summary_cols[2].metric("💵 Final", f"₹{final_bill:,.2f}")
        summary_cols[3].metric("👑 Points", f"+{total_points_earned}")
        summary_cols[4].metric("📊 Profit", f"₹{total_profit:,.2f}")
        
        payment_summary_cols = st.columns(3)
        payment_summary_cols[0].metric("💵 Cash", f"₹{cash_amount:,.2f}" if cash_amount > 0 else "₹0")
        payment_summary_cols[1].metric("🏦 Online", f"₹{online_amount:,.2f}" if online_amount > 0 else "₹0")
        payment_summary_cols[2].metric("📒 Udhaar", f"₹{udhaar_amount:,.2f}" if udhaar_amount > 0 else "₹0")
        
        can_save = True
        error_msg = ""
        
        if not cust_name.strip():
            can_save = False
            error_msg = "⚠️ Enter customer name!"
        
        if payment_split == "Multiple Payment Modes (Split Payment)":
            total_paid = cash_amount + online_amount + udhaar_amount
            if abs(total_paid - final_bill) > 0.01:
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
            
            # Save sale with points
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
                    total_points_earned,  # Total points including referral and manual
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
            
            # Update balances
            if cash_amount > 0:
                update_balance(cash_amount, "Cash", 'add')
            
            if online_amount > 0:
                update_balance(online_amount, "Online", 'add')
            
            if udhaar_amount > 0:
                save_data("CustomerKhata", [customer_info, udhaar_amount, str(today_dt), "Sale on credit"])
            
            # Deduct redeemed points
            if redeem_points > 0:
                save_data("Sales", [
                    str(today_dt),
                    "POINTS REDEEMED",
                    f"{redeem_points} points",
                    -redeem_value,
                    "Points Redemption",
                    customer_info,
                    -redeem_points,  # Negative points = deduction
                    0,
                    "Redemption"
                ])
            
            # Generate WhatsApp message
            whatsapp_message, points = generate_whatsapp_bill(
                cust_name,
                cust_phone,
                st.session_state.bill_cart,
                total,
                payment_info,
                total_points_earned
            )
            
            # Store sale details for WhatsApp
            st.session_state.last_sale_details = {
                'customer_name': cust_name,
                'customer_phone': cust_phone,
                'total_amount': total,
                'whatsapp_message': whatsapp_message,
                'points_earned': total_points_earned,
                'payment_info': payment_info,
                'items': st.session_state.bill_cart.copy()
            }
            
            st.success(f"✅ Sale completed! Profit: ₹{total_profit:,.2f} | Points: {total_points_earned} 👑")
            
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
                
                # ✅ SMART PURCHASE - Adds to existing or creates new
                payload = {
                    "action": "smart_purchase",
                    "sheet": "Inventory",
                    "item_name": item['Item'],
                    "qty": item['Qty'],
                    "unit": item['Unit'],
                    "rate": item['Rate'],
                    "total_value": total_value,
                    "date": str(today_dt),
                    "payment_info": payment_info
                }
                
                try:
                    response = requests.post(SCRIPT_URL, json=payload, timeout=10)
                    response_text = response.text.strip()
                    
                    if "Added" in response_text or "created" in response_text:
                        st.success(f"✅ {item['Item']}: {response_text}")
                    else:
                        st.warning(f"⚠️ {item['Item']}: Saved")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
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
        # Get only latest stock for each item (no duplicate entries)
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
    
    st.divider()
    
    # Show registered pets count only
    pets_df = load_data("PetRegister")
    if not pets_df.empty:
        st.metric("📊 Total Pets Registered", len(pets_df))
        st.info("💡 Pet details are stored in Google Sheets")
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
                
                # Customer due list with payment button
                for idx, row in sum_df.iterrows():
                    customer_name = row['Customer']
                    due_amount = row['Balance']
                    
                    with st.expander(f"🔴 **{customer_name}** - Due: Rs.{due_amount:,.2f}"):
                        st.write(f"**Outstanding Amount:** ₹{due_amount:,.2f}")
                        
                        st.markdown("#### 💰 Record Payment")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            payment_amt = st.number_input(
                                "Payment Amount",
                                min_value=0.0,
                                max_value=float(due_amount),
                                value=float(due_amount),
                                step=10.0,
                                key=f"pay_amt_{idx}"
                            )
                        
                        with col2:
                            payment_method = st.selectbox(
                                "Payment Mode",
                                ["Cash", "Online"],
                                key=f"pay_mode_{idx}"
                            )
                        
                        if st.button(f"✅ Receive Payment", key=f"pay_btn_{idx}", type="primary"):
                            if payment_amt > 0:
                                # Record negative amount (payment received)
                                save_data("CustomerKhata", [customer_name, -payment_amt, str(today_dt), f"Payment received via {payment_method}"])
                                
                                # Update balance
                                if payment_method == "Cash":
                                    update_balance(payment_amt, "Cash", 'add')
                                elif payment_method == "Online":
                                    update_balance(payment_amt, "Online", 'add')
                                
                                st.success(f"✅ Payment of ₹{payment_amt:,.2f} received from {customer_name}")
                                time.sleep(1)
                                st.rerun()
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


