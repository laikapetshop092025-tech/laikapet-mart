import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import time
import urllib.parse

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e0e7ff 0%, #f3f4f6 100%);
    }
    
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
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(240, 147, 251, 0.5);
        border: 2px solid #ff6b9d;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        box-shadow: 0 5px 25px rgba(255, 216, 155, 0.6);
        transform: scale(1.03);
        border: 2px solid #ffd89b;
        font-weight: 700;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #1e293b !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .main {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }
</style>
""", unsafe_allow_html=True)

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

# Initialize session states
if 'bill_cart' not in st.session_state: 
    st.session_state.bill_cart = []
if 'purchase_cart' not in st.session_state: 
    st.session_state.purchase_cart = []
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

def update_stock_in_sheet(item_name, qty_change, operation='subtract'):
    """Update stock in Google Sheets - subtract for sales, add for purchase"""
    try:
        item_name = str(item_name).strip().upper()
        qty_change = float(qty_change)
        
        # Get current stock
        inv_df = load_data("Inventory")
        if inv_df.empty:
            return False
        
        item_rows = inv_df[inv_df.iloc[:, 0].str.strip().str.upper() == item_name]
        if item_rows.empty:
            return False
        
        latest_row = item_rows.iloc[-1]
        current_qty = float(pd.to_numeric(latest_row.iloc[1], errors='coerce'))
        
        if operation == 'subtract':
            new_qty = current_qty - qty_change
        else:
            new_qty = current_qty + qty_change
        
        if new_qty < 0:
            st.error(f"❌ Insufficient stock for {item_name}!")
            return False
        
        payload = {
            "action": "update_stock",
            "item_name": item_name,
            "new_qty": new_qty
        }
        
        response = requests.post(SCRIPT_URL, json=payload, timeout=15)
        response_text = response.text.strip()
        
        if "SUCCESS" in response_text:
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Stock update error: {str(e)}")
        return False

def get_balance_from_sheet(mode):
    """Get balance from Google Sheets"""
    try:
        b_df = load_data("Balances")
        if b_df.empty or len(b_df.columns) < 2:
            return 0.0
        
        rows = b_df[b_df.iloc[:, 0].str.strip() == mode]
        
        if len(rows) > 0:
            latest_balance = rows.iloc[-1, 1]
            return float(pd.to_numeric(latest_balance, errors='coerce'))
        
        return 0.0
    except:
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
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def calculate_loyalty_points(amount, bill_date):
    """Calculate loyalty points - 2 points per ₹100 on weekdays, 4 points on weekends"""
    try:
        points_base = (amount // 100) * 2
        
        # Check if weekend (Saturday=5, Sunday=6)
        if bill_date.weekday() >= 5:
            points_base = points_base * 2
        
        return int(points_base)
    except:
        return 0

def get_customer_loyalty_points(customer_name):
    """Get total loyalty points for a customer"""
    try:
        loyalty_df = load_data("LoyaltyPoints")
        if loyalty_df.empty:
            return 0
        
        customer_rows = loyalty_df[loyalty_df.iloc[:, 0].str.strip().str.upper() == customer_name.strip().upper()]
        if customer_rows.empty:
            return 0
        
        total_points = pd.to_numeric(customer_rows.iloc[:, 1], errors='coerce').sum()
        return int(total_points)
    except:
        return 0

def get_item_purchase_rate(item_name):
    """Get the purchase rate of an item from inventory"""
    try:
        inv_df = load_data("Inventory")
        if inv_df.empty:
            return 0.0
        
        item_rows = inv_df[inv_df.iloc[:, 0].str.strip().str.upper() == item_name.strip().upper()]
        if item_rows.empty:
            return 0.0
        
        latest_row = item_rows.iloc[-1]
        purchase_rate = float(pd.to_numeric(latest_row.iloc[3], errors='coerce'))
        return purchase_rate
    except:
        return 0.0

# --- MULTI-USER LOGIN ---
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
    "Staff1": {"password": "Staff@123", "role": "staff", "name": "Staff Member 1"}
}

if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0; font-size: 48px;">🔐 LAIKA PET MART</h1>
        <p style="color: white; margin-top: 15px; font-size: 20px;">Multi-User Login System</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        u = st.text_input("👤 Username").strip()
        p = st.text_input("🔒 Password", type="password").strip()
        
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
    
    st.stop()

# --- SIDEBAR MENU ---
today_dt = datetime.now().date()

st.sidebar.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
    <h3 style="color: white; margin: 0;">👤 {st.session_state.username}</h3>
    <p style="color: white; margin: 5px 0 0 0; font-size: 14px;">{st.session_state.user_role.upper()}</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<h2>📋 Main Menu</h2>", unsafe_allow_html=True)

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "📊 Dashboard"

user_role = st.session_state.user_role or "staff"

if user_role in ["ceo", "owner", "manager"]:
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📦 Purchase", 
        "📋 Live Stock", 
        "📒 Customer Due",
        "🏢 Supplier Dues",
        "🐕 Pet Register",
        "💰 Expenses",
        "⭐ Loyalty Points"
    ]
else:
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📋 Live Stock"
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

# ==========================================
# MENU 1: DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-size: 52px;">Welcome to Laika Pet Mart</h1>
        <p style="color: white; margin-top: 15px; font-size: 22px;">🐕 Your Trusted Pet Care Partner 🐈</p>
    </div>
    """, unsafe_allow_html=True)
    
    cash_bal = get_current_balance("Cash")
    online_bal = get_current_balance("Online")
    total_bal = cash_bal + online_bal
    
    # Hand Investment
    total_hand_investment = 0
    try:
        hand_df = load_data("HandInvestments")
        if not hand_df.empty and len(hand_df.columns) > 2:
            hand_amounts = pd.to_numeric(hand_df.iloc[:, 2], errors='coerce').fillna(0)
            total_hand_investment = hand_amounts.sum()
    except:
        total_hand_investment = 0
    
    # Customer Due
    k_df = load_data("CustomerKhata")
    if not k_df.empty and len(k_df.columns) > 1:
        customer_due = k_df.groupby(k_df.columns[0])[k_df.columns[1]].sum()
        total_customer_due = customer_due[customer_due > 0].sum()
    else:
        total_customer_due = 0
    
    # Stock Value
    inv_df = load_data("Inventory")
    if not inv_df.empty and len(inv_df.columns) > 3:
        latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
        latest_stock['qty_val'] = pd.to_numeric(latest_stock.iloc[:, 1], errors='coerce').fillna(0)
        latest_stock['rate_val'] = pd.to_numeric(latest_stock.iloc[:, 3], errors='coerce').fillna(0)
        latest_stock['total_val'] = latest_stock['qty_val'] * latest_stock['rate_val']
        total_stock_value = latest_stock['total_val'].sum()
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
    
    # Manual Balance Adjustment Section
    if user_role in ["ceo", "owner"]:
        with st.expander("⚙️ Manually Adjust Balances", expanded=False):
            st.warning("⚠️ Use this only if balances are incorrect. This will override current values!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("💵 Cash Balance")
                new_cash = st.number_input("Set Cash Balance", min_value=0.0, value=float(cash_bal), step=100.0, key="manual_cash_input")
                if st.button("✅ Update Cash", key="update_cash_btn", use_container_width=True):
                    if save_data("Balances", ["Cash", new_cash]):
                        st.session_state.manual_cash = new_cash
                        st.success(f"✅ Cash updated to ₹{new_cash:,.2f}")
                        time.sleep(1)
                        st.rerun()
            
            with col2:
                st.subheader("🏦 Online Balance")
                new_online = st.number_input("Set Online Balance", min_value=0.0, value=float(online_bal), step=100.0, key="manual_online_input")
                if st.button("✅ Update Online", key="update_online_btn", use_container_width=True):
                    if save_data("Balances", ["Online", new_online]):
                        st.session_state.manual_online = new_online
                        st.success(f"✅ Online updated to ₹{new_online:,.2f}")
                        time.sleep(1)
                        st.rerun()
            
            with col3:
                st.subheader("📊 Quick Actions")
                if st.button("🔄 Refresh All Data", key="refresh_data", use_container_width=True):
                    st.session_state.manual_cash = None
                    st.session_state.manual_online = None
                    st.success("✅ Data refreshed!")
                    time.sleep(0.5)
                    st.rerun()
    
    # Daily Report
    st.divider()
    st.subheader("📅 Today's Report")
    
    bills_df = load_data("Bills")
    purchase_df = load_data("Purchases")
    expense_df = load_data("Expenses")
    
    today_sales = 0
    today_purchase = 0
    today_expense = 0
    
    if not bills_df.empty and 'Date' in bills_df.columns:
        today_bills = bills_df[bills_df['Date'] == today_dt]
        if len(today_bills.columns) > 6:
            today_sales = pd.to_numeric(today_bills.iloc[:, 6], errors='coerce').sum()
    
    if not purchase_df.empty and 'Date' in purchase_df.columns:
        today_purchases = purchase_df[purchase_df['Date'] == today_dt]
        if len(today_purchases.columns) > 5:
            today_purchase = pd.to_numeric(today_purchases.iloc[:, 5], errors='coerce').sum()
    
    if not expense_df.empty and 'Date' in expense_df.columns:
        today_expenses = expense_df[expense_df['Date'] == today_dt]
        if len(today_expenses.columns) > 2:
            today_expense = pd.to_numeric(today_expenses.iloc[:, 2], errors='coerce').sum()
    
    today_profit = today_sales - today_purchase - today_expense
    
    # Colorful Today's Report Cards
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
            <p style="margin: 0; font-size: 16px;">💰 Sales</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_sales:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);">
            <p style="margin: 0; font-size: 16px;">📦 Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_purchase:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(250, 112, 154, 0.4);">
            <p style="margin: 0; font-size: 16px;">💸 Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(48, 207, 208, 0.4);">
            <p style="margin: 0; font-size: 16px;">📈 Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{today_profit:,.2f}</h2>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{'+' if today_profit >= 0 else ''}{today_profit:,.2f}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Manual Today's Report Adjustment
    if user_role in ["ceo", "owner", "manager"]:
        with st.expander("⚙️ Manually Adjust Today's Report", expanded=False):
            st.warning("⚠️ Use this to correct today's figures if needed!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                adj_sales = st.number_input("Adjust Sales", value=float(today_sales), step=100.0, key="adj_sales")
                adj_purchase = st.number_input("Adjust Purchase", value=float(today_purchase), step=100.0, key="adj_purchase")
            
            with col2:
                adj_expense = st.number_input("Adjust Expense", value=float(today_expense), step=100.0, key="adj_expense")
                adj_profit = adj_sales - adj_purchase - adj_expense
                st.metric("Adjusted Profit", f"₹{adj_profit:,.2f}")
            
            st.info(f"""
            **Preview:**
            - Sales: ₹{today_sales:,.2f} → ₹{adj_sales:,.2f}
            - Purchase: ₹{today_purchase:,.2f} → ₹{adj_purchase:,.2f}
            - Expense: ₹{today_expense:,.2f} → ₹{adj_expense:,.2f}
            - Profit: ₹{today_profit:,.2f} → ₹{adj_profit:,.2f}
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Save Adjustments", key="save_daily_adj", type="primary", use_container_width=True):
                    # Save adjustment entry
                    save_data("DailyAdjustments", [
                        today_dt.strftime("%d/%m/%Y"),
                        adj_sales,
                        adj_purchase,
                        adj_expense,
                        adj_profit,
                        st.session_state.username
                    ])
                    st.success("✅ Today's report adjusted!")
                    time.sleep(1)
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset to Calculated", key="reset_daily", use_container_width=True):
                    st.info("Values reset to auto-calculated!")
                    time.sleep(0.5)
                    st.rerun()
    
    # Monthly Report
    st.divider()
    st.subheader("📊 Monthly Report")
    
    current_month = today_dt.month
    current_year = today_dt.year
    
    month_sales = 0
    month_purchase = 0
    month_expense = 0
    
    if not bills_df.empty and 'Date' in bills_df.columns:
        month_bills = bills_df[(bills_df['Date'].apply(lambda x: x.month if pd.notna(x) else 0) == current_month) & 
                               (bills_df['Date'].apply(lambda x: x.year if pd.notna(x) else 0) == current_year)]
        if len(month_bills.columns) > 6:
            month_sales = pd.to_numeric(month_bills.iloc[:, 6], errors='coerce').sum()
    
    if not purchase_df.empty and 'Date' in purchase_df.columns:
        month_purchases = purchase_df[(purchase_df['Date'].apply(lambda x: x.month if pd.notna(x) else 0) == current_month) & 
                                      (purchase_df['Date'].apply(lambda x: x.year if pd.notna(x) else 0) == current_year)]
        if len(month_purchases.columns) > 5:
            month_purchase = pd.to_numeric(month_purchases.iloc[:, 5], errors='coerce').sum()
    
    if not expense_df.empty and 'Date' in expense_df.columns:
        month_expenses = expense_df[(expense_df['Date'].apply(lambda x: x.month if pd.notna(x) else 0) == current_month) & 
                                    (expense_df['Date'].apply(lambda x: x.year if pd.notna(x) else 0) == current_year)]
        if len(month_expenses.columns) > 2:
            month_expense = pd.to_numeric(month_expenses.iloc[:, 2], errors='coerce').sum()
    
    month_profit = month_sales - month_purchase - month_expense
    
    # Colorful Monthly Report Cards
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div style="flex: 1; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);">
            <p style="margin: 0; font-size: 16px;">💰 Sales</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_sales:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);">
            <p style="margin: 0; font-size: 16px;">📦 Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_purchase:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(255, 153, 102, 0.4);">
            <p style="margin: 0; font-size: 16px;">💸 Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(255, 216, 155, 0.4);">
            <p style="margin: 0; font-size: 16px;">📈 Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{month_profit:,.2f}</h2>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{'+' if month_profit >= 0 else ''}{month_profit:,.2f}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# MENU 2: BILLING
# ==========================================
elif menu == "🧾 Billing":
    st.header("🧾 Billing System")
    
    tab1, tab2 = st.tabs(["➕ New Bill", "📜 Bill History"])
    
    with tab1:
        st.subheader("Create New Bill")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cust_name = st.text_input("👤 Customer Name", key="bill_cust_name")
            cust_phone = st.text_input("📱 Customer Phone", key="bill_cust_phone")
        
        with col2:
            bill_date = st.date_input("📅 Bill Date", value=today_dt, key="bill_date")
        
        st.divider()
        st.subheader("Add Items to Bill")
        
        # Load inventory for item selection
        inv_df = load_data("Inventory")
        if not inv_df.empty:
            item_list = inv_df.iloc[:, 0].unique().tolist()
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                selected_item = st.selectbox("Select Item", [""] + item_list, key="bill_item")
            
            with col2:
                item_qty = st.number_input("Quantity (Kg/Pcs)", min_value=0.0, value=1.0, step=0.5, key="bill_qty")
            
            with col3:
                item_rate = st.number_input("Rate per unit", min_value=0.0, value=0.0, step=1.0, key="bill_rate")
            
            with col4:
                st.write("")
                st.write("")
                if st.button("➕ Add", key="add_bill_item"):
                    if selected_item and item_qty > 0 and item_rate > 0:
                        # Get purchase rate for profit calculation
                        purchase_rate = get_item_purchase_rate(selected_item)
                        
                        st.session_state.bill_cart.append({
                            'Item': selected_item,
                            'Qty': item_qty,
                            'Rate': item_rate,
                            'Amount': item_qty * item_rate,
                            'Purchase_Rate': purchase_rate
                        })
                        st.success(f"✅ {selected_item} added to cart!")
                        st.rerun()
                    else:
                        st.error("Please fill all fields!")
        
        # Display Cart
        if st.session_state.bill_cart:
            st.divider()
            st.subheader("🛒 Cart Items")
            
            cart_df = pd.DataFrame(st.session_state.bill_cart)
            
            for idx, row in cart_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                col1.write(f"**{row['Item']}**")
                col2.write(f"{row['Qty']} units")
                col3.write(f"₹{row['Rate']:.2f}/unit")
                col4.write(f"₹{row['Amount']:.2f}")
                
                if col5.button("🗑️", key=f"del_bill_{idx}"):
                    st.session_state.bill_cart.pop(idx)
                    st.rerun()
            
            total_amount = cart_df['Amount'].sum()
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
                <h2 style="margin: 0;">Total Amount: ₹{total_amount:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Payment Details
            st.divider()
            st.subheader("💳 Payment Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cash_paid = st.number_input("💵 Cash Paid", min_value=0.0, value=0.0, step=10.0, key="cash_paid")
            
            with col2:
                online_paid = st.number_input("🏦 Online Paid", min_value=0.0, value=0.0, step=10.0, key="online_paid")
            
            with col3:
                due_amount = total_amount - cash_paid - online_paid
                st.metric("📒 Due Amount", f"₹{due_amount:,.2f}")
            
            # Generate Bill Button
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Generate Bill", type="primary", use_container_width=True):
                    if not cust_name:
                        st.error("Please enter customer name!")
                    else:
                        # Save each item to Bills sheet
                        all_saved = True
                        
                        for item in st.session_state.bill_cart:
                            bill_data = [
                                bill_date.strftime("%d/%m/%Y"),
                                cust_name,
                                cust_phone,
                                item['Item'],
                                item['Qty'],
                                item['Rate'],
                                item['Amount']
                            ]
                            
                            if not save_data("Bills", bill_data):
                                all_saved = False
                                break
                            
                            # Update stock
                            if not update_stock_in_sheet(item['Item'], item['Qty'], operation='subtract'):
                                st.error(f"Failed to update stock for {item['Item']}")
                                all_saved = False
                                break
                        
                        if all_saved:
                            # Update Cash Balance
                            if cash_paid > 0:
                                update_balance(cash_paid, "Cash", operation='add')
                            
                            # Update Online Balance
                            if online_paid > 0:
                                update_balance(online_paid, "Online", operation='add')
                            
                            # Save Customer Due if any
                            if due_amount > 0:
                                save_data("CustomerKhata", [cust_name, due_amount])
                            
                            # Calculate and save loyalty points
                            loyalty_points = calculate_loyalty_points(total_amount, bill_date)
                            if loyalty_points > 0:
                                save_data("LoyaltyPoints", [cust_name, loyalty_points, bill_date.strftime("%d/%m/%Y")])
                            
                            st.success(f"✅ Bill generated successfully! Loyalty Points: {loyalty_points}")
                            st.session_state.bill_cart = []
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Error generating bill!")
            
            with col2:
                if st.button("📱 Send WhatsApp Bill", use_container_width=True):
                    if not cust_phone:
                        st.error("Please enter customer phone number!")
                    else:
                        # Generate bill message
                        msg = f"*LAIKA PET MART - BILL*\n\n"
                        msg += f"Customer: {cust_name}\n"
                        msg += f"Date: {bill_date.strftime('%d/%m/%Y')}\n"
                        msg += f"{'='*30}\n\n"
                        
                        for item in st.session_state.bill_cart:
                            msg += f"{item['Item']}\n"
                            msg += f"  Qty: {item['Qty']} × ₹{item['Rate']} = ₹{item['Amount']:.2f}\n\n"
                        
                        msg += f"{'='*30}\n"
                        msg += f"Total: ₹{total_amount:,.2f}\n"
                        msg += f"Cash Paid: ₹{cash_paid:,.2f}\n"
                        msg += f"Online Paid: ₹{online_paid:,.2f}\n"
                        msg += f"Due: ₹{due_amount:,.2f}\n\n"
                        
                        loyalty_pts = calculate_loyalty_points(total_amount, bill_date)
                        msg += f"Loyalty Points Earned: {loyalty_pts}\n"
                        msg += f"\nThank you for shopping with us! 🐾"
                        
                        # Create WhatsApp link
                        phone = cust_phone.replace("+", "").replace(" ", "")
                        if not phone.startswith("91"):
                            phone = "91" + phone
                        
                        wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
                        st.markdown(f"[📱 Click to Send Bill on WhatsApp]({wa_link})")
    
    with tab2:
        st.subheader("📜 Bill History")
        
        bills_df = load_data("Bills")
        
        if not bills_df.empty:
            # Date filter
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_date = st.date_input("Filter by Date", value=today_dt, key="filter_bill_date")
            
            with col2:
                if st.button("🔍 Filter", key="filter_bills"):
                    st.rerun()
            
            with col3:
                if st.button("🔄 Show All", key="show_all_bills"):
                    filter_date = None
                    st.rerun()
            
            # Filter bills
            if filter_date and 'Date' in bills_df.columns:
                display_df = bills_df[bills_df['Date'] == filter_date]
            else:
                display_df = bills_df
            
            if not display_df.empty:
                st.divider()
                
                # Group by date and show bills
                if 'Date' in display_df.columns:
                    for bill_date in display_df['Date'].unique():
                        date_bills = display_df[display_df['Date'] == bill_date]
                        
                        st.markdown(f"### 📅 {bill_date.strftime('%d/%m/%Y')}")
                        
                        # Group by customer for each date
                        for idx, row in date_bills.iterrows():
                            with st.expander(f"Bill #{idx+1} - {row.iloc[1] if len(row) > 1 else 'Unknown'} - ₹{row.iloc[6] if len(row) > 6 else 0:.2f}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Customer:** {row.iloc[1] if len(row) > 1 else 'N/A'}")
                                    st.write(f"**Phone:** {row.iloc[2] if len(row) > 2 else 'N/A'}")
                                
                                with col2:
                                    st.write(f"**Item:** {row.iloc[3] if len(row) > 3 else 'N/A'}")
                                    st.write(f"**Qty:** {row.iloc[4] if len(row) > 4 else 0} × ₹{row.iloc[5] if len(row) > 5 else 0} = ₹{row.iloc[6] if len(row) > 6 else 0:.2f}")
                                
                                if st.button(f"🗑️ Delete Bill #{idx+1}", key=f"del_history_bill_{idx}"):
                                    st.warning("Delete functionality coming soon!")
                        
                        st.divider()
                else:
                    st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No bills found for selected date!")
        else:
            st.info("No bills found!")

# ==========================================
# MENU 3: PURCHASE
# ==========================================
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    tab1, tab2 = st.tabs(["➕ New Purchase", "📜 Purchase History"])
    
    with tab1:
        st.subheader("Create New Purchase")
        
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_name = st.text_input("🏢 Supplier Name", key="purch_supplier")
            supplier_phone = st.text_input("📱 Supplier Phone", key="purch_phone")
        
        with col2:
            purch_date = st.date_input("📅 Purchase Date", value=today_dt, key="purch_date")
        
        st.divider()
        st.subheader("Add Items to Purchase")
        
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        
        with col1:
            item_name = st.text_input("Item Name", key="purch_item_name")
        
        with col2:
            item_qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5, key="purch_qty")
        
        with col3:
            item_unit = st.selectbox("Unit", ["Kg", "Pcs", "Box", "Bag"], key="purch_unit")
        
        with col4:
            item_rate = st.number_input("Rate/Unit", min_value=0.0, value=0.0, step=1.0, key="purch_rate")
        
        with col5:
            st.write("")
            st.write("")
            if st.button("➕", key="add_purch_item"):
                if item_name and item_qty > 0 and item_rate > 0:
                    st.session_state.purchase_cart.append({
                        'Item': item_name.upper(),
                        'Qty': item_qty,
                        'Unit': item_unit,
                        'Rate': item_rate,
                        'Amount': item_qty * item_rate
                    })
                    st.success(f"✅ {item_name} added!")
                    st.rerun()
        
        # Display Purchase Cart
        if st.session_state.purchase_cart:
            st.divider()
            st.subheader("🛒 Purchase Cart")
            
            cart_df = pd.DataFrame(st.session_state.purchase_cart)
            
            for idx, row in cart_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                col1.write(f"**{row['Item']}**")
                col2.write(f"{row['Qty']} {row['Unit']}")
                col3.write(f"₹{row['Rate']:.2f}/{row['Unit']}")
                col4.write(f"₹{row['Amount']:.2f}")
                
                if col5.button("🗑️", key=f"del_purch_{idx}"):
                    st.session_state.purchase_cart.pop(idx)
                    st.rerun()
            
            total_amount = cart_df['Amount'].sum()
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
                <h2 style="margin: 0;">Total Purchase: ₹{total_amount:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Payment Details
            st.divider()
            st.subheader("💳 Payment Mode")
            
            payment_mode = st.radio("Select Payment Mode", 
                                    ["💵 Cash", "🏦 Online", "👋 Hand Investment", "📒 Credit (Supplier Due)"],
                                    horizontal=True,
                                    key="purch_payment_mode")
            
            if payment_mode == "📒 Credit (Supplier Due)":
                paid_amount = st.number_input("Paid Amount (if any)", min_value=0.0, value=0.0, step=10.0, key="purch_paid")
                due_amount = total_amount - paid_amount
                
                if paid_amount > 0:
                    paid_mode = st.radio("Paid via", ["💵 Cash", "🏦 Online"], horizontal=True, key="purch_paid_mode")
            
            # Save Purchase Button
            st.divider()
            
            if st.button("✅ Save Purchase", type="primary", use_container_width=True):
                if not supplier_name:
                    st.error("Please enter supplier name!")
                else:
                    all_saved = True
                    
                    for item in st.session_state.purchase_cart:
                        # Save to Purchases sheet
                        purch_data = [
                            purch_date.strftime("%d/%m/%Y"),
                            supplier_name,
                            supplier_phone,
                            item['Item'],
                            f"{item['Qty']} {item['Unit']}",
                            item['Amount']
                        ]
                        
                        if not save_data("Purchases", purch_data):
                            all_saved = False
                            break
                        
                        # Save to Inventory
                        inv_data = [
                            item['Item'],
                            item['Qty'],
                            item['Unit'],
                            item['Rate'],
                            purch_date.strftime("%d/%m/%Y")
                        ]
                        
                        if not save_data("Inventory", inv_data):
                            all_saved = False
                            break
                    
                    if all_saved:
                        # Update balances based on payment mode
                        if payment_mode == "💵 Cash":
                            update_balance(total_amount, "Cash", operation='subtract')
                        elif payment_mode == "🏦 Online":
                            update_balance(total_amount, "Online", operation='subtract')
                        elif payment_mode == "👋 Hand Investment":
                            save_data("HandInvestments", [supplier_name, purch_date.strftime("%d/%m/%Y"), total_amount])
                        elif payment_mode == "📒 Credit (Supplier Due)":
                            if paid_amount > 0:
                                if paid_mode == "💵 Cash":
                                    update_balance(paid_amount, "Cash", operation='subtract')
                                else:
                                    update_balance(paid_amount, "Online", operation='subtract')
                            
                            if due_amount > 0:
                                save_data("SupplierDues", [supplier_name, due_amount, purch_date.strftime("%d/%m/%Y")])
                        
                        st.success("✅ Purchase saved successfully!")
                        st.session_state.purchase_cart = []
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error saving purchase!")
    
    with tab2:
        st.subheader("📜 Purchase History")
        
        purch_df = load_data("Purchases")
        
        if not purch_df.empty:
            st.dataframe(purch_df, use_container_width=True)
        else:
            st.info("No purchases found!")

# ==========================================
# MENU 4: LIVE STOCK
# ==========================================
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

# ==========================================
# MENU 5: CUSTOMER DUE
# ==========================================
elif menu == "📒 Customer Due":
    st.header("📒 Customer Due Management")
    
    k_df = load_data("CustomerKhata")
    
    if not k_df.empty and len(k_df.columns) >= 2:
        # Convert amount column to numeric
        k_df_copy = k_df.copy()
        k_df_copy.iloc[:, 1] = pd.to_numeric(k_df_copy.iloc[:, 1], errors='coerce').fillna(0)
        
        customer_dues = k_df_copy.groupby(k_df_copy.columns[0])[k_df_copy.columns[1]].sum()
        customers_with_due = customer_dues[customer_dues > 0]
        
        if not customers_with_due.empty:
            st.subheader("📊 All Customer Dues")
            
            for idx, (customer, due) in enumerate(customers_with_due.items()):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"### 👤 {customer}")
                        st.markdown(f"**Due Amount: ₹{due:,.2f}**")
                    
                    with col2:
                        with st.expander("💰 Make Payment", expanded=False):
                            payment_amount = st.number_input(
                                "Payment Amount", 
                                min_value=0.0, 
                                max_value=float(due), 
                                value=float(due),
                                step=10.0,
                                key=f"cust_pay_{idx}_{customer}"
                            )
                            
                            payment_mode = st.radio(
                                "Payment Mode",
                                ["💵 Cash", "🏦 Online"],
                                horizontal=True,
                                key=f"cust_mode_{idx}_{customer}"
                            )
                            
                            if st.button("✅ Receive", key=f"cust_receive_{idx}_{customer}", type="primary", use_container_width=True):
                                if payment_amount > 0:
                                    # Save negative entry to reduce due
                                    if save_data("CustomerKhata", [customer, -payment_amount]):
                                        # Update balance
                                        mode = "Cash" if payment_mode == "💵 Cash" else "Online"
                                        update_balance(payment_amount, mode, operation='add')
                                        
                                        st.success(f"✅ ₹{payment_amount:,.2f} received!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Error saving payment!")
                    
                    with col3:
                        st.write("")
                
                st.divider()
            
            # Total Due Summary
            total_due = customers_with_due.sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin-top: 20px;">
                <h2 style="margin: 0;">Total Customer Due: ₹{total_due:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ No pending customer dues!")
    else:
        st.info("No customer dues found!")

# ==========================================
# MENU 6: SUPPLIER DUES
# ==========================================
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues Management")
    
    sup_df = load_data("SupplierDues")
    
    if not sup_df.empty and len(sup_df.columns) >= 2:
        # Convert amount column to numeric
        sup_df_copy = sup_df.copy()
        sup_df_copy.iloc[:, 1] = pd.to_numeric(sup_df_copy.iloc[:, 1], errors='coerce').fillna(0)
        
        supplier_dues = sup_df_copy.groupby(sup_df_copy.columns[0])[sup_df_copy.columns[1]].sum()
        suppliers_with_due = supplier_dues[supplier_dues > 0]
        
        if not suppliers_with_due.empty:
            st.subheader("📊 All Supplier Dues")
            
            for idx, (supplier, due) in enumerate(suppliers_with_due.items()):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"### 🏢 {supplier}")
                        st.markdown(f"**Due Amount: ₹{due:,.2f}**")
                    
                    with col2:
                        with st.expander("💰 Make Payment", expanded=False):
                            payment_amount = st.number_input(
                                "Payment Amount", 
                                min_value=0.0, 
                                max_value=float(due), 
                                value=float(due),
                                step=10.0,
                                key=f"sup_pay_{idx}_{supplier}"
                            )
                            
                            payment_mode = st.radio(
                                "Payment Mode",
                                ["💵 Cash", "🏦 Online"],
                                horizontal=True,
                                key=f"sup_mode_{idx}_{supplier}"
                            )
                            
                            if st.button("✅ Pay Now", key=f"sup_pay_btn_{idx}_{supplier}", type="primary", use_container_width=True):
                                if payment_amount > 0:
                                    # Save negative entry to reduce due
                                    if save_data("SupplierDues", [supplier, -payment_amount, today_dt.strftime("%d/%m/%Y")]):
                                        # Update balance
                                        mode = "Cash" if payment_mode == "💵 Cash" else "Online"
                                        update_balance(payment_amount, mode, operation='subtract')
                                        
                                        st.success(f"✅ ₹{payment_amount:,.2f} paid!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Error saving payment!")
                    
                    with col3:
                        st.write("")
                
                st.divider()
            
            # Total Due Summary
            total_due = suppliers_with_due.sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin-top: 20px;">
                <h2 style="margin: 0;">Total Supplier Due: ₹{total_due:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ No pending supplier dues!")
    else:
        st.info("No supplier dues found!")

# ==========================================
# MENU 7: PET REGISTER
# ==========================================
elif menu == "🐕 Pet Register":
    st.header("🐕 Pet Register")
    
    tab1, tab2 = st.tabs(["➕ Register Pet", "📋 Pet Records"])
    
    with tab1:
        st.subheader("Register New Pet")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Bird", "Other"], key="pet_type")
            pet_breed = st.text_input("Breed", key="pet_breed")
            pet_color = st.text_input("Color", key="pet_color")
            pet_age = st.text_input("Age", key="pet_age")
        
        with col2:
            sale_date = st.date_input("Sale Date", value=today_dt, key="pet_sale_date")
            customer_name = st.text_input("Customer Name", key="pet_customer")
            customer_phone = st.text_input("Customer Phone", key="pet_cust_phone")
            sale_price = st.number_input("Sale Price", min_value=0.0, value=0.0, step=100.0, key="pet_price")
        
        st.divider()
        st.subheader("Vaccination Schedule")
        
        col1, col2 = st.columns(2)
        
        with col1:
            vaccine_1 = st.text_input("Vaccine 1", key="vaccine_1")
            vaccine_1_date = st.date_input("Vaccine 1 Date", key="vaccine_1_date")
        
        with col2:
            vaccine_2 = st.text_input("Vaccine 2", key="vaccine_2")
            vaccine_2_date = st.date_input("Vaccine 2 Date", key="vaccine_2_date")
        
        if st.button("✅ Register Pet", type="primary", use_container_width=True):
            pet_data = [
                sale_date.strftime("%d/%m/%Y"),
                pet_type,
                pet_breed,
                pet_color,
                pet_age,
                customer_name,
                customer_phone,
                sale_price,
                vaccine_1,
                vaccine_1_date.strftime("%d/%m/%Y"),
                vaccine_2,
                vaccine_2_date.strftime("%d/%m/%Y")
            ]
            
            if save_data("PetRegister", pet_data):
                st.success(f"✅ {pet_type} registered successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error registering pet!")
    
    with tab2:
        st.subheader("📋 All Pet Records")
        
        pet_df = load_data("PetRegister")
        
        if not pet_df.empty:
            st.dataframe(pet_df, use_container_width=True)
        else:
            st.info("No pet records found!")

# ==========================================
# MENU 8: EXPENSES
# ==========================================
elif menu == "💰 Expenses":
    st.header("💰 Expense Management")
    
    tab1, tab2 = st.tabs(["➕ Add Expense", "📊 Expense History"])
    
    with tab1:
        st.subheader("Add New Expense")
        
        col1, col2 = st.columns(2)
        
        with col1:
            expense_date = st.date_input("Date", value=today_dt, key="exp_date")
            expense_category = st.selectbox("Category", 
                                          ["Rent", "Electricity", "Salary", "Transport", "Miscellaneous"],
                                          key="exp_category")
        
        with col2:
            expense_amount = st.number_input("Amount", min_value=0.0, value=0.0, step=10.0, key="exp_amount")
            payment_mode = st.radio("Payment Mode", ["💵 Cash", "🏦 Online"], horizontal=True, key="exp_payment")
        
        expense_remark = st.text_area("Remarks", key="exp_remark")
        
        if st.button("✅ Add Expense", type="primary", use_container_width=True):
            if expense_amount > 0:
                exp_data = [
                    expense_date.strftime("%d/%m/%Y"),
                    expense_category,
                    expense_amount,
                    expense_remark
                ]
                
                if save_data("Expenses", exp_data):
                    # Update balance
                    mode = "Cash" if payment_mode == "💵 Cash" else "Online"
                    update_balance(expense_amount, mode, operation='subtract')
                    
                    st.success("✅ Expense added successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error adding expense!")
            else:
                st.error("Please enter expense amount!")
    
    with tab2:
        st.subheader("📊 Expense History")
        
        exp_df = load_data("Expenses")
        
        if not exp_df.empty:
            # Monthly summary
            if 'Date' in exp_df.columns and len(exp_df.columns) > 2:
                current_month = today_dt.month
                current_year = today_dt.year
                
                month_expenses = exp_df[(exp_df['Date'].apply(lambda x: x.month if pd.notna(x) else 0) == current_month) & 
                                       (exp_df['Date'].apply(lambda x: x.year if pd.notna(x) else 0) == current_year)]
                
                if not month_expenses.empty:
                    total_month_exp = pd.to_numeric(month_expenses.iloc[:, 2], errors='coerce').sum()
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px;">
                        <h2 style="margin: 0;">This Month's Expenses: ₹{total_month_exp:,.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            st.dataframe(exp_df, use_container_width=True)
        else:
            st.info("No expenses found!")

# ==========================================
# MENU 9: LOYALTY POINTS
# ==========================================
elif menu == "⭐ Loyalty Points":
    st.header("⭐ Loyalty Points Management")
    
    st.info("""
    **Loyalty Points System:**
    - ₹100 purchase = 2 points (Monday to Friday)
    - ₹100 purchase = 4 points (Saturday & Sunday)
    """)
    
    tab1, tab2 = st.tabs(["🔍 Check Points", "📊 All Customers"])
    
    with tab1:
        st.subheader("Check Customer Points")
        
        customer_name = st.text_input("Enter Customer Name", key="loyalty_search")
        
        if st.button("🔍 Search", key="search_loyalty"):
            if customer_name:
                points = get_customer_loyalty_points(customer_name)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 30px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
                    <h3 style="margin: 0;">{customer_name}</h3>
                    <h1 style="margin: 10px 0;">⭐ {points} Points</h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Please enter customer name!")
    
    with tab2:
        st.subheader("📊 All Customer Points")
        
        loyalty_df = load_data("LoyaltyPoints")
        
        if not loyalty_df.empty and len(loyalty_df.columns) > 1:
            customer_points = loyalty_df.groupby(loyalty_df.columns[0])[loyalty_df.columns[1]].sum()
            customer_points = customer_points.sort_values(ascending=False)
            
            for idx, (customer, points) in enumerate(customer_points.items(), 1):
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "⭐"
                st.info(f"{medal} **{customer}**: {int(points)} points")
        else:
            st.info("No loyalty points data found!")
