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
        new_qty = float(new_qty)
        
        st.info(f"🔄 Updating {item_name} stock to {new_qty}...")
        
        payload = {
            "action": "update_stock",
            "item_name": item_name,
            "new_qty": new_qty
        }
        
        response = requests.post(SCRIPT_URL, json=payload, timeout=15)
        response_text = response.text.strip()
        
        st.write(f"Server Response: {response_text}")
        
        if "SUCCESS" in response_text:
            st.success(f"✅ {item_name} stock updated to {new_qty}")
            return True
        elif "ERROR" in response_text:
            st.error(f"❌ {response_text}")
            return False
        else:
            st.warning(f"⚠️ Unexpected response: {response_text}")
            return False
            
    except Exception as e:
        st.error(f"❌ Stock update failed: {str(e)}")
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
            item_rows = inv_df[inv_df.iloc[:, 0].str.strip().str.upper() == str(item_name).strip().upper()]
            
            if not item_rows.empty:
                last_purchase_rate = pd.to_numeric(item_rows.iloc[-1, 3], errors='coerce')
                return float(last_purchase_rate) if pd.notna(last_purchase_rate) else 0.0
        return 0.0
    except:
        return 0.0

def calculate_profit_for_period(start_date, end_date):
    """Calculate actual profit for a period"""
    try:
        s_df = load_data("Sales")
        if s_df.empty or 'Date' not in s_df.columns:
            return 0.0, 0.0, 0.0, 0.0
        
        period_sales = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
        
        total_sale_amount = 0.0
        total_purchase_cost = 0.0
        
        if not period_sales.empty:
            for _, sale_row in period_sales.iterrows():
                item_name = sale_row.iloc[1] if len(sale_row) > 1 else ""
                sale_amount = pd.to_numeric(sale_row.iloc[3], errors='coerce') if len(sale_row) > 3 else 0.0
                
                qty_str = sale_row.iloc[2] if len(sale_row) > 2 else "0"
                try:
                    qty_sold = float(str(qty_str).split()[0])
                except:
                    qty_sold = 0.0
                
                purchase_rate = get_item_purchase_rate(item_name)
                purchase_cost = qty_sold * purchase_rate
                
                total_sale_amount += sale_amount
                total_purchase_cost += purchase_cost
        
        e_df = load_data("Expenses")
        period_expense = 0.0
        
        if not e_df.empty and len(e_df.columns) > 2:
            try:
                e_df['exp_date'] = pd.to_datetime(e_df.iloc[:, 0], errors='coerce').dt.date
                period_exp = e_df[(e_df['exp_date'] >= start_date) & (e_df['exp_date'] <= end_date)]
                period_expense = pd.to_numeric(period_exp.iloc[:, 2], errors='coerce').sum() if not period_exp.empty else 0.0
            except:
                period_expense = 0.0
        
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
        
        period_purchases = inv_df[(inv_df['Date'] >= start_date) & (inv_df['Date'] <= end_date)]
        
        if not period_purchases.empty and len(period_purchases.columns) > 4:
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
        return int(amount * 0.05)
    else:
        return int(amount * 0.02)

def generate_whatsapp_bill(customer_name, customer_phone, cart_items, total_amount, payment_info, royalty_points=0):
    """Generate WhatsApp bill message"""
    
    today = datetime.now()
    is_weekend = today.weekday() >= 5
    
    points_earned = calculate_royalty_points(total_amount, is_weekend)
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
    phone = phone_number.strip().replace('+', '').replace('-', '').replace(' ', '')
    
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    encoded_message = urllib.parse.quote(message)
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
else:
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
    
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        customer_due = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum()
        total_customer_due = customer_due[customer_due > 0].sum()
    else:
        total_customer_due = 0
    
    inv_df = load_data("Inventory")
    if not inv_df.empty and len(inv_df.columns) > 3:
        latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
        latest_stock['qty_val'] = pd.to_numeric(latest_stock.iloc[:, 1], errors='coerce').fillna(0)
        latest_stock['rate_val'] = pd.to_numeric(latest_stock.iloc[:, 3], errors='coerce').fillna(0)
        latest_stock['total_val'] = latest_stock['qty_val'] * latest_stock['rate_val']
        total_stock_value = latest_stock['total_val'].sum()
    else:
        total_stock_value = 0
    
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
    
    st.info("✅ Dashboard loaded successfully!")

elif menu == "🧾 Billing":
    st.header("🧾 Billing Section")
    st.info("Billing features coming soon...")

elif menu == "📦 Purchase":
    st.header("📦 Purchase Section")
    st.info("Purchase features coming soon...")

elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    st.info("Stock management coming soon...")

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    st.info("Expense tracking coming soon...")

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Register")
    st.info("Pet registration coming soon...")

elif menu == "📒 Customer Due":
    st.header("📒 Customer Due")
    st.info("Customer due management coming soon...")

elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues")
    st.info("Supplier dues management coming soon...")

elif menu == "👑 Royalty Points":
    st.header("👑 Royalty Points")
    st.info("Royalty points system coming soon...")
