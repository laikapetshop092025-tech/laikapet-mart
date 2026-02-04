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
        "💉 Services",
        "⭐ Loyalty Points",
        "🎁 Offers & Discount",
        "📈 Analysis Report",
        "📑 Financial Reports"
    ]
else:
    menu_items = [
        "📊 Dashboard", 
        "🧾 Billing", 
        "📋 Live Stock",
        "💉 Services"
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
            
            # Show purchase rate when item is selected
            if selected_item:
                purchase_rate = get_item_purchase_rate(selected_item)
                st.info(f"💡 **Purchase Rate:** ₹{purchase_rate:.2f} | You can set your selling price below")
            
            with col2:
                item_qty = st.number_input("Quantity (Kg/Pcs)", min_value=0.0, value=1.0, step=0.5, key="bill_qty")
            
            with col3:
                # Set default selling rate slightly higher than purchase rate if available
                default_rate = 0.0
                if selected_item:
                    purchase_rate = get_item_purchase_rate(selected_item)
                    default_rate = purchase_rate * 1.2  # 20% markup as default suggestion
                
                item_rate = st.number_input("Selling Rate per unit", min_value=0.0, value=default_rate, step=1.0, key="bill_rate")
            
            # Show profit margin
            if selected_item and item_rate > 0:
                purchase_rate = get_item_purchase_rate(selected_item)
                profit_per_unit = item_rate - purchase_rate
                profit_margin = ((profit_per_unit / item_rate) * 100) if item_rate > 0 else 0
                
                if profit_per_unit > 0:
                    st.success(f"📈 Profit: ₹{profit_per_unit:.2f}/unit ({profit_margin:.1f}% margin)")
                elif profit_per_unit < 0:
                    st.error(f"⚠️ Loss: ₹{abs(profit_per_unit):.2f}/unit (Selling below cost!)")
                else:
                    st.warning("⚠️ No profit - Selling at cost price")
            
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
            
            # Manual Discount Option
            st.divider()
            st.subheader("💰 Discount (Optional)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                discount_type = st.selectbox("Discount Type", 
                                            ["No Discount", "Percentage (%)", "Flat Amount (₹)"],
                                            key="discount_type")
            
            discount_value = 0
            discount_amount = 0
            
            if discount_type == "Percentage (%)":
                with col2:
                    discount_value = st.number_input("Discount %", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key="discount_percent")
                    discount_amount = (total_amount * discount_value) / 100
            
            elif discount_type == "Flat Amount (₹)":
                with col2:
                    discount_amount = st.number_input("Discount ₹", min_value=0.0, max_value=float(total_amount), value=0.0, step=10.0, key="discount_flat")
            
            if discount_amount > 0:
                discount_reason = st.text_input("Discount Reason", placeholder="e.g., Regular customer, Festival offer", key="discount_reason")
                st.info(f"💡 Discount Applied: ₹{discount_amount:,.2f}")
            else:
                discount_reason = ""
            
            # Calculate amount after discount
            amount_after_discount = total_amount - discount_amount
            
            if discount_amount > 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 15px; border-radius: 10px; text-align: center; color: white; margin: 10px 0;">
                    <h3 style="margin: 0;">Amount to Pay: ₹{amount_after_discount:,.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Payment Details
            st.divider()
            st.subheader("💳 Payment Details")
            
            # Payment Mode Selection
            payment_mode = st.radio(
                "Select Payment Mode",
                ["💵 Cash", "🏦 Online", "📒 Due (Credit)"],
                horizontal=True,
                key="bill_payment_mode"
            )
            
            # Amount fields based on payment mode
            if payment_mode == "💵 Cash":
                cash_paid = amount_after_discount
                online_paid = 0.0
                due_amount_adjusted = 0.0
                st.success(f"✅ Cash Payment: ₹{cash_paid:,.2f}")
            
            elif payment_mode == "🏦 Online":
                cash_paid = 0.0
                online_paid = amount_after_discount
                due_amount_adjusted = 0.0
                st.success(f"✅ Online Payment: ₹{online_paid:,.2f}")
            
            else:  # Due/Credit
                cash_paid = 0.0
                online_paid = 0.0
                due_amount_adjusted = amount_after_discount
                st.warning(f"📒 Due Amount: ₹{due_amount_adjusted:,.2f} (Will be added to customer account)")
            
            # Loyalty Points Section
            st.divider()
            st.subheader("⭐ Loyalty Points")
            
            # Calculate suggested points (₹100 = 2 points)
            suggested_points = int((amount_after_discount // 100) * 2)
            
            # Show current points first
            current_customer_points = 0
            if cust_name:
                current_customer_points = get_customer_loyalty_points(cust_name)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 14px;">Current Points</p>
                    <h2 style="margin: 5px 0; font-size: 32px;">{current_customer_points}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 15px; border-radius: 10px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 14px;">Suggested Points</p>
                    <h2 style="margin: 5px 0; font-size: 32px;">{suggested_points}</h2>
                    <p style="margin: 0; font-size: 12px; opacity: 0.9;">₹100 = 2 points</p>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                loyalty_points = st.number_input("Points to Give", 
                                                min_value=0, 
                                                value=suggested_points, 
                                                step=1, 
                                                key="bill_loyalty_points", 
                                                help="Change if you want to give more/less points")
            
            with col2:
                loyalty_reason = st.text_input("Reason (Optional)", value="Purchase", key="bill_loyalty_reason",
                                              placeholder="e.g., Purchase, Special Offer")
            
            # Redeem Points Option
            st.divider()
            use_redeem = st.checkbox("🎁 Redeem Loyalty Points", key="use_redeem")
            
            redeem_points = 0
            redeem_value = 0
            
            if use_redeem and current_customer_points > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    redeem_points = st.number_input("Points to Redeem", 
                                                   min_value=0, 
                                                   max_value=current_customer_points, 
                                                   value=min(10, current_customer_points),
                                                   step=1,
                                                   key="redeem_points")
                    st.info("💡 1 Point = ₹1")
                
                with col2:
                    redeem_value = redeem_points * 1  # 1 point = 1 rupee
                    st.metric("Discount Amount", f"₹{redeem_value}")
                    
                    remaining_points = current_customer_points - redeem_points
                    st.metric("Points After Redeem", f"{remaining_points}")
            
            # Update due amount if redeeming points
            if redeem_value > 0:
                final_amount = amount_after_discount - redeem_value
                cash_paid_adjusted = cash_paid
                online_paid_adjusted = online_paid
                due_amount_adjusted = final_amount - cash_paid_adjusted - online_paid_adjusted
            else:
                final_amount = amount_after_discount
                cash_paid_adjusted = cash_paid
                online_paid_adjusted = online_paid
                # Calculate due based on payment mode
                if payment_mode == "📒 Due (Credit)":
                    due_amount_adjusted = amount_after_discount
                else:
                    due_amount_adjusted = 0.0
            
            # Show final summary
            if redeem_value > 0 or discount_amount > 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 15px; border-radius: 10px; color: white; margin: 10px 0;">
                    <h4 style="margin: 0 0 10px 0;">Final Bill Summary</h4>
                    <p style="margin: 0;"><strong>Original Amount:</strong> ₹{total_amount:,.2f}</p>
                    {f'<p style="margin: 5px 0;"><strong>Manual Discount:</strong> -₹{discount_amount:,.2f}</p>' if discount_amount > 0 else ''}
                    {f'<p style="margin: 5px 0;"><strong>Points Discount:</strong> -₹{redeem_value:,.2f} ({redeem_points} points)</p>' if redeem_value > 0 else ''}
                    <p style="margin: 5px 0;"><strong>Final Amount:</strong> ₹{final_amount:,.2f}</p>
                    <p style="margin: 5px 0;"><strong>Paid:</strong> ₹{cash_paid_adjusted + online_paid_adjusted:,.2f}</p>
                    <p style="margin: 5px 0 0 0;"><strong>Due:</strong> ₹{due_amount_adjusted:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Show points preview
            if cust_name:
                new_total_points = current_customer_points + loyalty_points - redeem_points
                st.success(f"🎯 Today's Points: **+{loyalty_points}** | Redeemed: **-{redeem_points}** | Final Balance: **{new_total_points}** points")
            
            # Generate Bill Button
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Generate Bill", type="primary", use_container_width=True):
                    if not cust_name:
                        st.error("Please enter customer name!")
                    else:
                        try:
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
                                # Redeem Points - Save negative entry
                                if redeem_points > 0:
                                    redeem_data = [
                                        cust_name,
                                        -redeem_points,  # Negative to deduct
                                        bill_date.strftime("%d/%m/%Y"),
                                        f"Redeemed (₹{redeem_value} discount)",
                                        st.session_state.username
                                    ]
                                    save_data("LoyaltyPoints", redeem_data)
                                
                                # Update Cash Balance
                                if cash_paid > 0:
                                    update_balance(cash_paid, "Cash", operation='add')
                                
                                # Update Online Balance
                                if online_paid > 0:
                                    update_balance(online_paid, "Online", operation='add')
                                
                                # Save Customer Due if any
                                if due_amount_adjusted > 0:
                                    save_data("CustomerKhata", [cust_name, due_amount_adjusted])
                                
                                # Add Loyalty Points (new points earned)
                                if loyalty_points > 0:
                                    points_data = [
                                        cust_name,
                                        loyalty_points,
                                        bill_date.strftime("%d/%m/%Y"),
                                        loyalty_reason if loyalty_reason else "Purchase",
                                        st.session_state.username
                                    ]
                                    save_data("LoyaltyPoints", points_data)
                                
                                st.success(f"✅ Bill generated successfully!")
                                if loyalty_points > 0:
                                    st.info(f"⭐ {loyalty_points} loyalty points added!")
                                if redeem_points > 0:
                                    st.success(f"🎁 {redeem_points} points redeemed (₹{redeem_value} discount)!")
                                st.session_state.bill_cart = []
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Error generating bill!")
                        except Exception as e:
                            st.error(f"❌ Error generating bill: {str(e)}")
            
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
                        msg += f"Subtotal: ₹{total_amount:,.2f}\n"
                        
                        # Show manual discount if applied
                        if discount_amount > 0:
                            msg += f"Discount: -₹{discount_amount:,.2f}"
                            if discount_reason:
                                msg += f" ({discount_reason})"
                            msg += "\n"
                        
                        # Show redeem discount if applied
                        if redeem_value > 0:
                            msg += f"Points Discount: -₹{redeem_value:,.2f} ({redeem_points} points)\n"
                        
                        # Show final amount if any discount
                        if discount_amount > 0 or redeem_value > 0:
                            msg += f"Final Amount: ₹{final_amount:,.2f}\n"
                        
                        msg += f"Cash Paid: ₹{cash_paid:,.2f}\n"
                        msg += f"Online Paid: ₹{online_paid:,.2f}\n"
                        msg += f"Due: ₹{due_amount_adjusted:,.2f}\n\n"
                        
                        msg += f"{'='*30}\n"
                        msg += f"*LOYALTY POINTS*\n"
                        msg += f"Previous Balance: {current_customer_points} points\n"
                        
                        if loyalty_points > 0:
                            msg += f"Earned Today: +{loyalty_points} points 🎉\n"
                        
                        if redeem_points > 0:
                            msg += f"Redeemed Today: -{redeem_points} points\n"
                        
                        final_points = current_customer_points + loyalty_points - redeem_points
                        msg += f"*New Balance: {final_points} points* ⭐\n\n"
                        
                        msg += f"Thank you for shopping with us! 🐾"
                        
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
        
        # Load inventory to show existing items
        inv_df = load_data("Inventory")
        existing_items = []
        if not inv_df.empty:
            existing_items = sorted(inv_df.iloc[:, 0].unique().tolist())
        
        # Option to select existing or add new
        item_option = st.radio("Item Selection", ["Existing Item", "New Item"], horizontal=True, key="item_option")
        
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        
        with col1:
            if item_option == "Existing Item":
                if existing_items:
                    selected_item = st.selectbox("Select Existing Item", existing_items, key="purch_existing_item")
                    item_name = selected_item
                else:
                    st.warning("No existing items! Please select 'New Item'")
                    item_name = ""
            else:
                item_name = st.text_input("New Item Name", key="purch_new_item_name").upper()
        
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
# MENU 9: SERVICES
# ==========================================
elif menu == "💉 Services":
    st.header("💉 Service Management")
    
    st.info("💡 Track vaccination, grooming, and other pet services here. Payment automatically adds to Cash/Online balance.")
    
    tab1, tab2 = st.tabs(["➕ Add Service", "📋 Service History"])
    
    with tab1:
        st.subheader("Record Service")
        
        col1, col2 = st.columns(2)
        
        with col1:
            service_date = st.date_input("Service Date", value=today_dt, key="service_date")
            customer_name = st.text_input("Customer Name", key="service_customer")
            customer_phone = st.text_input("Customer Phone", key="service_phone")
        
        with col2:
            pet_name = st.text_input("Pet Name (Optional)", key="service_pet_name")
            pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Bird", "Other"], key="service_pet_type")
        
        st.divider()
        st.subheader("Service Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            service_type = st.selectbox("Service Type", 
                                       ["Vaccination", "Grooming", "Health Checkup", "Training", "Nail Cutting", 
                                        "Bathing", "Ear Cleaning", "Deworming", "Other"],
                                       key="service_type")
            
            if service_type == "Other":
                service_type = st.text_input("Specify Service", key="service_other")
        
        with col2:
            service_amount = st.number_input("Service Charge ₹", min_value=0.0, value=0.0, step=50.0, key="service_amount")
            payment_mode = st.radio("Payment Mode", ["💵 Cash", "🏦 Online"], horizontal=True, key="service_payment")
        
        service_notes = st.text_area("Notes/Details", placeholder="e.g., Vaccine name, next due date, etc.", key="service_notes")
        
        st.divider()
        
        if st.button("✅ Save Service", type="primary", use_container_width=True):
            if not customer_name:
                st.error("Please enter customer name!")
            elif service_amount <= 0:
                st.error("Please enter service amount!")
            else:
                service_data = [
                    service_date.strftime("%d/%m/%Y"),
                    customer_name,
                    customer_phone,
                    pet_name if pet_name else "N/A",
                    pet_type,
                    service_type,
                    service_amount,
                    payment_mode.replace("💵 ", "").replace("🏦 ", ""),
                    service_notes,
                    st.session_state.username
                ]
                
                if save_data("Services", service_data):
                    # Update balance
                    mode = "Cash" if payment_mode == "💵 Cash" else "Online"
                    update_balance(service_amount, mode, operation='add')
                    
                    st.success(f"✅ Service recorded! ₹{service_amount:,.2f} added to {mode}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error saving service!")
    
    with tab2:
        st.subheader("📋 Service History")
        
        services_df = load_data("Services")
        
        if not services_df.empty:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_date = st.date_input("Filter by Date", value=today_dt, key="filter_service_date")
            
            with col2:
                if st.button("🔍 Filter", key="filter_services"):
                    st.rerun()
            
            with col3:
                if st.button("🔄 Show All", key="show_all_services"):
                    filter_date = None
                    st.rerun()
            
            # Calculate total
            if len(services_df.columns) > 6:
                total_services = pd.to_numeric(services_df.iloc[:, 6], errors='coerce').sum()
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
                    <h2 style="margin: 0;">Total Service Income: ₹{total_services:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Display services
            display_df = services_df
            if filter_date and 'Date' in services_df.columns:
                display_df = services_df[services_df['Date'] == filter_date]
            
            if not display_df.empty:
                for idx, row in display_df.iterrows():
                    with st.expander(f"🐾 {row.iloc[1] if len(row) > 1 else 'Customer'} - {row.iloc[5] if len(row) > 5 else 'Service'} - ₹{row.iloc[6] if len(row) > 6 else 0:.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Date:** {row.iloc[0] if len(row) > 0 else 'N/A'}")
                            st.write(f"**Customer:** {row.iloc[1] if len(row) > 1 else 'N/A'}")
                            st.write(f"**Phone:** {row.iloc[2] if len(row) > 2 else 'N/A'}")
                            st.write(f"**Pet Name:** {row.iloc[3] if len(row) > 3 else 'N/A'}")
                        
                        with col2:
                            st.write(f"**Pet Type:** {row.iloc[4] if len(row) > 4 else 'N/A'}")
                            st.write(f"**Service:** {row.iloc[5] if len(row) > 5 else 'N/A'}")
                            st.write(f"**Amount:** ₹{row.iloc[6] if len(row) > 6 else 0:.2f}")
                            st.write(f"**Payment:** {row.iloc[7] if len(row) > 7 else 'N/A'}")
                        
                        if len(row) > 8 and row.iloc[8]:
                            st.write(f"**Notes:** {row.iloc[8]}")
            else:
                st.info("No services found for selected date!")
        else:
            st.info("No services recorded yet!")

# ==========================================
# MENU 10: OFFERS & DISCOUNT
# ==========================================
elif menu == "🎁 Offers & Discount":
    st.header("🎁 Offers & Discount Management")
    
    tab1, tab2 = st.tabs(["➕ Create Offer", "📋 Active Offers"])
    
    with tab1:
        st.subheader("Create New Offer/Discount")
        
        col1, col2 = st.columns(2)
        
        with col1:
            offer_name = st.text_input("🏷️ Offer Name", placeholder="e.g., Diwali Mega Sale", key="offer_name")
            offer_type = st.selectbox("Offer Type", 
                                     ["Percentage Discount", "Flat Discount", "Buy 1 Get 1", "Combo Offer", "Free Gift", "Custom Offer"],
                                     key="offer_type")
            
            if offer_type == "Percentage Discount":
                discount_percent = st.number_input("Discount %", min_value=0, max_value=100, value=10, key="discount_percent")
                offer_description = f"{discount_percent}% OFF on all items"
            elif offer_type == "Flat Discount":
                flat_amount = st.number_input("Discount Amount ₹", min_value=0.0, value=100.0, step=10.0, key="flat_amount")
                min_purchase = st.number_input("Minimum Purchase ₹", min_value=0.0, value=500.0, step=50.0, key="min_purchase")
                offer_description = f"₹{flat_amount} OFF on purchase above ₹{min_purchase}"
            elif offer_type == "Buy 1 Get 1":
                product_name = st.text_input("Product Name", key="b1g1_product")
                offer_description = f"Buy 1 Get 1 FREE on {product_name}"
            elif offer_type == "Combo Offer":
                combo_items = st.text_area("Combo Items (comma separated)", placeholder="Dog Food, Dog Shampoo, Dog Toy", key="combo_items")
                combo_price = st.number_input("Combo Price ₹", min_value=0.0, value=500.0, step=50.0, key="combo_price")
                offer_description = f"Combo Deal: {combo_items} at ₹{combo_price}"
            elif offer_type == "Free Gift":
                gift_item = st.text_input("Free Gift Item", key="gift_item")
                min_bill = st.number_input("Minimum Bill Amount ₹", min_value=0.0, value=1000.0, step=100.0, key="min_bill")
                offer_description = f"Free {gift_item} on purchase above ₹{min_bill}"
            else:
                offer_description = st.text_area("Custom Offer Description", placeholder="Describe your offer here...", key="custom_offer")
        
        with col2:
            offer_valid_from = st.date_input("Valid From", value=today_dt, key="offer_from")
            offer_valid_till = st.date_input("Valid Till", value=today_dt + timedelta(days=7), key="offer_till")
            
            offer_status = st.radio("Status", ["Active", "Inactive"], horizontal=True, key="offer_status")
            
            st.markdown("### 👁️ Preview")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin-top: 10px;">
                <h3 style="margin: 0 0 10px 0;">🎁 {offer_name if offer_name else 'Your Offer Name'}</h3>
                <p style="margin: 0; font-size: 16px;">{offer_description if offer_description else 'Offer description will appear here'}</p>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Valid: {offer_valid_from.strftime('%d/%m/%Y')} - {offer_valid_till.strftime('%d/%m/%Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("✅ Create Offer", type="primary", use_container_width=True):
                if offer_name and offer_description:
                    offer_data = [
                        offer_name,
                        offer_type,
                        offer_description,
                        offer_valid_from.strftime("%d/%m/%Y"),
                        offer_valid_till.strftime("%d/%m/%Y"),
                        offer_status,
                        st.session_state.username,
                        today_dt.strftime("%d/%m/%Y")
                    ]
                    
                    if save_data("Offers", offer_data):
                        st.success(f"✅ Offer '{offer_name}' created successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Error creating offer!")
                else:
                    st.error("Please fill offer name and description!")
        
        with col2:
            if st.button("📱 Generate WhatsApp Message", use_container_width=True):
                if offer_name and offer_description:
                    wa_msg = f"*🎁 {offer_name.upper()}*\n\n"
                    wa_msg += f"{offer_description}\n\n"
                    wa_msg += f"📅 Valid from {offer_valid_from.strftime('%d/%m/%Y')} to {offer_valid_till.strftime('%d/%m/%Y')}\n\n"
                    wa_msg += f"🐕 Visit LAIKA PET MART today!\n"
                    wa_msg += f"Call us for more details! 📞"
                    
                    st.text_area("WhatsApp Message (Copy & Share)", wa_msg, height=200)
                else:
                    st.error("Please fill offer details first!")
    
    with tab2:
        st.subheader("📋 All Offers")
        
        offers_df = load_data("Offers")
        
        if not offers_df.empty:
            # Filter active offers
            col1, col2 = st.columns(2)
            
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All", "Active", "Inactive"], key="filter_offer_status")
            
            with col2:
                if st.button("🔄 Refresh Offers", key="refresh_offers"):
                    st.rerun()
            
            st.divider()
            
            # Display offers
            for idx, row in offers_df.iterrows():
                if len(row) >= 6:
                    offer_status = row.iloc[5] if len(row) > 5 else "Active"
                    
                    if filter_status == "All" or filter_status == offer_status:
                        status_color = "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)" if offer_status == "Active" else "linear-gradient(135deg, #ff9966 0%, #ff5e62 100%)"
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background: {status_color}; padding: 20px; border-radius: 12px; color: white; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="flex: 1;">
                                        <h3 style="margin: 0 0 10px 0;">🎁 {row.iloc[0]}</h3>
                                        <p style="margin: 0; font-size: 16px;">{row.iloc[2]}</p>
                                        <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">📅 Valid: {row.iloc[3]} - {row.iloc[4]}</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="background: rgba(255,255,255,0.3); padding: 8px 16px; border-radius: 20px; font-weight: bold;">
                                            {offer_status}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([4, 1])
                            
                            with col2:
                                if st.button("🗑️ Delete", key=f"del_offer_{idx}", use_container_width=True):
                                    st.warning("Delete functionality coming soon!")
        else:
            st.info("No offers created yet! Create your first offer above.")

# ==========================================
# MENU 11: LOYALTY POINTS
# ==========================================
elif menu == "⭐ Loyalty Points":
    st.header("⭐ Loyalty Points Management")
    
    st.info("💡 Manually add loyalty points to customers. Points accumulate over time!")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Points", "🔍 Check Points", "📊 All Customers"])
    
    with tab1:
        st.subheader("Add Loyalty Points")
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name", key="loyalty_add_customer")
            points_to_add = st.number_input("Points to Add", min_value=1, value=2, step=1, key="points_add")
        
        with col2:
            points_date = st.date_input("Date", value=today_dt, key="points_date")
            reason = st.text_input("Reason (Optional)", placeholder="e.g., Purchase, Referral, Special bonus", key="points_reason")
        
        # Show current points
        if customer_name:
            current_points = get_customer_loyalty_points(customer_name)
            new_total = current_points + points_to_add
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.9;">Current Points</p>
                    <h2 style="margin: 10px 0; font-size: 28px;">{current_points}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.9;">Adding</p>
                    <h2 style="margin: 10px 0; font-size: 28px;">{points_to_add}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.9;">New Total</p>
                    <h2 style="margin: 10px 0; font-size: 28px;">{new_total}</h2>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        if st.button("✅ Add Points", type="primary", use_container_width=True):
            if not customer_name:
                st.error("Please enter customer name!")
            elif points_to_add <= 0:
                st.error("Please enter valid points!")
            else:
                points_data = [
                    customer_name,
                    points_to_add,
                    points_date.strftime("%d/%m/%Y"),
                    reason if reason else "Manual Entry",
                    st.session_state.username
                ]
                
                if save_data("LoyaltyPoints", points_data):
                    st.success(f"✅ {points_to_add} points added to {customer_name}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error adding points!")
    
    with tab2:
        st.subheader("Check Customer Points")
        
        customer_name = st.text_input("Enter Customer Name", key="loyalty_search")
        
        if st.button("🔍 Search", key="search_loyalty"):
            if customer_name:
                points = get_customer_loyalty_points(customer_name)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 30px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
                    <h3 style="margin: 0;">{customer_name}</h3>
                    <h1 style="margin: 10px 0;">{points} Points</h1>
                </div>
                """, unsafe_allow_html=True)
                
                # Show transaction history
                st.divider()
                st.subheader("📜 Points History")
                
                loyalty_df = load_data("LoyaltyPoints")
                if not loyalty_df.empty:
                    customer_history = loyalty_df[loyalty_df.iloc[:, 0].str.strip().str.upper() == customer_name.strip().upper()]
                    
                    if not customer_history.empty:
                        for idx, row in customer_history.iterrows():
                            points_val = int(pd.to_numeric(row.iloc[1], errors='coerce'))
                            date_val = row.iloc[2] if len(row) > 2 else "N/A"
                            reason_val = row.iloc[3] if len(row) > 3 else "N/A"
                            
                            st.info(f"**{date_val}**: +{points_val} points - {reason_val}")
                    else:
                        st.info("No history found")
            else:
                st.error("Please enter customer name!")
    
    with tab3:
        st.subheader("📊 All Customer Points")
        
        loyalty_df = load_data("LoyaltyPoints")
        
        if not loyalty_df.empty and len(loyalty_df.columns) > 1:
            customer_points = loyalty_df.groupby(loyalty_df.columns[0])[loyalty_df.columns[1]].sum()
            customer_points = customer_points.sort_values(ascending=False)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px;">
                <h3 style="margin: 0;">🏆 Top Loyalty Customers 🏆</h3>
            </div>
            """, unsafe_allow_html=True)
            
            for idx, (customer, points) in enumerate(customer_points.items(), 1):
                # Medal selection
                if idx == 1:
                    medal_icon = "🥇"
                elif idx == 2:
                    medal_icon = "🥈"
                elif idx == 3:
                    medal_icon = "🥉"
                else:
                    medal_icon = "⭐"
                
                # Simple text display using safe conversion
                try:
                    points_val = int(float(points))
                except:
                    points_val = 0
                
                display_text = "{} {}: {} Points".format(medal_icon, customer, points_val)
                st.info(display_text)
        else:
            st.info("No loyalty points data found!")

# ==========================================
# MENU 11: ANALYSIS REPORT
# ==========================================
elif menu == "📈 Analysis Report":
    st.header("📈 Business Analysis Report")
    
    # Date Range Selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_from = st.date_input("From Date", value=today_dt.replace(day=1), key="analysis_from")
    
    with col2:
        analysis_to = st.date_input("To Date", value=today_dt, key="analysis_to")
    
    with col3:
        st.write("")
        st.write("")
        if st.button("📊 Generate Report", type="primary", use_container_width=True):
            st.rerun()
    
    st.divider()
    
    # Load all data
    bills_df = load_data("Bills")
    purchase_df = load_data("Purchases")
    expense_df = load_data("Expenses")
    customer_df = load_data("CustomerKhata")
    supplier_df = load_data("SupplierDues")
    inv_df = load_data("Inventory")
    
    # Calculate metrics for selected period
    period_sales = 0
    period_purchase = 0
    period_expense = 0
    
    if not bills_df.empty and 'Date' in bills_df.columns:
        period_bills = bills_df[(bills_df['Date'] >= analysis_from) & (bills_df['Date'] <= analysis_to)]
        if len(period_bills.columns) > 6:
            period_sales = pd.to_numeric(period_bills.iloc[:, 6], errors='coerce').sum()
    
    if not purchase_df.empty and 'Date' in purchase_df.columns:
        period_purchases = purchase_df[(purchase_df['Date'] >= analysis_from) & (purchase_df['Date'] <= analysis_to)]
        if len(period_purchases.columns) > 5:
            period_purchase = pd.to_numeric(period_purchases.iloc[:, 5], errors='coerce').sum()
    
    if not expense_df.empty and 'Date' in expense_df.columns:
        period_expenses = expense_df[(expense_df['Date'] >= analysis_from) & (expense_df['Date'] <= analysis_to)]
        if len(period_expenses.columns) > 2:
            period_expense = pd.to_numeric(period_expenses.iloc[:, 2], errors='coerce').sum()
    
    period_profit = period_sales - period_purchase - period_expense
    
    # Display Period Summary
    st.subheader(f"📅 Period Summary ({analysis_from.strftime('%d/%m/%Y')} to {analysis_to.strftime('%d/%m/%Y')})")
    
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
            <p style="margin: 0; font-size: 16px;">💰 Total Sales</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{period_sales:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);">
            <p style="margin: 0; font-size: 16px;">📦 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{period_purchase:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(250, 112, 154, 0.4);">
            <p style="margin: 0; font-size: 16px;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{period_expense:,.2f}</h2>
        </div>
        <div style="flex: 1; background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(48, 207, 208, 0.4);">
            <p style="margin: 0; font-size: 16px;">📈 Net Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 32px;">₹{period_profit:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Current Balances & Dues
    st.divider()
    st.subheader("💼 Current Financial Status")
    
    cash_bal = get_current_balance("Cash")
    online_bal = get_current_balance("Online")
    
    # Customer Dues
    total_customer_due = 0
    if not customer_df.empty and len(customer_df.columns) >= 2:
        customer_df_copy = customer_df.copy()
        customer_df_copy.iloc[:, 1] = pd.to_numeric(customer_df_copy.iloc[:, 1], errors='coerce').fillna(0)
        customer_dues = customer_df_copy.groupby(customer_df_copy.columns[0])[customer_df_copy.columns[1]].sum()
        total_customer_due = customer_dues[customer_dues > 0].sum()
    
    # Supplier Dues
    total_supplier_due = 0
    if not supplier_df.empty and len(supplier_df.columns) >= 2:
        supplier_df_copy = supplier_df.copy()
        supplier_df_copy.iloc[:, 1] = pd.to_numeric(supplier_df_copy.iloc[:, 1], errors='coerce').fillna(0)
        supplier_dues = supplier_df_copy.groupby(supplier_df_copy.columns[0])[supplier_df_copy.columns[1]].sum()
        total_supplier_due = supplier_dues[supplier_dues > 0].sum()
    
    # Stock Value
    total_stock_value = 0
    if not inv_df.empty and len(inv_df.columns) > 3:
        latest_stock = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
        latest_stock['qty_val'] = pd.to_numeric(latest_stock.iloc[:, 1], errors='coerce').fillna(0)
        latest_stock['rate_val'] = pd.to_numeric(latest_stock.iloc[:, 3], errors='coerce').fillna(0)
        latest_stock['total_val'] = latest_stock['qty_val'] * latest_stock['rate_val']
        total_stock_value = latest_stock['total_val'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    col1.markdown(f"""
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);">
        <p style="margin: 0; font-size: 16px;">💵 Cash in Hand</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{cash_bal:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);">
        <p style="margin: 0; font-size: 16px;">🏦 Online Balance</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{online_bal:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col3.markdown(f"""
    <div style="background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(255, 153, 102, 0.4);">
        <p style="margin: 0; font-size: 16px;">📦 Stock Value</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{total_stock_value:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    
    col1.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(255, 216, 155, 0.4);">
        <p style="margin: 0; font-size: 16px;">📒 Customer Dues (Receivable)</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{total_customer_due:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 4px 15px rgba(250, 112, 154, 0.4);">
        <p style="margin: 0; font-size: 16px;">🏢 Supplier Dues (Payable)</p>
        <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{total_supplier_due:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Insights
    st.divider()
    st.subheader("💡 Key Insights")
    
    profit_margin = (period_profit / period_sales * 100) if period_sales > 0 else 0
    net_working_capital = cash_bal + online_bal + total_customer_due - total_supplier_due
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white;">
            <h4 style="margin: 0 0 15px 0;">📊 Performance Metrics</h4>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Profit Margin:** {profit_margin:.2f}%")
        st.markdown(f"**Sales per Day:** ₹{period_sales / max((analysis_to - analysis_from).days + 1, 1):,.2f}")
        
        if period_sales > 0:
            st.markdown(f"**Expense Ratio:** {(period_expense/period_sales*100):.2f}%")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; color: white;">
            <h4 style="margin: 0 0 15px 0;">💼 Financial Health</h4>
            <p style="margin: 5px 0;"><strong>Net Working Capital:</strong> ₹{net_working_capital:,.2f}</p>
            <p style="margin: 5px 0;"><strong>Total Assets:</strong> ₹{cash_bal + online_bal + total_stock_value:,.2f}</p>
            <p style="margin: 5px 0;"><strong>Current Ratio:</strong> {((cash_bal + online_bal + total_customer_due) / max(total_supplier_due, 1)):.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Top Performers
    st.divider()
    st.subheader("🏆 Top Performers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Top Customers")
        if not bills_df.empty and 'Date' in bills_df.columns:
            period_bills = bills_df[(bills_df['Date'] >= analysis_from) & (bills_df['Date'] <= analysis_to)]
            if not period_bills.empty and len(period_bills.columns) > 6:
                customer_sales = period_bills.groupby(period_bills.columns[1])[period_bills.columns[6]].apply(lambda x: pd.to_numeric(x, errors='coerce').sum())
                top_customers = customer_sales.nlargest(5)
                
                for idx, (customer, amount) in enumerate(top_customers.items(), 1):
                    medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "⭐"
                    st.success(f"{medal} **{customer}**: ₹{amount:,.2f}")
            else:
                st.info("No customer data for this period")
        else:
            st.info("No customer data available")
    
    with col2:
        st.markdown("#### 🛍️ Top Selling Products")
        if not bills_df.empty and 'Date' in bills_df.columns:
            period_bills = bills_df[(bills_df['Date'] >= analysis_from) & (bills_df['Date'] <= analysis_to)]
            if not period_bills.empty and len(period_bills.columns) > 6:
                product_sales = period_bills.groupby(period_bills.columns[3])[period_bills.columns[6]].apply(lambda x: pd.to_numeric(x, errors='coerce').sum())
                top_products = product_sales.nlargest(5)
                
                for idx, (product, amount) in enumerate(top_products.items(), 1):
                    medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "⭐"
                    st.success(f"{medal} **{product}**: ₹{amount:,.2f}")
            else:
                st.info("No product data for this period")
        else:
            st.info("No product data available")


# ==========================================
# MENU 13: FINANCIAL REPORTS
# ==========================================
elif menu == "📑 Financial Reports":
    st.header("📑 Financial Reports")
    
    st.info("💼 Professional accounting reports for your business")
    
    # Report Selection
    report_type = st.selectbox("Select Report Type", 
                               ["Profit & Loss Statement", "Balance Sheet"],
                               key="financial_report_type")
    
    # Date Range
    col1, col2 = st.columns(2)
    
    with col1:
        fin_from = st.date_input("From Date", value=today_dt.replace(day=1), key="fin_from")
    
    with col2:
        fin_to = st.date_input("To Date", value=today_dt, key="fin_to")
    
    st.divider()
    
    # Load Data
    bills_df = load_data("Bills")
    purchase_df = load_data("Purchases")
    expense_df = load_data("Expenses")
    services_df = load_data("Services")
    customer_df = load_data("CustomerKhata")
    supplier_df = load_data("SupplierDues")
    inv_df = load_data("Inventory")
    
    # ==========================================
    # PROFIT & LOSS
    # ==========================================
    if report_type == "Profit & Loss Statement":
        st.subheader(f"📊 Profit & Loss Statement")
        st.caption(f"Period: {fin_from.strftime('%d/%m/%Y')} to {fin_to.strftime('%d/%m/%Y')}")
        st.divider()
        
        # Calculate Income
        sales_income = 0
        if not bills_df.empty and 'Date' in bills_df.columns:
            period_bills = bills_df[(bills_df['Date'] >= fin_from) & (bills_df['Date'] <= fin_to)]
            if len(period_bills.columns) > 6:
                sales_income = pd.to_numeric(period_bills.iloc[:, 6], errors='coerce').sum()
        
        service_income = 0
        if not services_df.empty and 'Date' in services_df.columns:
            period_services = services_df[(services_df['Date'] >= fin_from) & (services_df['Date'] <= fin_to)]
            if len(period_services.columns) > 6:
                service_income = pd.to_numeric(period_services.iloc[:, 6], errors='coerce').sum()
        
        total_income = sales_income + service_income
        
        # Display Income
        st.markdown("### 💰 INCOME")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Product Sales")
        with col2:
            st.write(f"₹{sales_income:,.2f}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Service Revenue")
        with col2:
            st.write(f"₹{service_income:,.2f}")
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**TOTAL INCOME**")
        with col2:
            st.markdown(f"**₹{total_income:,.2f}**")
        
        st.divider()
        
        # Calculate COGS
        cogs = 0
        if not purchase_df.empty and 'Date' in purchase_df.columns:
            period_purchases = purchase_df[(purchase_df['Date'] >= fin_from) & (purchase_df['Date'] <= fin_to)]
            if len(period_purchases.columns) > 5:
                cogs = pd.to_numeric(period_purchases.iloc[:, 5], errors='coerce').sum()
        
        st.markdown("### 📦 COST OF GOODS SOLD")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Purchases")
        with col2:
            st.write(f"₹{cogs:,.2f}")
        
        gross_profit = total_income - cogs
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**GROSS PROFIT**")
        with col2:
            st.markdown(f"**₹{gross_profit:,.2f}**")
        
        st.divider()
        
        # Calculate Expenses
        st.markdown("### 💸 OPERATING EXPENSES")
        
        total_expenses = 0
        if not expense_df.empty and 'Date' in expense_df.columns:
            period_expenses = expense_df[(expense_df['Date'] >= fin_from) & (expense_df['Date'] <= fin_to)]
            if len(period_expenses.columns) > 2:
                expense_by_cat = period_expenses.groupby(period_expenses.columns[1])[period_expenses.columns[2]].apply(
                    lambda x: pd.to_numeric(x, errors='coerce').sum()
                )
                
                for category, amount in expense_by_cat.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"{category}")
                    with col2:
                        st.write(f"₹{amount:,.2f}")
                    total_expenses += amount
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**TOTAL EXPENSES**")
        with col2:
            st.markdown(f"**₹{total_expenses:,.2f}**")
        
        st.divider()
        
        # NET PROFIT
        net_profit = gross_profit - total_expenses
        profit_margin = (net_profit/total_income*100) if total_income > 0 else 0
        
        st.markdown("### 📈 NET PROFIT/LOSS")
        
        profit_color = "#43e97b 0%, #38f9d7" if net_profit >= 0 else "#ff9966 0%, #ff5e62"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {profit_color} 100%); padding: 30px; border-radius: 12px; text-align: center; color: white; margin: 20px 0;">
            <h2 style="margin: 0;">{"NET PROFIT" if net_profit >= 0 else "NET LOSS"}</h2>
            <h1 style="margin: 10px 0; font-size: 48px;">₹{abs(net_profit):,.2f}</h1>
            <p style="margin: 0; opacity: 0.9;">Profit Margin: {profit_margin:.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Ratios
        st.divider()
        st.markdown("### 📊 Financial Ratios")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gross_margin = (gross_profit/total_income*100) if total_income > 0 else 0
            st.metric("Gross Margin", f"{gross_margin:.2f}%")
        
        with col2:
            st.metric("Net Margin", f"{profit_margin:.2f}%")
        
        with col3:
            expense_ratio = (total_expenses/total_income*100) if total_income > 0 else 0
            st.metric("Expense Ratio", f"{expense_ratio:.2f}%")
    
    # ==========================================
    # BALANCE SHEET
    # ==========================================
    else:
        st.subheader(f"📊 Balance Sheet")
        st.caption(f"As on {fin_to.strftime('%d/%m/%Y')}")
        st.divider()
        
        # ASSETS
        st.markdown("### 💎 ASSETS")
        
        # Cash
        cash_bal = get_current_balance("Cash")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Cash in Hand")
        with col2:
            st.write(f"₹{cash_bal:,.2f}")
        
        # Online/Bank
        online_bal = get_current_balance("Online")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Bank Balance")
        with col2:
            st.write(f"₹{online_bal:,.2f}")
        
        # Customer Dues (Receivable)
        receivable = 0
        if not customer_df.empty and len(customer_df.columns) >= 2:
            cust_copy = customer_df.copy()
            cust_copy.iloc[:, 1] = pd.to_numeric(cust_copy.iloc[:, 1], errors='coerce').fillna(0)
            cust_dues = cust_copy.groupby(cust_copy.columns[0])[cust_copy.columns[1]].sum()
            receivable = cust_dues[cust_dues > 0].sum()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Accounts Receivable")
        with col2:
            st.write(f"₹{receivable:,.2f}")
        
        # Inventory
        inventory_val = 0
        if not inv_df.empty and len(inv_df.columns) > 3:
            latest = inv_df.groupby(inv_df.iloc[:, 0]).tail(1)
            latest['qty'] = pd.to_numeric(latest.iloc[:, 1], errors='coerce').fillna(0)
            latest['rate'] = pd.to_numeric(latest.iloc[:, 3], errors='coerce').fillna(0)
            latest['total'] = latest['qty'] * latest['rate']
            inventory_val = latest['total'].sum()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Inventory/Stock")
        with col2:
            st.write(f"₹{inventory_val:,.2f}")
        
        total_assets = cash_bal + online_bal + receivable + inventory_val
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**TOTAL ASSETS**")
        with col2:
            st.markdown(f"**₹{total_assets:,.2f}**")
        
        st.divider()
        
        # LIABILITIES
        st.markdown("### 📋 LIABILITIES")
        
        # Supplier Dues (Payable)
        payable = 0
        if not supplier_df.empty and len(supplier_df.columns) >= 2:
            supp_copy = supplier_df.copy()
            supp_copy.iloc[:, 1] = pd.to_numeric(supp_copy.iloc[:, 1], errors='coerce').fillna(0)
            supp_dues = supp_copy.groupby(supp_copy.columns[0])[supp_copy.columns[1]].sum()
            payable = supp_dues[supp_dues > 0].sum()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Accounts Payable")
        with col2:
            st.write(f"₹{payable:,.2f}")
        
        total_liabilities = payable
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**TOTAL LIABILITIES**")
        with col2:
            st.markdown(f"**₹{total_liabilities:,.2f}**")
        
        st.divider()
        
        # EQUITY
        st.markdown("### 👤 OWNER'S EQUITY")
        
        equity = total_assets - total_liabilities
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Owner's Equity")
        with col2:
            st.write(f"₹{equity:,.2f}")
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**TOTAL EQUITY**")
        with col2:
            st.markdown(f"**₹{equity:,.2f}**")
        
        st.divider()
        
        # Balance Check
        st.markdown("### ⚖️ ACCOUNTING EQUATION")
        
        liabilities_equity = total_liabilities + equity
        balanced = abs(total_assets - liabilities_equity) < 1
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; text-align: center; color: white;">
            <h3 style="margin: 0;">Assets = Liabilities + Equity</h3>
            <h2 style="margin: 10px 0;">₹{total_assets:,.2f} = ₹{total_liabilities:,.2f} + ₹{equity:,.2f}</h2>
            <p style="margin: 0; font-size: 18px;">{"✅ Balanced" if balanced else "⚠️ Check Data"}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Financial Health
        st.divider()
        st.markdown("### 📊 Financial Health")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_ratio = (total_assets/total_liabilities) if total_liabilities > 0 else 0
            st.metric("Current Ratio", f"{current_ratio:.2f}", help="Should be > 1.5")
        
        with col2:
            quick_ratio = ((cash_bal + online_bal + receivable)/total_liabilities) if total_liabilities > 0 else 0
            st.metric("Quick Ratio", f"{quick_ratio:.2f}", help="Should be > 1.0")
        
        with col3:
            debt_ratio = (total_liabilities/total_assets) if total_assets > 0 else 0
            st.metric("Debt Ratio", f"{debt_ratio:.2f}", help="Lower is better")
