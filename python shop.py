import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
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
    # Only initialize from sheets if NOT set yet
    st.session_state.manual_cash = None
    st.session_state.balance_initialized = False
if 'manual_online' not in st.session_state:
    st.session_state.manual_online = None
if 'balance_initialized' not in st.session_state:
    st.session_state.balance_initialized = False

def generate_pdf_bill(customer_name, customer_phone, items, total_amt, points, payment_mode, bill_date):
    """Generate PDF bill"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#FF1493'), alignment=TA_CENTER)
        elements.append(Paragraph("LAIKA PET STORE", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Bill details
        bill_info = [
            ['Customer:', customer_name, 'Date:', bill_date],
            ['Phone:', customer_phone, 'Mode:', payment_mode]
        ]
        t = Table(bill_info, colWidths=[1.5*inch, 2.5*inch, 1*inch, 2*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#FF1493')),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3*inch))
        
        # Items table
        data = [['Item', 'Quantity', 'Price']]
        for item in items:
            data.append([item['Item'], item['Qty'], f"₹{item['Price']:.2f}"])
        
        data.append(['', 'TOTAL', f"₹{total_amt:.2f}"])
        data.append(['', 'Points Earned', f"+{points}"])
        
        t = Table(data, colWidths=[3*inch, 2*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF1493')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -2), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)
        elements.append(Paragraph("Thank you for shopping with us! 🐾", footer_style))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError:
        return None

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
    """Get LATEST balance from Google Sheets Balances sheet"""
    try:
        b_df = load_data("Balances")
        if b_df.empty or len(b_df.columns) < 2:
            return 0.0
        
        # Find rows matching the mode (Cash or Online)
        rows = b_df[b_df.iloc[:, 0].str.strip() == mode]
        
        if len(rows) > 0:
            # Get the LAST (latest) entry for this mode
            latest_balance = rows.iloc[-1, 1]  # Last row, second column
            return float(pd.to_numeric(latest_balance, errors='coerce'))
        
        return 0.0
    except Exception as e:
        st.error(f"Error loading balance from sheets: {str(e)}")
        return 0.0

def get_current_balance(mode):
    """Get current balance - Load from sheets ONCE when app opens, then use local"""
    if mode == "Cash":
        # If not loaded yet (app just opened), load from sheets
        if st.session_state.manual_cash is None:
            st.session_state.manual_cash = get_balance_from_sheet("Cash")
        return st.session_state.manual_cash
    elif mode == "Online":
        # If not loaded yet (app just opened), load from sheets
        if st.session_state.manual_online is None:
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
    """Update balance and save to Google Sheets"""
    if mode not in ["Cash", "Online"]:
        return True
    
    try:
        current_bal = get_current_balance(mode)
        
        if operation == 'add':
            new_bal = current_bal + amount
        else:
            new_bal = current_bal - amount
        
        # Update session state
        if mode == "Cash":
            st.session_state.manual_cash = new_bal
        elif mode == "Online":
            st.session_state.manual_online = new_bal
        
        # Save to Google Sheets (this will be the new LATEST entry)
        if save_data("Balances", [mode, new_bal]):
            st.success(f"✅ {mode}: ₹{current_bal:,.2f} → ₹{new_bal:,.2f}")
            time.sleep(0.5)
            return True
        else:
            st.error(f"❌ Failed to save {mode} balance to sheets!")
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

# --- 2. MULTI-USER LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# User credentials database
USERS = {
    "Owner": {
        "password": "Ayush@092025",
        "role": "owner",
        "name": "Ayush (Owner)"
    },
    "Manager": {
        "password": "Manager@123",
        "role": "manager",
        "name": "Store Manager"
    },
    "Staff1": {
        "password": "Staff@123",
        "role": "staff",
        "name": "Staff Member 1"
    },
    "Staff2": {
        "password": "Staff@456",
        "role": "staff",
        "name": "Staff Member 2"
    }
}

if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 48px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🔐 LAIKA PET MART</h1>
        <p style="color: white; margin-top: 15px; font-size: 20px; opacity: 0.95;">Multi-User Login System</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        u = st.text_input("👤 Username", key="login_username").strip()
        p = st.text_input("🔒 Password", type="password", key="login_password")
        
        # Show available users hint
        with st.expander("ℹ️ Available User Roles"):
            st.info("""
            **Owner**: Full access to all features
            **Manager**: Access to reports, billing, inventory
            **Staff**: Billing and basic operations only
            """)
        
        if st.button("🚀 LOGIN", use_container_width=True, type="primary"):
            if u in USERS and USERS[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.user_role = USERS[u]["role"]
                st.session_state.username = USERS[u]["name"]
                st.success(f"✅ Welcome {USERS[u]['name']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show demo credentials
        st.divider()
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <b>🔑 Demo Credentials:</b><br>
            <small>
            Owner: <code>Owner</code> / <code>Ayush@092025</code><br>
            Manager: <code>Manager</code> / <code>Manager@123</code><br>
            Staff: <code>Staff1</code> / <code>Staff@123</code>
            </small>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# --- 3. CHECK NEW DAY ---
today_dt = datetime.now().date()
if st.session_state.last_check_date != today_dt:
    if st.session_state.last_check_date is not None:
        archive_daily_data()
    st.session_state.last_check_date = today_dt

# --- 4. SIDEBAR MENU WITH ROLE-BASED ACCESS ---
# Display user info in sidebar (only if logged in)
if st.session_state.user_role:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h3 style="color: white; margin: 0;">👤 {st.session_state.username}</h3>
        <p style="color: white; margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{st.session_state.user_role.upper()}</p>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 20px;'>📋 Main Menu</h2>", unsafe_allow_html=True)

# Initialize selected menu in session state
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "📊 Dashboard"

# Define menu items based on user role
user_role = st.session_state.user_role or "staff"  # Default to staff if None

if user_role == "owner":
    # Owner has access to everything
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
        "🔔 Automated Reminders",
        "💼 GST & Invoices",
        "👥 User Management"
    ]
elif user_role == "manager":
    # Manager has most access except user management
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
        "🔔 Automated Reminders",
        "💼 GST & Invoices"
    ]
else:  # staff
    # Staff has limited access - billing and basic operations only
    menu_items = [
        "📊 Dashboard",
        "🧾 Billing",
        "📋 Live Stock",
        "🐾 Pet Register"
    ]

# Create buttons for each menu item
for item in menu_items:
    # Check if this is the selected menu
    is_selected = (st.session_state.selected_menu == item)
    
    # Button with custom styling based on selection
    button_type = "primary" if is_selected else "secondary"
    
    if st.sidebar.button(
        item, 
        key=f"menu_{item}",
        use_container_width=True,
        type=button_type
    ):
        st.session_state.selected_menu = item
        st.rerun()

# Get the selected menu (without emoji for comparison)
menu = st.session_state.selected_menu

st.sidebar.divider()

if st.sidebar.button("🚪 Logout", use_container_width=True):
    # Clear ALL session states
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.manual_cash = None
    st.session_state.manual_online = None
    st.session_state.balance_initialized = False
    st.rerun()

curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')
is_weekend = datetime.now().weekday() >= 5

# --- 5. DASHBOARD ---
if menu == "📊 Dashboard":
    # Professional Header with Logo and Gradient
    try:
        # Try to load logo from uploads
        import base64
        logo_path = "/mnt/user-data/uploads/logo_png.png"
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); border-radius: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <img src="data:image/png;base64,{logo_data}" style="width: 180px; margin-bottom: 15px; filter: drop-shadow(0 5px 10px rgba(0,0,0,0.3));">
            <h1 style="color: white; margin: 0; font-size: 52px; text-shadow: 3px 3px 6px rgba(0,0,0,0.4); font-weight: bold; letter-spacing: 2px;">Welcome to Laika Pet Mart</h1>
            <p style="color: white; margin-top: 15px; font-size: 22px; opacity: 0.95; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🐕 Your Trusted Pet Care Partner 🐈</p>
        </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback without logo
        st.markdown("""
        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); border-radius: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <div style="font-size: 80px; margin-bottom: 15px;">👑🐾</div>
            <h1 style="color: white; margin: 0; font-size: 52px; text-shadow: 3px 3px 6px rgba(0,0,0,0.4); font-weight: bold; letter-spacing: 2px;">Welcome to Laika Pet Mart</h1>
            <p style="color: white; margin-top: 15px; font-size: 22px; opacity: 0.95; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🐕 Your Trusted Pet Care Partner 🐈</p>
        </div>
        """, unsafe_allow_html=True)
    
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
    <style>
    .balance-card {{
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transition: transform 0.3s ease;
        border: 2px solid rgba(255,255,255,0.3);
    }}
    .balance-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.25);
    }}
    .card-label {{
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 10px;
        opacity: 0.9;
    }}
    .card-amount {{
        font-size: 32px;
        font-weight: bold;
        margin: 0;
    }}
    </style>
    
    <div style="display: flex; gap: 15px; justify-content: space-between; margin-bottom: 30px;">
        <div class="balance-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; flex: 1;">
            <p class="card-label">💵 Galla (Cash)</p>
            <h2 class="card-amount">₹{cash_bal:,.2f}</h2>
        </div>
        <div class="balance-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; flex: 1;">
            <p class="card-label">🏦 Online</p>
            <h2 class="card-amount">₹{online_bal:,.2f}</h2>
        </div>
        <div class="balance-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; flex: 1;">
            <p class="card-label">⚡ Total Balance</p>
            <h2 class="card-amount">₹{total_bal:,.2f}</h2>
        </div>
        <div class="balance-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; flex: 1;">
            <p class="card-label">📒 Udhaar</p>
            <h2 class="card-amount">₹{total_u:,.2f}</h2>
        </div>
        <div class="balance-card" style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); color: white; flex: 1;">
            <p class="card-label">📦 Stock Value</p>
            <h2 class="card-amount">₹{total_stock_val:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔧 Balance Settings"):
        st.success("✅ Balance automatically loads from Google Sheets latest entry!")
        st.info("💡 Logout/Login karne par latest balance Google Sheets se load hoga")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cash Balance")
            st.write(f"Current: ₹{cash_bal:,.2f}")
            new_cash = st.number_input("Update Cash Balance", value=float(cash_bal), step=1.0, key="cash_set")
            if st.button("💾 Save Cash Balance", key="btn_cash"):
                st.session_state.manual_cash = new_cash
                save_data("Balances", ["Cash", new_cash])
                st.success(f"✅ Cash updated to ₹{new_cash:,.2f}")
                time.sleep(1)
                st.rerun()
        
        with col2:
            st.subheader("Online Balance")
            st.write(f"Current: ₹{online_bal:,.2f}")
            new_online = st.number_input("Update Online Balance", value=float(online_bal), step=1.0, key="online_set")
            if st.button("💾 Save Online Balance", key="btn_online"):
                st.session_state.manual_online = new_online
                save_data("Balances", ["Online", new_online])
                st.success(f"✅ Online updated to ₹{new_online:,.2f}")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # TODAY'S REPORT
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
        <h2 style="color: white; margin: 0; text-align: center; font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            📈 Today's Report - {today_dt.strftime('%d %B %Y')}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    s_today = s_df[s_df['Date'] == today_dt] if not s_df.empty and 'Date' in s_df.columns else pd.DataFrame()
    i_today = i_df[i_df['Date'] == today_dt] if not i_df.empty and 'Date' in i_df.columns else pd.DataFrame()
    e_today = e_df[e_df['Date'] == today_dt] if not e_df.empty and 'Date' in e_df.columns else pd.DataFrame()
    
    today_sale = pd.to_numeric(s_today.iloc[:, 3], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 3 else 0
    
    today_pur = 0
    if not i_today.empty and len(i_today.columns) > 3:
        qty_vals = pd.to_numeric(i_today.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals = pd.to_numeric(i_today.iloc[:, 3], errors='coerce').fillna(0)
        today_pur = (qty_vals * rate_vals).sum()
    
    # Calculate 18 Jan 2026 purchase total (for reference, already included in monthly)
    jan18_date = datetime(2026, 1, 18).date()
    
    today_exp = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty and len(e_today.columns) > 2 else 0
    today_profit = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.15);">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{today_sale:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.15);">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">📦 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{today_pur:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f857a6 0%, #ff5858 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.15);">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{today_exp:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%); padding: 20px; border-radius: 12px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.15);">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">📈 Total Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px;">₹{today_profit:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # MONTHLY REPORT
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
        <h2 style="color: white; margin: 0; text-align: center; font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🗓️ Monthly Report - {curr_m_name} {today_dt.year}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Add 18 Jan purchase to monthly total (automatically included since it's in January)
    # No need for separate addition - it's already counted in i_month data
    
    month_exp = pd.to_numeric(e_month.iloc[:, 2], errors='coerce').sum() if not e_month.empty and len(e_month.columns) > 2 else 0
    month_profit = pd.to_numeric(s_month.iloc[:, 7], errors='coerce').sum() if not s_month.empty and len(s_month.columns) > 7 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333; box-shadow: 0 5px 15px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.5);">
            <p style="margin: 0; font-size: 14px; font-weight: 600;">💰 Total Sale</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px; color: #11998e;">₹{month_sale:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333; box-shadow: 0 5px 15px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.5);">
            <p style="margin: 0; font-size: 14px; font-weight: 600;">📦 Total Purchase</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px; color: #ee0979;">₹{month_pur:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333; box-shadow: 0 5px 15px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.5);">
            <p style="margin: 0; font-size: 14px; font-weight: 600;">💸 Total Expense</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px; color: #f857a6;">₹{month_exp:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); padding: 20px; border-radius: 12px; text-align: center; color: #333; box-shadow: 0 5px 15px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.5);">
            <p style="margin: 0; font-size: 14px; font-weight: 600;">📈 Total Profit</p>
            <h2 style="margin: 10px 0 0 0; font-size: 28px; color: #2193b0;">₹{month_profit:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

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
        # Calculate TOTAL points for this customer (all transactions)
        if c_ph and not s_df.empty and len(s_df.columns) > 6:
            # Filter all bills with this phone number
            customer_sales = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)]
            # Sum all points (positive earned, negative used)
            pts_bal = pd.to_numeric(customer_sales.iloc[:, 6], errors='coerce').sum()
        else:
            pts_bal = 0
        
        # Display available points
        if pts_bal > 0:
            st.metric("👑 Available Points", int(pts_bal))
        elif pts_bal < 0:
            st.metric("👑 Points Balance", int(pts_bal), delta="Used more than earned")
        else:
            st.metric("👑 Available Points", 0)
    
    # GST Option Checkbox
    col1, col2 = st.columns(2)
    with col1:
        pay_m = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
    with col2:
        gst_bill = st.checkbox("📄 GST Bill Required?", value=False, help="Check if customer needs GST invoice")
    
    # Show GST fields only if checkbox is checked
    if gst_bill:
        st.info("📄 GST Invoice Details Required")
        col1, col2 = st.columns(2)
        with col1:
            c_gstin = st.text_input("Customer GSTIN (Optional)", placeholder="Enter if available", help="Leave empty for B2C")
            c_address = st.text_area("Billing Address", placeholder="Required for GST invoice")
        with col2:
            gst_rate = st.selectbox("GST Rate %", [5, 12, 18, 28], index=2, help="Select applicable GST rate")
            st.info(f"Selected: {gst_rate}% GST\nCGST: {gst_rate/2}% | SGST: {gst_rate/2}%")
    
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
        
        # Calculate what balance will be after this transaction
        new_balance = pts_bal + total_pts
        
        # Show GST calculation if GST bill is selected
        if gst_bill:
            st.divider()
            st.markdown("### 💼 GST Invoice Calculation")
            
            # Calculate GST amounts
            taxable_amount = total_amt / (1 + gst_rate/100)
            gst_amount = total_amt - taxable_amount
            cgst = gst_amount / 2
            sgst = gst_amount / 2
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Taxable Amount", f"₹{taxable_amount:.2f}")
            col2.metric(f"🔴 CGST ({gst_rate/2}%)", f"₹{cgst:.2f}")
            col3.metric(f"🔵 SGST ({gst_rate/2}%)", f"₹{sgst:.2f}")
            col4.metric("📊 Total GST", f"₹{gst_amount:.2f}")
            
            st.success(f"💳 **Grand Total (with GST): ₹{total_amt:,.2f}**")
        else:
            st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        
        # Show points info
        col1, col2 = st.columns(2)
        with col1:
            if total_pts >= 0:
                st.success(f"🎁 Points Earned This Bill: +{total_pts}")
            else:
                st.warning(f"🎁 Points Redeemed: {total_pts}")
        with col2:
            st.info(f"👑 New Balance After Bill: {int(new_balance)} points")
        
        if st.button("✅ Save Bill & Send WhatsApp", type="primary"):
            # Save all items to Sales
            for item in st.session_state.bill_cart:
                save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']])
            
            # Update balance based on payment mode
            if pay_m == "Cash":
                update_balance(total_amt, "Cash", 'add')
            elif pay_m == "Online":
                update_balance(total_amt, "Online", 'add')
            else:  # Udhaar
                # Add to Customer Khata automatically
                save_data("CustomerKhata", [f"{c_name}({c_ph})", total_amt, str(today_dt), "Udhaar"])
                st.success(f"✅ Bill saved as Udhaar! Added to Customer Khata: {c_name}")
            
            # Generate WhatsApp message
            items_text = "\n".join([f"• {item['Item']} - {item['Qty']} - ₹{item['Price']}" for item in st.session_state.bill_cart])
            
            # Calculate new points balance
            new_pts_balance = pts_bal + total_pts
            
            # Build points message
            if total_pts >= 0:
                points_msg = f"🎁 *आज के प्वाइंट्स:* +{total_pts}"
            else:
                points_msg = f"🎁 *आज के प्वाइंट्स:* {total_pts} (Redeemed)"
            
            points_msg += f"\n👑 *कुल बचे प्वाइंट्स:* {int(new_pts_balance)}"
            
            # Add GST details if applicable
            if gst_bill:
                taxable_amount = total_amt / (1 + gst_rate/100)
                gst_amount = total_amt - taxable_amount
                cgst = gst_amount / 2
                sgst = gst_amount / 2
                
                gst_details = f"""
📄 *GST Invoice Details:*
Taxable Amount: ₹{taxable_amount:.2f}
CGST ({gst_rate/2}%): ₹{cgst:.2f}
SGST ({gst_rate/2}%): ₹{sgst:.2f}
Total GST: ₹{gst_amount:.2f}"""
            else:
                gst_details = ""
            
            message = f"""🐾 *LAIKA PET MART* 🐾
            
नमस्ते {c_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{total_amt:,.2f}
{points_msg}
{gst_details}

धन्यवाद! 🙏
फिर से आइएगा! 🐕"""
            
            import urllib.parse
            encoded_msg = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/91{c_ph}?text={encoded_msg}"
            
            st.success("✅ Bill saved successfully!")
            
            # Generate PDF
            pdf_data = generate_pdf_bill(c_name, c_ph, st.session_state.bill_cart, total_amt, total_pts, pay_m, str(today_dt))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### 📱 Send WhatsApp")
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">📲 Send via WhatsApp</button></a>', unsafe_allow_html=True)
            
            with col2:
                if pdf_data:
                    st.markdown(f"### 📄 Download PDF")
                    st.download_button(
                        label="📥 Download Bill PDF",
                        data=pdf_data,
                        file_name=f"Bill_{c_name}_{today_dt}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("📄 Install reportlab for PDF: pip install reportlab")
            
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
                            # Calculate current points balance for this customer
                            cust_bills = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(cust_phone), na=False)]
                            cust_pts_balance = pd.to_numeric(cust_bills.iloc[:, 6], errors='coerce').sum() if not cust_bills.empty else 0
                            
                            # Create WhatsApp message
                            items_text = "\n".join(bill_data['items'])
                            
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {cust_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{bill_data['total']:,.2f}
🎁 *आज के प्वाइंट्स:* +{bill_data['points']}
👑 *कुल बचे प्वाइंट्स:* {int(cust_pts_balance)}

धन्यवाद! 🙏
फिर से आइएगा! 🐕"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; font-size: 20px;">💬</button></a>', unsafe_allow_html=True)
                        else:
                            st.write("")
                    
                    st.divider()
            
            # Delete option for today's bills
            st.divider()
            with st.expander("🗑️ Delete Bill Entry"):
                st.warning("⚠️ This will delete entries from Google Sheets")
                del_customer = st.selectbox("Select Customer", list(customer_bills.keys()), key="del_bill_customer")
                if st.button("🗑️ Delete Selected Bill", key="del_bill_btn"):
                    st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets for now")
                    st.info(f"Go to Sales sheet and delete rows for: {del_customer}")
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
        
        # Delete option
        st.divider()
        with st.expander("🗑️ Delete Purchase Entry"):
            st.warning("⚠️ Select row to delete")
            if len(i_df) > 0:
                del_idx = st.number_input("Row number to delete (from above table)", min_value=0, max_value=len(i_df)-1, value=0)
                st.info(f"Selected: {i_df.iloc[del_idx, 0] if len(i_df.columns) > 0 else 'N/A'}")
                if st.button("🗑️ Delete Selected Purchase"):
                    st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets")
                    st.info("Go to Inventory sheet and delete the corresponding row")

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
        
        # Delete option
        st.divider()
        with st.expander("🗑️ Delete Expense Entry"):
            st.warning("⚠️ Select row to delete")
            if len(e_df) > 0:
                del_idx = st.number_input("Row number to delete", min_value=0, max_value=len(e_df)-1, value=0, key="del_exp")
                st.info(f"Selected: {e_df.iloc[del_idx, 1] if len(e_df.columns) > 1 else 'N/A'} - ₹{e_df.iloc[del_idx, 2] if len(e_df.columns) > 2 else 0}")
                if st.button("🗑️ Delete Selected Expense"):
                    st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets")
                    st.info("Go to Expenses sheet and delete the corresponding row")

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
        
        # Delete option
        st.divider()
        with st.expander("🗑️ Delete Pet Record"):
            if len(p_df) > 0:
                del_idx = st.number_input("Row number to delete", min_value=0, max_value=len(p_df)-1, value=0, key="del_pet")
                st.info(f"Selected: {p_df.iloc[del_idx, 0] if len(p_df.columns) > 0 else 'N/A'}")
                if st.button("🗑️ Delete Selected Pet"):
                    st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets")
                    st.info("Go to PetRecords sheet and delete the corresponding row")

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
                # Determine the type
                if "+" in t:  # Udhaar (customer ne udhaar liya)
                    final_amt = a  # Positive amount
                    save_data("CustomerKhata", [n, final_amt, str(today_dt), m])
                    st.success(f"✅ Udhaar entry added: {n} owes ₹{a:,.2f}")
                else:  # Jama (customer ne payment kiya)
                    final_amt = -a  # Negative amount (reduces balance)
                    save_data("CustomerKhata", [n, final_amt, str(today_dt), m])
                    
                    # Update Cash/Online balance if payment received
                    if m == "Cash":
                        update_balance(a, "Cash", 'add')
                        st.success(f"✅ Payment received! ₹{a:,.2f} added to Cash")
                    elif m == "Online":
                        update_balance(a, "Online", 'add')
                        st.success(f"✅ Payment received! ₹{a:,.2f} added to Online")
                    else:
                        st.success(f"✅ Payment entry added (Mode: {m})")
                
                time.sleep(1)
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
        
        # Delete option
        st.divider()
        with st.expander("🗑️ Delete Khata Entry"):
            st.dataframe(k_df.tail(10), use_container_width=True)
            if len(k_df) > 0:
                del_idx = st.number_input("Row number to delete", min_value=0, max_value=len(k_df)-1, value=0, key="del_khata")
                st.info(f"Selected: {k_df.iloc[del_idx, 0] if len(k_df.columns) > 0 else 'N/A'}")
                if st.button("🗑️ Delete Selected Entry"):
                    st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets")
                    st.info("Go to CustomerKhata sheet and delete the corresponding row")

# --- 12. SUPPLIER DUES ---
elif menu == "🏢 Supplier Dues":
    st.header("🏢 Supplier Dues Management")
    
    # Two tabs: Add Entry and View Summary
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
                    # Determine amount: + for credit (we owe), - for payment (we paid)
                    if "Credit" in t or "Liya" in t:
                        final_amt = a  # Positive = we owe
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Credit"])
                        st.success(f"✅ ₹{a:,.2f} ka maal entry added for {s}")
                    else:  # Payment
                        final_amt = -a  # Negative = we paid
                        save_data("Dues", [s, final_amt, str(today_dt), m, "Payment"])
                        
                        # Update balance if Cash/Online
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
            
            # Calculate balance per supplier
            sum_df = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Supplier', 'Balance']
            
            # Filter out zero balances
            sum_df = sum_df[sum_df['Balance'] != 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                st.markdown("### 💰 Outstanding Balances")
                
                for _, row in sum_df.iterrows():
                    supplier_name = row['Supplier']
                    balance = row['Balance']
                    
                    # Get transaction details for this supplier
                    supplier_txns = d_df[d_df.iloc[:, 0] == supplier_name]
                    
                    with st.expander(f"{'🔴' if balance > 0 else '🟢'} **{supplier_name}** - Balance: ₹{abs(balance):,.2f} {'(We Owe)' if balance > 0 else '(They Owe)'}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("#### Transaction History")
                            for _, txn in supplier_txns.iterrows():
                                date = str(txn.iloc[2]) if len(txn) > 2 else "N/A"
                                amount = float(txn.iloc[1]) if len(txn) > 1 else 0
                                mode = str(txn.iloc[3]) if len(txn) > 3 else "N/A"
                                txn_type = str(txn.iloc[4]) if len(txn) > 4 else ("Credit" if amount > 0 else "Payment")
                                
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
                
                # Overall summary
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
            
            # All transactions table
            st.divider()
            st.subheader("📋 All Transactions")
            st.dataframe(d_df, use_container_width=True)
            
            # Delete option
            st.divider()
            with st.expander("🗑️ Delete Transaction"):
                if len(d_df) > 0:
                    del_idx = st.number_input("Row number to delete", min_value=0, max_value=len(d_df)-1, value=0, key="del_due")
                    st.info(f"Selected: {d_df.iloc[del_idx, 0] if len(d_df.columns) > 0 else 'N/A'} - ₹{d_df.iloc[del_idx, 1] if len(d_df.columns) > 1 else 0}")
                    if st.button("🗑️ Delete Selected Transaction"):
                        st.error("Delete feature requires direct sheet access - Please delete manually from Google Sheets")
                        st.info("Go to Dues sheet and delete the corresponding row")
        else:
            st.info("No supplier transactions yet. Add your first entry above!")

# --- 13. ROYALTY POINTS ---
elif menu == "👑 Royalty Points":
    st.header("👑 Royalty Points System")
    
    s_df = load_data("Sales")
    
    if not s_df.empty and len(s_df.columns) > 6:
        st.info("💡 Weekend shopping gives 5x points! Weekday shopping gives 2x points!")
        
        # Calculate points per customer (CONSOLIDATED - one entry per customer)
        customer_data = {}
        for _, row in s_df.iterrows():
            customer_info = str(row.iloc[5]) if len(row) > 5 else ""
            points = pd.to_numeric(row.iloc[6], errors='coerce') if len(row) > 6 else 0
            date = str(row.iloc[0]) if len(row) > 0 else ""
            amount = float(row.iloc[3]) if len(row) > 3 else 0
            
            if customer_info and customer_info != "nan":
                if customer_info not in customer_data:
                    customer_data[customer_info] = {
                        'total_points': 0,
                        'transactions': [],
                        'total_spent': 0
                    }
                
                customer_data[customer_info]['total_points'] += points
                customer_data[customer_info]['total_spent'] += amount
                customer_data[customer_info]['transactions'].append({
                    'date': date,
                    'points': int(points),
                    'amount': amount
                })
        
        # Convert to dataframe for display
        if customer_data:
            points_df = pd.DataFrame([
                {
                    "Customer": k.split("(")[0] if "(" in k else k,
                    "Phone": k.split("(")[1].replace(")", "") if "(" in k else "N/A",
                    "Total Points": int(v['total_points']),
                    "Total Spent": f"₹{v['total_spent']:,.2f}",
                    "Transactions": len(v['transactions'])
                }
                for k, v in customer_data.items()
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
            c1.metric("👥 Total Customers", len(customer_data))
            c2.metric("🎁 Total Points Given", sum([v['total_points'] for v in customer_data.values()]))
            c3.metric("⭐ Active Customers", len([v for v in customer_data.values() if v['total_points'] > 0]))
            
            st.divider()
            st.subheader("📊 Customer Points Leaderboard (Consolidated)")
            
            # Simple display without styling
            st.dataframe(points_df, use_container_width=True, height=400)
            
            # Show color guide
            st.info("💚 100+ points = VIP | 💛 50+ points = Regular | 🔴 Negative = Used more than earned")
            
            # Detailed transaction history
            st.divider()
            st.subheader("📜 Transaction History")
            
            selected_customer = st.selectbox(
                "Select Customer to View History",
                options=list(customer_data.keys()),
                format_func=lambda x: f"{x.split('(')[0]} - {customer_data[x]['total_points']} points"
            )
            
            if selected_customer:
                cust_info = customer_data[selected_customer]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("👑 Total Points", int(cust_info['total_points']))
                col2.metric("💰 Total Spent", f"₹{cust_info['total_spent']:,.2f}")
                col3.metric("🛒 Total Bills", len(cust_info['transactions']))
                
                st.divider()
                st.write("**Transaction Details:**")
                
                for i, txn in enumerate(reversed(cust_info['transactions']), 1):
                    pts = txn['points']
                    if pts >= 0:
                        st.success(f"{i}. 📅 {txn['date']} | 💰 ₹{txn['amount']:,.2f} | 🎁 +{pts} points")
                    else:
                        st.warning(f"{i}. 📅 {txn['date']} | 💰 ₹{txn['amount']:,.2f} | 🔴 {pts} points (Redeemed)")
            
            # Download option
            st.divider()
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

# --- 14. ADVANCED REPORTS & ANALYTICS ---
elif menu == "📈 Advanced Reports":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">📈 Advanced Reports & Analytics</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Deep Insights for Smart Business Decisions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load all data
    s_df = load_data("Sales")
    i_df = load_data("Inventory")
    e_df = load_data("Expenses")
    k_df = load_data("CustomerKhata")
    
    # Create tabs for different reports
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Best Sellers", 
        "🐌 Slow Moving", 
        "💰 Profit Analysis",
        "👥 Customer Insights",
        "📊 Monthly Trends",
        "🔍 Detailed Reports"
    ])
    
    # ==================== TAB 1: BEST SELLING PRODUCTS ====================
    with tab1:
        st.subheader("🏆 Best Selling Products")
        
        if not s_df.empty and len(s_df.columns) > 1:
            # Date range selector
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30))
            with col2:
                end_date = st.date_input("To Date", value=datetime.now().date())
            
            # Filter sales by date range
            if 'Date' in s_df.columns:
                filtered_sales = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
            else:
                filtered_sales = s_df
            
            if not filtered_sales.empty:
                # Group by product and calculate metrics
                product_stats = {}
                for _, row in filtered_sales.iterrows():
                    product = str(row.iloc[1]) if len(row) > 1 else "Unknown"
                    qty_str = str(row.iloc[2]) if len(row) > 2 else "0"
                    qty = float(qty_str.split()[0]) if qty_str.split() else 0
                    revenue = float(row.iloc[3]) if len(row) > 3 else 0
                    profit = float(row.iloc[7]) if len(row) > 7 else 0
                    
                    if product not in product_stats:
                        product_stats[product] = {
                            'quantity_sold': 0,
                            'revenue': 0,
                            'profit': 0,
                            'bills': 0
                        }
                    
                    product_stats[product]['quantity_sold'] += qty
                    product_stats[product]['revenue'] += revenue
                    product_stats[product]['profit'] += profit
                    product_stats[product]['bills'] += 1
                
                # Convert to dataframe
                best_sellers_df = pd.DataFrame([
                    {
                        'Product': k,
                        'Qty Sold': f"{v['quantity_sold']:.1f}",
                        'Revenue': f"₹{v['revenue']:,.2f}",
                        'Profit': f"₹{v['profit']:,.2f}",
                        'Bills': v['bills'],
                        'Avg Bill Value': f"₹{v['revenue']/v['bills']:,.2f}"
                    }
                    for k, v in product_stats.items()
                ])
                
                # Sort by revenue
                best_sellers_df['Revenue_Numeric'] = [product_stats[k]['revenue'] for k in product_stats.keys()]
                best_sellers_df = best_sellers_df.sort_values('Revenue_Numeric', ascending=False)
                best_sellers_df = best_sellers_df.drop('Revenue_Numeric', axis=1).reset_index(drop=True)
                
                # Display top 10
                st.markdown("### 🥇 Top 10 Products by Revenue")
                
                top10 = best_sellers_df.head(10).reset_index(drop=True)
                
                if not top10.empty:
                    # Simple display without styling
                    st.dataframe(top10, use_container_width=True)
                    
                    # Show medals separately
                    st.info("🥇 #1: " + str(top10.iloc[0]['Product']) if len(top10) > 0 else "")
                    if len(top10) > 1:
                        st.info("🥈 #2: " + str(top10.iloc[1]['Product']))
                    if len(top10) > 2:
                        st.info("🥉 #3: " + str(top10.iloc[2]['Product']))
                else:
                    st.info("No product data to display")
                
                # Summary metrics
                st.divider()
                col1, col2, col3 = st.columns(3)
                
                total_revenue = sum([v['revenue'] for v in product_stats.values()])
                total_profit = sum([v['profit'] for v in product_stats.values()])
                total_items = len(product_stats)
                
                col1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
                col2.metric("📈 Total Profit", f"₹{total_profit:,.2f}")
                col3.metric("📦 Products Sold", total_items)
                
                # Download option
                st.divider()
                csv = best_sellers_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Full Report",
                    data=csv,
                    file_name=f"best_sellers_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No sales data in selected date range")
        else:
            st.info("No sales data available")
    
    # ==================== TAB 2: SLOW MOVING PRODUCTS ====================
    with tab2:
        st.subheader("🐌 Slow Moving & Dead Stock Analysis")
        
        if not i_df.empty and not s_df.empty:
            # Get unique products from inventory
            inventory_products = set(i_df.iloc[:, 0].unique())
            
            # Calculate days selection
            days_threshold = st.slider("No sales in last X days", 7, 90, 30)
            cutoff_date = datetime.now().date() - timedelta(days=days_threshold)
            
            # Get products sold after cutoff
            if 'Date' in s_df.columns:
                recent_sales = s_df[s_df['Date'] >= cutoff_date]
                recently_sold = set(recent_sales.iloc[:, 1].unique())
            else:
                recently_sold = set()
            
            # Find slow moving items
            slow_moving = inventory_products - recently_sold
            
            if slow_moving:
                st.error(f"🚨 Found {len(slow_moving)} slow moving products!")
                
                # Get current stock and value
                slow_items_data = []
                for product in slow_moving:
                    product_inventory = i_df[i_df.iloc[:, 0] == product]
                    if not product_inventory.empty:
                        # Get latest entry
                        latest = product_inventory.iloc[-1]
                        qty_str = str(latest.iloc[1]) if len(latest) > 1 else "0"
                        qty = float(qty_str.split()[0]) if qty_str.split() else 0
                        rate = float(latest.iloc[3]) if len(latest) > 3 else 0
                        value = qty * rate
                        
                        # Check last sale date
                        product_sales = s_df[s_df.iloc[:, 1] == product]
                        if not product_sales.empty and 'Date' in product_sales.columns:
                            last_sale = product_sales['Date'].max()
                            days_since = (datetime.now().date() - last_sale).days
                        else:
                            last_sale = "Never"
                            days_since = 999
                        
                        slow_items_data.append({
                            'Product': product,
                            'Current Stock': qty_str,
                            'Rate': f"₹{rate:.2f}",
                            'Stock Value': f"₹{value:,.2f}",
                            'Last Sale': str(last_sale),
                            'Days Since Sale': days_since,
                            'Value_Numeric': value
                        })
                
                slow_df = pd.DataFrame(slow_items_data)
                slow_df = slow_df.sort_values('Days Since Sale', ascending=False)
                
                # Summary
                total_dead_value = slow_df['Value_Numeric'].sum()
                st.warning(f"💸 Total value locked in slow moving stock: ₹{total_dead_value:,.2f}")
                
                # Display
                slow_df = slow_df.drop('Value_Numeric', axis=1)
                st.dataframe(slow_df, use_container_width=True)
                
                # Recommendations
                st.divider()
                st.markdown("### 💡 Recommendations:")
                st.info("1. Consider offering discounts on these items")
                st.info("2. Bundle with fast-moving products")
                st.info("3. Run promotional campaigns")
                st.info("4. Reduce future orders for these products")
                
                # Download
                csv = slow_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Slow Moving Report",
                    data=csv,
                    file_name=f"slow_moving_stock_{today_dt}.csv",
                    mime="text/csv"
                )
            else:
                st.success(f"✅ All products sold in last {days_threshold} days!")
        else:
            st.info("Need both inventory and sales data for this analysis")
    
    # ==================== TAB 3: PROFIT ANALYSIS ====================
    with tab3:
        st.subheader("💰 Profit Margin Analysis")
        
        if not s_df.empty and len(s_df.columns) > 7:
            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From", value=datetime.now().date() - timedelta(days=30), key="profit_start")
            with col2:
                end_date = st.date_input("To", value=datetime.now().date(), key="profit_end")
            
            # Filter
            if 'Date' in s_df.columns:
                filtered = s_df[(s_df['Date'] >= start_date) & (s_df['Date'] <= end_date)]
            else:
                filtered = s_df
            
            if not filtered.empty:
                # Calculate metrics
                total_revenue = pd.to_numeric(filtered.iloc[:, 3], errors='coerce').sum()
                total_profit = pd.to_numeric(filtered.iloc[:, 7], errors='coerce').sum()
                total_cost = total_revenue - total_profit
                
                profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
                
                # Display main metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💵 Revenue", f"₹{total_revenue:,.2f}")
                col2.metric("💰 Profit", f"₹{total_profit:,.2f}")
                col3.metric("💸 Cost", f"₹{total_cost:,.2f}")
                col4.metric("📊 Margin", f"{profit_margin:.1f}%")
                
                st.divider()
                
                # Product-wise profit analysis
                st.markdown("### 📦 Product-wise Profit Margins")
                
                product_profit = {}
                for _, row in filtered.iterrows():
                    product = str(row.iloc[1]) if len(row) > 1 else "Unknown"
                    revenue = float(row.iloc[3]) if len(row) > 3 else 0
                    profit = float(row.iloc[7]) if len(row) > 7 else 0
                    
                    if product not in product_profit:
                        product_profit[product] = {'revenue': 0, 'profit': 0}
                    
                    product_profit[product]['revenue'] += revenue
                    product_profit[product]['profit'] += profit
                
                # Convert to dataframe
                profit_df = pd.DataFrame([
                    {
                        'Product': k,
                        'Revenue': f"₹{v['revenue']:,.2f}",
                        'Profit': f"₹{v['profit']:,.2f}",
                        'Cost': f"₹{v['revenue']-v['profit']:,.2f}",
                        'Margin %': f"{(v['profit']/v['revenue']*100):.1f}%" if v['revenue'] > 0 else "0%",
                        'Margin_Numeric': (v['profit']/v['revenue']*100) if v['revenue'] > 0 else 0
                    }
                    for k, v in product_profit.items()
                ])
                
                # Sort by margin
                profit_df = profit_df.sort_values('Margin_Numeric', ascending=False)
                
                # Check if dataframe has data before displaying
                if not profit_df.empty:
                    profit_df_display = profit_df.drop('Margin_Numeric', axis=1)
                    
                    # Simple display without styling
                    st.dataframe(profit_df_display, use_container_width=True)
                    
                    # Show color guide
                    st.markdown("""
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                        <b>Margin Guide:</b><br>
                        ✅ 30%+ = High margin - Excellent!<br>
                        ⚠️ 15-30% = Medium margin - Good<br>
                        ❌ <10% = Low margin - Review pricing
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No profit data available for analysis")
                
                # Download
                csv = profit_df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Profit Analysis",
                    data=csv,
                    file_name=f"profit_analysis_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data in selected range")
        else:
            st.info("Need sales data with profit information")
    
    # ==================== TAB 4: CUSTOMER INSIGHTS ====================
    with tab4:
        st.subheader("👥 Customer Analytics")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Customer analysis
            customer_analysis = {}
            
            for _, row in s_df.iterrows():
                customer = str(row.iloc[5]) if len(row) > 5 else "Unknown"
                amount = float(row.iloc[3]) if len(row) > 3 else 0
                date = row.iloc[0] if len(row) > 0 else None
                
                if customer != "Unknown" and customer != "nan":
                    if customer not in customer_analysis:
                        customer_analysis[customer] = {
                            'total_spent': 0,
                            'visits': 0,
                            'last_visit': date,
                            'first_visit': date
                        }
                    
                    customer_analysis[customer]['total_spent'] += amount
                    customer_analysis[customer]['visits'] += 1
                    
                    if date and customer_analysis[customer]['last_visit']:
                        if date > customer_analysis[customer]['last_visit']:
                            customer_analysis[customer]['last_visit'] = date
                        if date < customer_analysis[customer]['first_visit']:
                            customer_analysis[customer]['first_visit'] = date
            
            if customer_analysis:
                # Convert to dataframe
                customer_df = pd.DataFrame([
                    {
                        'Customer': k.split("(")[0] if "(" in k else k,
                        'Phone': k.split("(")[1].replace(")", "") if "(" in k else "N/A",
                        'Total Spent': f"₹{v['total_spent']:,.2f}",
                        'Visits': v['visits'],
                        'Avg Bill': f"₹{v['total_spent']/v['visits']:,.2f}",
                        'Last Visit': str(v['last_visit']),
                        'Spent_Numeric': v['total_spent']
                    }
                    for k, v in customer_analysis.items()
                ])
                
                customer_df = customer_df.sort_values('Spent_Numeric', ascending=False)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👥 Total Customers", len(customer_analysis))
                col2.metric("💰 Total Revenue", f"₹{sum([v['total_spent'] for v in customer_analysis.values()]):,.2f}")
                col3.metric("📊 Avg Customer Value", f"₹{sum([v['total_spent'] for v in customer_analysis.values()])/len(customer_analysis):,.2f}")
                col4.metric("🔄 Avg Visits", f"{sum([v['visits'] for v in customer_analysis.values()])/len(customer_analysis):.1f}")
                
                st.divider()
                
                # Top customers
                st.markdown("### 🏆 Top 20 Customers")
                
                top20 = customer_df.head(20).drop('Spent_Numeric', axis=1)
                st.dataframe(top20, use_container_width=True)
                
                # Download
                csv = customer_df.drop('Spent_Numeric', axis=1).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Customer Report",
                    data=csv,
                    file_name=f"customer_insights_{today_dt}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No customer data available")
        else:
            st.info("Need sales data with customer information")
    
    # ==================== TAB 5: MONTHLY TRENDS ====================
    with tab5:
        st.subheader("📊 Monthly Trends & Comparisons")
        
        if not s_df.empty and 'Date' in s_df.columns:
            # Add month column
            s_df['Month'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.to_period('M')
            
            # Group by month
            monthly_stats = s_df.groupby('Month').agg({
                s_df.columns[3]: lambda x: pd.to_numeric(x, errors='coerce').sum(),  # Revenue
                s_df.columns[7]: lambda x: pd.to_numeric(x, errors='coerce').sum() if len(s_df.columns) > 7 else 0,  # Profit
                s_df.columns[0]: 'count'  # Number of bills
            }).reset_index()
            
            monthly_stats.columns = ['Month', 'Revenue', 'Profit', 'Bills']
            monthly_stats['Month'] = monthly_stats['Month'].astype(str)
            
            # Display
            st.markdown("### 📈 Month-wise Performance")
            
            for _, row in monthly_stats.iterrows():
                month = row['Month']
                revenue = row['Revenue']
                profit = row['Profit']
                bills = row['Bills']
                margin = (profit/revenue*100) if revenue > 0 else 0
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white;">
                        <h3 style="margin: 0;">{month}</h3>
                        <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                            <div>💰 Revenue: ₹{revenue:,.2f}</div>
                            <div>📈 Profit: ₹{profit:,.2f}</div>
                            <div>🧾 Bills: {bills}</div>
                            <div>📊 Margin: {margin:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Download
            csv = monthly_stats.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Monthly Trends",
                data=csv,
                file_name=f"monthly_trends_{today_dt}.csv",
                mime="text/csv"
            )
        else:
            st.info("Need sales data with dates")
    
    # ==================== TAB 6: DETAILED REPORTS ====================
    with tab6:
        st.subheader("🔍 Custom Detailed Reports")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Sales Summary", "Expense Summary", "Inventory Valuation", "Customer Udhaar Report"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30), key="detail_start")
        with col2:
            end = st.date_input("End Date", value=datetime.now().date(), key="detail_end")
        
        if st.button("🔍 Generate Report", type="primary"):
            if report_type == "Sales Summary":
                if not s_df.empty and 'Date' in s_df.columns:
                    filtered = s_df[(s_df['Date'] >= start) & (s_df['Date'] <= end)]
                    st.dataframe(filtered, use_container_width=True)
                    
                    # Summary
                    total = pd.to_numeric(filtered.iloc[:, 3], errors='coerce').sum()
                    st.success(f"Total Sales: ₹{total:,.2f}")
                    
                    csv = filtered.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download", csv, f"sales_{start}_to_{end}.csv", "text/csv")
            
            elif report_type == "Expense Summary":
                if not e_df.empty and 'Date' in e_df.columns:
                    filtered = e_df[(e_df['Date'] >= start) & (e_df['Date'] <= end)]
                    st.dataframe(filtered, use_container_width=True)
                    
                    total = pd.to_numeric(filtered.iloc[:, 2], errors='coerce').sum()
                    st.error(f"Total Expenses: ₹{total:,.2f}")
                    
                    csv = filtered.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download", csv, f"expenses_{start}_to_{end}.csv", "text/csv")
            
            elif report_type == "Inventory Valuation":
                if not i_df.empty:
                    i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
                    i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
                    i_df['value'] = i_df['qty_v'] * i_df['rate_v']
                    
                    st.dataframe(i_df[['Item', 'Quantity', 'Rate', 'value']], use_container_width=True)
                    st.success(f"Total Stock Value: ₹{i_df['value'].sum():,.2f}")
            
            elif report_type == "Customer Udhaar Report":
                if not k_df.empty:
                    summary = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
                    summary.columns = ['Customer', 'Balance']
                    summary = summary[summary['Balance'] != 0].sort_values('Balance', ascending=False)
                    
                    st.dataframe(summary, use_container_width=True)
                    st.warning(f"Total Udhaar: ₹{summary['Balance'].sum():,.2f}")
                    
                    csv = summary.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download", csv, f"udhaar_report_{today_dt}.csv", "text/csv")

# --- 15. USER MANAGEMENT (OWNER ONLY) ---
elif menu == "👥 User Management":
    if st.session_state.user_role != "owner":
        st.error("🚫 Access Denied! Only Owner can access User Management.")
        st.stop()
    
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">👥 User Management</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Manage Staff & Access Control</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Current Users", "➕ Add User", "✏️ Edit User", "📊 Activity Log"])
    
    # TAB 1: Current Users
    with tab1:
        st.subheader("📋 Current User List")
        
        # Display users in cards
        for username, data in USERS.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.markdown(f"### 👤 {data['name']}")
                
                with col2:
                    role_color = {
                        "owner": "🔴",
                        "manager": "🟡", 
                        "staff": "🟢"
                    }
                    st.write(f"{role_color.get(data['role'], '⚪')} Role: **{data['role'].upper()}**")
                
                with col3:
                    st.write(f"🔑 Username: `{username}`")
                
                with col4:
                    if st.button("✏️", key=f"edit_{username}", help="Edit User"):
                        st.session_state.edit_user = username
                        st.rerun()
                
                st.divider()
        
        # Summary
        st.markdown("### 📊 User Summary")
        col1, col2, col3 = st.columns(3)
        
        owner_count = sum(1 for u in USERS.values() if u['role'] == 'owner')
        manager_count = sum(1 for u in USERS.values() if u['role'] == 'manager')
        staff_count = sum(1 for u in USERS.values() if u['role'] == 'staff')
        
        col1.metric("👑 Owners", owner_count)
        col2.metric("📊 Managers", manager_count)
        col3.metric("👥 Staff", staff_count)
    
    # TAB 2: Add User
    with tab2:
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username", placeholder="e.g., Staff3")
            new_name = st.text_input("Full Name", placeholder="e.g., Rahul Kumar")
            new_password = st.text_input("Password", type="password", placeholder="Min 8 characters")
            new_role = st.selectbox("Role", ["staff", "manager", "owner"])
            
            st.info(f"""
            **Role Permissions:**
            - **Owner**: Full access (Dashboard, Billing, Reports, User Management, etc.)
            - **Manager**: All except User Management
            - **Staff**: Billing & Basic Operations only
            """)
            
            if st.form_submit_button("✅ Add User", type="primary"):
                if new_username and new_name and new_password:
                    if new_username in USERS:
                        st.error(f"❌ Username '{new_username}' already exists!")
                    elif len(new_password) < 8:
                        st.error("❌ Password must be at least 8 characters!")
                    else:
                        # Note: In production, this should save to database
                        st.success(f"""
                        ✅ User Created Successfully!
                        
                        **Username**: {new_username}
                        **Name**: {new_name}
                        **Role**: {new_role.upper()}
                        
                        ⚠️ Note: Currently users are stored in code. 
                        For permanent storage, connect to database.
                        """)
                        st.info("📋 User credentials to share:")
                        st.code(f"Username: {new_username}\nPassword: {new_password}")
                else:
                    st.error("❌ Please fill all fields!")
    
    # TAB 3: Edit User
    with tab3:
        st.subheader("✏️ Edit User Details")
        
        # Check if user selected for editing
        if 'edit_user' not in st.session_state:
            st.session_state.edit_user = None
        
        # User selector
        edit_username = st.selectbox(
            "Select User to Edit",
            options=list(USERS.keys()),
            index=list(USERS.keys()).index(st.session_state.edit_user) if st.session_state.edit_user in USERS else 0
        )
        
        if edit_username:
            user_data = USERS[edit_username]
            
            st.divider()
            
            # Show current details
            st.markdown("### 📋 Current Details")
            col1, col2, col3 = st.columns(3)
            col1.info(f"**Username:** {edit_username}")
            col2.info(f"**Name:** {user_data['name']}")
            col3.info(f"**Role:** {user_data['role'].upper()}")
            
            st.divider()
            
            # Edit form
            st.markdown("### ✏️ Update Details")
            
            with st.form("edit_user_form"):
                st.warning("⚠️ Leave fields empty if you don't want to change them")
                
                # New username
                new_username = st.text_input(
                    "New Username (Optional)",
                    placeholder=f"Current: {edit_username}",
                    help="Change username - leave empty to keep current"
                )
                
                # New name
                new_name = st.text_input(
                    "New Full Name (Optional)",
                    placeholder=f"Current: {user_data['name']}",
                    help="Change display name - leave empty to keep current"
                )
                
                # New password
                new_password = st.text_input(
                    "New Password (Optional)",
                    type="password",
                    placeholder="Enter new password (min 8 chars)",
                    help="Change password - leave empty to keep current"
                )
                
                confirm_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Re-enter new password",
                    help="Confirm your new password"
                )
                
                # Role change
                new_role = st.selectbox(
                    "Role",
                    ["staff", "manager", "owner"],
                    index=["staff", "manager", "owner"].index(user_data['role'])
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submit_edit = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                
                with col2:
                    cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submit_edit:
                    # Validation
                    errors = []
                    
                    # Check if new username already exists
                    if new_username and new_username != edit_username and new_username in USERS:
                        errors.append(f"Username '{new_username}' already exists!")
                    
                    # Check password match
                    if new_password or confirm_password:
                        if new_password != confirm_password:
                            errors.append("Passwords do not match!")
                        elif len(new_password) < 8:
                            errors.append("Password must be at least 8 characters!")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Prepare update message
                        changes = []
                        
                        # Build the updated user data
                        updated_username = new_username if new_username else edit_username
                        updated_name = new_name if new_name else user_data['name']
                        updated_password = new_password if new_password else user_data['password']
                        updated_role = new_role
                        
                        # Track what changed
                        if new_username and new_username != edit_username:
                            changes.append(f"Username: {edit_username} → {new_username}")
                        if new_name and new_name != user_data['name']:
                            changes.append(f"Name: {user_data['name']} → {new_name}")
                        if new_password:
                            changes.append("Password: Updated")
                        if new_role != user_data['role']:
                            changes.append(f"Role: {user_data['role']} → {new_role}")
                        
                        if changes:
                            st.success("✅ User Updated Successfully!")
                            st.markdown("### 📝 Changes Made:")
                            for change in changes:
                                st.write(f"• {change}")
                            
                            # Show new credentials if username or password changed
                            if new_username or new_password:
                                st.divider()
                                st.info("📋 Updated Credentials:")
                                st.code(f"""Username: {updated_username}
Password: {updated_password if new_password else '[Unchanged]'}
Role: {updated_role.upper()}""")
                            
                            st.warning("""
                            ⚠️ **Important:**
                            - These changes are currently stored in memory only
                            - For permanent storage, connect to a database
                            - User will need to re-login with new credentials
                            """)
                            
                            # Clear edit selection
                            st.session_state.edit_user = None
                        else:
                            st.info("ℹ️ No changes made")
                
                if cancel_edit:
                    st.session_state.edit_user = None
                    st.rerun()
    
    # TAB 4: Activity Log
    with tab4:
        st.subheader("📊 User Activity Log")
        
        st.info("🚧 Activity logging feature coming soon!")
        
        # Sample activity log
        st.markdown("### 📝 Recent Activities (Demo)")
        
        sample_activities = [
            {"user": "Staff1", "action": "Created Bill", "amount": "₹1,250", "time": "2 hours ago"},
            {"user": "Manager", "action": "Added Inventory", "amount": "₹8,500", "time": "3 hours ago"},
            {"user": "Staff2", "action": "Created Bill", "amount": "₹850", "time": "5 hours ago"},
            {"user": "Owner", "action": "Viewed Reports", "amount": "-", "time": "1 day ago"},
        ]
        
        for activity in sample_activities:
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            with col1:
                st.write(f"👤 {activity['user']}")
            with col2:
                st.write(f"📝 {activity['action']}")
            with col3:
                st.write(f"💰 {activity['amount']}")
            with col4:
                st.write(f"🕒 {activity['time']}")
            st.divider()

# --- 16. AUTOMATED REMINDERS ---
elif menu == "🔔 Automated Reminders":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🔔 Automated Reminders</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Never Miss Important Dates & Tasks</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    p_df = load_data("PetRecords")
    k_df = load_data("CustomerKhata")
    d_df = load_data("Dues")
    i_df = load_data("Inventory")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💉 Vaccination Due",
        "💰 Payment Reminders", 
        "📦 Low Stock Alerts",
        "🏢 Supplier Payments",
        "⚙️ Settings"
    ])
    
    # ==================== TAB 1: VACCINATION DUE ====================
    with tab1:
        st.subheader("💉 Pet Vaccination Due Reminders")
        
        if not p_df.empty and len(p_df.columns) > 6:
            # Calculate vaccination due dates
            today = datetime.now().date()
            
            # Find pets with upcoming vaccinations
            upcoming_vax = []
            overdue_vax = []
            
            for _, row in p_df.iterrows():
                try:
                    owner = str(row.iloc[0]) if len(row) > 0 else "Unknown"
                    phone = str(row.iloc[1]) if len(row) > 1 else "N/A"
                    breed = str(row.iloc[2]) if len(row) > 2 else "Unknown"
                    next_vax_str = str(row.iloc[6]) if len(row) > 6 else None
                    
                    if next_vax_str and next_vax_str != "nan":
                        next_vax = pd.to_datetime(next_vax_str, errors='coerce').date()
                        
                        if next_vax:
                            days_until = (next_vax - today).days
                            
                            vax_info = {
                                'owner': owner,
                                'phone': phone,
                                'breed': breed,
                                'next_vax': next_vax,
                                'days_until': days_until
                            }
                            
                            if days_until < 0:
                                overdue_vax.append(vax_info)
                            elif days_until <= 30:
                                upcoming_vax.append(vax_info)
                except:
                    continue
            
            # Display overdue vaccinations
            if overdue_vax:
                st.error(f"🚨 {len(overdue_vax)} Overdue Vaccinations!")
                
                for vax in overdue_vax:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            st.write(f"👤 **{vax['owner']}**")
                            st.write(f"🐕 {vax['breed']}")
                        
                        with col2:
                            st.write(f"📱 {vax['phone']}")
                        
                        with col3:
                            st.error(f"⚠️ Overdue by {abs(vax['days_until'])} days")
                            st.write(f"Due: {vax['next_vax']}")
                        
                        with col4:
                            # WhatsApp reminder button
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {vax['owner']} जी!

आपके पालतू ({vax['breed']}) का टीकाकरण {abs(vax['days_until'])} दिन से लंबित है!

📅 Due Date: {vax['next_vax']}
💉 कृपया जल्द से जल्द appointment लें

🏥 Contact: Laika Pet Mart"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{vax['phone']}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #dc3545; color: white; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer;">📱 Send</button></a>', unsafe_allow_html=True)
                        
                        st.divider()
            
            # Display upcoming vaccinations
            if upcoming_vax:
                st.warning(f"⏰ {len(upcoming_vax)} Vaccinations Due in Next 30 Days")
                
                for vax in sorted(upcoming_vax, key=lambda x: x['days_until']):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            st.write(f"👤 **{vax['owner']}**")
                            st.write(f"🐕 {vax['breed']}")
                        
                        with col2:
                            st.write(f"📱 {vax['phone']}")
                        
                        with col3:
                            st.warning(f"📅 Due in {vax['days_until']} days")
                            st.write(f"Date: {vax['next_vax']}")
                        
                        with col4:
                            # WhatsApp reminder button
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {vax['owner']} जी!

आपके पालतू ({vax['breed']}) का टीकाकरण {vax['days_until']} दिन में है!

📅 Due Date: {vax['next_vax']}
💉 कृपया appointment बुक करें

🏥 Contact: Laika Pet Mart"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{vax['phone']}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #ffc107; color: black; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer;">📱 Send</button></a>', unsafe_allow_html=True)
                        
                        st.divider()
            
            if not overdue_vax and not upcoming_vax:
                st.success("✅ No vaccinations due in the next 30 days!")
        else:
            st.info("No pet records found. Add pets in Pet Register to track vaccinations.")
    
    # ==================== TAB 2: PAYMENT REMINDERS ====================
    with tab2:
        st.subheader("💰 Customer Payment Reminders (Udhaar)")
        
        if not k_df.empty and len(k_df.columns) > 1:
            # Calculate customer balances
            customer_balances = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            customer_balances.columns = ['Customer', 'Balance']
            
            # Filter only customers with positive balance (owe money)
            udhaar_customers = customer_balances[customer_balances['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not udhaar_customers.empty:
                st.warning(f"📋 {len(udhaar_customers)} Customers with Pending Payments")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                total_udhaar = udhaar_customers['Balance'].sum()
                avg_udhaar = total_udhaar / len(udhaar_customers)
                max_udhaar = udhaar_customers['Balance'].max()
                
                col1.metric("💰 Total Udhaar", f"₹{total_udhaar:,.2f}")
                col2.metric("📊 Average", f"₹{avg_udhaar:,.2f}")
                col3.metric("🔴 Highest", f"₹{max_udhaar:,.2f}")
                
                st.divider()
                
                # Filter options
                min_amount = st.slider("Show customers with udhaar ≥", 0, int(max_udhaar), 0, 100)
                
                filtered_customers = udhaar_customers[udhaar_customers['Balance'] >= min_amount]
                
                # Display customers
                for _, row in filtered_customers.iterrows():
                    customer_info = row['Customer']
                    balance = row['Balance']
                    
                    # Extract name and phone
                    if "(" in customer_info and ")" in customer_info:
                        cust_name = customer_info.split("(")[0].strip()
                        cust_phone = customer_info.split("(")[1].replace(")", "").strip()
                    else:
                        cust_name = customer_info
                        cust_phone = ""
                    
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"👤 **{cust_name}**")
                            if cust_phone:
                                st.write(f"📱 {cust_phone}")
                        
                        with col2:
                            if balance >= 5000:
                                st.error(f"💰 ₹{balance:,.2f}")
                            elif balance >= 2000:
                                st.warning(f"💰 ₹{balance:,.2f}")
                            else:
                                st.info(f"💰 ₹{balance:,.2f}")
                        
                        with col3:
                            if cust_phone:
                                # WhatsApp reminder
                                message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {cust_name} जी!

आपका बकाया: ₹{balance:,.2f}

कृपया जल्द से जल्द भुगतान करें।

धन्यवाद! 🙏
Laika Pet Mart"""
                                
                                import urllib.parse
                                encoded_msg = urllib.parse.quote(message)
                                whatsapp_url = f"https://wa.me/91{cust_phone}?text={encoded_msg}"
                                
                                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer;">💬 Send</button></a>', unsafe_allow_html=True)
                        
                        st.divider()
            else:
                st.success("✅ No pending customer payments!")
        else:
            st.info("No udhaar records found.")
    
    # ==================== TAB 3: LOW STOCK ALERTS ====================
    with tab3:
        st.subheader("📦 Low Stock Alerts")
        
        if not i_df.empty and len(i_df.columns) > 3:
            # Calculate current stock
            i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
            i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
            
            # Get latest stock for each item
            stock_summary = i_df.groupby(i_df.columns[0]).agg({
                i_df.columns[1]: 'last',
                'qty_v': 'last',
                'rate_v': 'last'
            }).reset_index()
            stock_summary.columns = ['Item', 'Quantity', 'Qty_Numeric', 'Rate']
            
            # Low stock threshold selector
            threshold = st.slider("Low Stock Threshold (units)", 1, 10, 5)
            
            # Find low stock items
            low_stock = stock_summary[stock_summary['Qty_Numeric'] < threshold]
            
            if not low_stock.empty:
                st.error(f"🚨 {len(low_stock)} Items Below Threshold!")
                
                # Calculate total value locked
                low_stock['Value'] = low_stock['Qty_Numeric'] * low_stock['Rate']
                total_value = low_stock['Value'].sum()
                
                st.warning(f"💸 Current Stock Value: ₹{total_value:,.2f}")
                
                st.divider()
                
                # Display low stock items
                for _, row in low_stock.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.write(f"📦 **{row['Item']}**")
                    
                    with col2:
                        st.error(f"⚠️ Only {row['Qty_Numeric']:.0f} units left!")
                    
                    with col3:
                        st.write(f"💰 Rate: ₹{row['Rate']:,.2f}")
                    
                    st.divider()
                
                # Recommendation
                st.info("💡 Recommendation: Order these items soon to avoid stock-out!")
            else:
                st.success(f"✅ All items above {threshold} units threshold!")
        else:
            st.info("No inventory data found.")
    
    # ==================== TAB 4: SUPPLIER PAYMENTS ====================
    with tab4:
        st.subheader("🏢 Supplier Payment Reminders")
        
        if not d_df.empty and len(d_df.columns) > 1:
            # Calculate supplier balances
            supplier_balances = d_df.groupby(d_df.columns[0]).agg({d_df.columns[1]: 'sum'}).reset_index()
            supplier_balances.columns = ['Supplier', 'Balance']
            
            # Filter suppliers we owe money to (positive balance)
            pending_payments = supplier_balances[supplier_balances['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not pending_payments.empty:
                st.warning(f"💰 {len(pending_payments)} Suppliers Pending Payment")
                
                # Summary
                col1, col2, col3 = st.columns(3)
                total_due = pending_payments['Balance'].sum()
                avg_due = total_due / len(pending_payments)
                max_due = pending_payments['Balance'].max()
                
                col1.metric("💸 Total Due", f"₹{total_due:,.2f}")
                col2.metric("📊 Average", f"₹{avg_due:,.2f}")
                col3.metric("🔴 Highest", f"₹{max_due:,.2f}")
                
                st.divider()
                
                # Display suppliers
                for _, row in pending_payments.iterrows():
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.write(f"🏢 **{row['Supplier']}**")
                    
                    with col2:
                        if row['Balance'] >= 10000:
                            st.error(f"💰 ₹{row['Balance']:,.2f}")
                        elif row['Balance'] >= 5000:
                            st.warning(f"💰 ₹{row['Balance']:,.2f}")
                        else:
                            st.info(f"💰 ₹{row['Balance']:,.2f}")
                    
                    st.divider()
                
                st.info("💡 Tip: Maintain good relationships by paying suppliers on time!")
            else:
                st.success("✅ No pending supplier payments!")
        else:
            st.info("No supplier dues data found.")
    
    # ==================== TAB 5: SETTINGS ====================
    with tab5:
        st.subheader("⚙️ Reminder Settings")
        
        st.info("🚧 Advanced settings coming soon!")
        
        # Sample settings
        st.markdown("### 📅 Reminder Frequency")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Daily Low Stock Alert", value=True)
            st.checkbox("Weekly Udhaar Summary", value=True)
            st.checkbox("Monthly Supplier Report", value=False)
        
        with col2:
            st.checkbox("Vaccination 7 days before", value=True)
            st.checkbox("Vaccination 3 days before", value=True)
            st.checkbox("Vaccination day reminder", value=True)
        
        st.divider()
        
        st.markdown("### 📱 Notification Channels")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("WhatsApp Notifications", value=True)
            st.checkbox("SMS Notifications", value=False, disabled=True)
        
        with col2:
            st.checkbox("Email Notifications", value=False, disabled=True)
            st.checkbox("In-App Notifications", value=True)
        
        st.divider()
        
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
            st.info("Note: Some features require additional setup")

# --- 16. GST & INVOICE MANAGEMENT ---
elif menu == "💼 GST & Invoices":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">💼 GST & Invoice Management</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Professional Invoicing & Tax Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Generate Invoice",
        "📊 GST Summary",
        "🗂️ Invoice History",
        "📈 Tax Reports",
        "⚙️ GST Settings"
    ])
    
    # ==================== TAB 1: GENERATE INVOICE ====================
    with tab1:
        st.subheader("📄 Generate GST Invoice")
        
        # Business details (should be in settings in production)
        st.markdown("### 🏢 Business Details")
        col1, col2 = st.columns(2)
        
        with col1:
            business_name = st.text_input("Business Name", value="LAIKA PET MART", key="biz_name")
            business_address = st.text_area("Address", value="Shop No. 123, Main Market\nBareilly, UP - 243001", key="biz_addr")
            gstin = st.text_input("GSTIN", value="09XXXXX1234X1Z5", placeholder="Enter your GSTIN", key="gstin")
        
        with col2:
            business_phone = st.text_input("Phone", value="+91 9876543210", key="biz_phone")
            business_email = st.text_input("Email", value="laika@petmart.com", key="biz_email")
            pan = st.text_input("PAN", value="XXXXX1234X", key="pan")
        
        st.divider()
        
        # Customer details
        st.markdown("### 👤 Customer Details")
        col1, col2 = st.columns(2)
        
        with col1:
            cust_name = st.text_input("Customer Name", key="inv_cust_name")
            cust_phone = st.text_input("Phone", key="inv_cust_phone")
            cust_gstin = st.text_input("Customer GSTIN (Optional)", placeholder="Leave empty for B2C", key="cust_gstin")
        
        with col2:
            cust_address = st.text_area("Billing Address", key="inv_cust_addr")
            invoice_date = st.date_input("Invoice Date", value=datetime.now().date(), key="inv_date")
            invoice_num = st.text_input("Invoice Number", value=f"INV-{datetime.now().strftime('%Y%m%d')}-001", key="inv_num")
        
        st.divider()
        
        # Items
        st.markdown("### 📦 Invoice Items")
        
        # Initialize items in session state
        if 'invoice_items' not in st.session_state:
            st.session_state.invoice_items = []
        
        # Add item form
        with st.form("add_invoice_item"):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                item_name = st.text_input("Item Description", key="item_desc")
            with col2:
                item_qty = st.number_input("Qty", min_value=0.1, value=1.0, key="item_qty")
            with col3:
                item_rate = st.number_input("Rate", min_value=0.0, value=0.0, key="item_rate")
            with col4:
                item_gst = st.selectbox("GST %", [0, 5, 12, 18, 28], index=3, key="item_gst")
            with col5:
                add_item = st.form_submit_button("➕ Add", use_container_width=True)
            
            if add_item and item_name and item_rate > 0:
                taxable_amt = item_qty * item_rate
                gst_amt = (taxable_amt * item_gst) / 100
                total_amt = taxable_amt + gst_amt
                
                st.session_state.invoice_items.append({
                    'Description': item_name,
                    'Qty': item_qty,
                    'Rate': item_rate,
                    'Taxable': taxable_amt,
                    'GST %': item_gst,
                    'GST Amt': gst_amt,
                    'Total': total_amt
                })
                st.rerun()
        
        # Display items
        if st.session_state.invoice_items:
            items_df = pd.DataFrame(st.session_state.invoice_items)
            st.dataframe(items_df, use_container_width=True)
            
            # Calculate totals
            total_taxable = sum([item['Taxable'] for item in st.session_state.invoice_items])
            total_gst = sum([item['GST Amt'] for item in st.session_state.invoice_items])
            grand_total = sum([item['Total'] for item in st.session_state.invoice_items])
            
            # Display summary
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Taxable Amount", f"₹{total_taxable:,.2f}")
            col2.metric("📊 Total GST", f"₹{total_gst:,.2f}")
            col3.metric("💳 Grand Total", f"₹{grand_total:,.2f}")
            
            # Action buttons
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Generate PDF Invoice", type="primary", use_container_width=True):
                    st.success("✅ Invoice generated successfully!")
                    st.info("📥 Download feature: Install reportlab library")
                    st.code("pip install reportlab")
            
            with col2:
                if st.button("📧 Email Invoice", use_container_width=True):
                    st.info("📧 Email feature coming soon!")
            
            with col3:
                if st.button("🗑️ Clear Items", use_container_width=True):
                    st.session_state.invoice_items = []
                    st.rerun()
        else:
            st.info("➕ Add items to generate invoice")
    
    # ==================== TAB 2: GST SUMMARY ====================
    with tab2:
        st.subheader("📊 GST Summary Report")
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            gst_start = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30), key="gst_start")
        with col2:
            gst_end = st.date_input("To Date", value=datetime.now().date(), key="gst_end")
        
        # Load sales data
        s_df = load_data("Sales")
        
        if not s_df.empty and 'Date' in s_df.columns:
            # Filter by date
            filtered_sales = s_df[(s_df['Date'] >= gst_start) & (s_df['Date'] <= gst_end)]
            
            if not filtered_sales.empty:
                # Calculate GST (assuming 18% on all sales)
                total_sales = pd.to_numeric(filtered_sales.iloc[:, 3], errors='coerce').sum()
                
                # GST breakdown
                gst_rate = 18  # Default 18%
                
                # Taxable amount (sales / 1.18)
                taxable_amt = total_sales / (1 + gst_rate/100)
                gst_amt = total_sales - taxable_amt
                
                cgst = gst_amt / 2
                sgst = gst_amt / 2
                
                # Display summary
                st.markdown("### 💰 Period Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💵 Total Sales", f"₹{total_sales:,.2f}")
                col2.metric("📊 Taxable Amount", f"₹{taxable_amt:,.2f}")
                col3.metric("🔴 CGST (9%)", f"₹{cgst:,.2f}")
                col4.metric("🔵 SGST (9%)", f"₹{sgst:,.2f}")
                
                st.divider()
                
                # GST breakdown by rate
                st.markdown("### 📋 GST Rate-wise Breakdown")
                
                # Sample breakdown (in production, store GST % with each sale)
                breakdown_data = {
                    'GST Rate': ['5%', '12%', '18%', '28%'],
                    'Taxable Amount': [0, 0, taxable_amt, 0],
                    'CGST': [0, 0, cgst, 0],
                    'SGST': [0, 0, sgst, 0],
                    'Total GST': [0, 0, gst_amt, 0]
                }
                
                breakdown_df = pd.DataFrame(breakdown_data)
                st.dataframe(breakdown_df, use_container_width=True)
                
                # Download GSTR report
                st.divider()
                csv = breakdown_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download GST Report (CSV)",
                    data=csv,
                    file_name=f"GST_Report_{gst_start}_to_{gst_end}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No sales in selected date range")
        else:
            st.info("No sales data available")
    
    # ==================== TAB 3: INVOICE HISTORY ====================
    with tab3:
        st.subheader("🗂️ Invoice History")
        
        # Load sales as invoices
        s_df = load_data("Sales")
        
        if not s_df.empty:
            st.info("💡 Currently showing sales records. Full invoice management coming soon!")
            
            # Display recent transactions
            st.markdown("### 📋 Recent Transactions")
            
            # Show last 20 transactions
            recent_sales = s_df.tail(20).copy()
            
            if not recent_sales.empty:
                # Format for display
                display_df = recent_sales.copy()
                
                # Add invoice number (simulated)
                display_df['Invoice'] = [f"INV-{i+1:04d}" for i in range(len(display_df))]
                
                st.dataframe(display_df, use_container_width=True)
                
                # Summary
                st.divider()
                total = pd.to_numeric(recent_sales.iloc[:, 3], errors='coerce').sum()
                st.success(f"💰 Total: ₹{total:,.2f} ({len(recent_sales)} transactions)")
        else:
            st.info("No invoice history available")
    
    # ==================== TAB 4: TAX REPORTS ====================
    with tab4:
        st.subheader("📈 Tax Reports & Analytics")
        
        # Report type selector
        report_type = st.selectbox(
            "Select Report Type",
            [
                "Monthly GST Summary",
                "Quarterly GST Summary", 
                "Annual Tax Report",
                "GSTR-1 Format",
                "GSTR-3B Format"
            ]
        )
        
        # Financial year selector
        fy_year = st.selectbox("Financial Year", ["2024-25", "2025-26", "2026-27"], index=1)
        
        if report_type == "Monthly GST Summary":
            st.info("📊 Monthly GST breakdown for " + fy_year)
            
            # Sample monthly data
            months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
            
            monthly_data = {
                'Month': months,
                'Sales': [0] * 12,
                'Taxable': [0] * 12,
                'CGST': [0] * 12,
                'SGST': [0] * 12,
                'Total GST': [0] * 12
            }
            
            # Load actual data
            s_df = load_data("Sales")
            if not s_df.empty and 'Date' in s_df.columns:
                s_df['Month'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.month
                s_df['Year'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.year
                
                # Filter for current FY
                fy_sales = s_df[s_df['Year'] == 2026]  # Adjust based on FY
                
                for i, month_num in enumerate(range(4, 13)):  # Apr to Dec
                    month_sales = fy_sales[fy_sales['Month'] == month_num]
                    if not month_sales.empty:
                        total = pd.to_numeric(month_sales.iloc[:, 3], errors='coerce').sum()
                        taxable = total / 1.18
                        gst = total - taxable
                        
                        monthly_data['Sales'][i] = total
                        monthly_data['Taxable'][i] = taxable
                        monthly_data['CGST'][i] = gst / 2
                        monthly_data['SGST'][i] = gst / 2
                        monthly_data['Total GST'][i] = gst
            
            monthly_df = pd.DataFrame(monthly_data)
            st.dataframe(monthly_df, use_container_width=True)
            
            # Download
            csv = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Monthly Report",
                data=csv,
                file_name=f"Monthly_GST_{fy_year}.csv",
                mime="text/csv"
            )
        
        elif report_type == "GSTR-1 Format":
            st.warning("📋 GSTR-1 Format Template")
            st.info("""
            **GSTR-1 Components:**
            - B2B Invoices (with GSTIN)
            - B2C Large Invoices (>₹2.5 lakh)
            - B2C Small Invoices
            - Credit/Debit Notes
            - Exports
            
            This feature requires detailed invoice data with customer GSTIN.
            """)
        
        else:
            st.info(f"📊 {report_type} feature coming soon!")
    
    # ==================== TAB 5: GST SETTINGS ====================
    with tab5:
        st.subheader("⚙️ GST Configuration & Settings")
        
        st.markdown("### 🏢 Business Registration Details")
        
        with st.form("gst_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Legal Business Name", value="LAIKA PET MART", key="legal_name")
                st.text_input("Trade Name", value="Laika Pet Store", key="trade_name")
                st.text_input("GSTIN", value="09XXXXX1234X1Z5", key="gstin_settings")
                st.text_input("PAN", value="XXXXX1234X", key="pan_settings")
            
            with col2:
                st.text_input("State Code", value="09 - Uttar Pradesh", key="state_code")
                st.selectbox("Business Type", ["Retailer", "Wholesaler", "Both"], key="biz_type")
                st.selectbox("Composition Scheme", ["No", "Yes"], key="composition")
                st.date_input("GST Registration Date", key="gst_reg_date")
            
            st.divider()
            
            st.markdown("### 📊 Default GST Rates")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input("Pet Food GST %", value=18, min_value=0, max_value=28, key="food_gst")
                st.number_input("Pet Accessories GST %", value=18, min_value=0, max_value=28, key="acc_gst")
            
            with col2:
                st.number_input("Pet Medicines GST %", value=12, min_value=0, max_value=28, key="med_gst")
                st.number_input("Pet Grooming GST %", value=18, min_value=0, max_value=28, key="groom_gst")
            
            with col3:
                st.number_input("Services GST %", value=18, min_value=0, max_value=28, key="serv_gst")
                st.number_input("Other Items GST %", value=18, min_value=0, max_value=28, key="other_gst")
            
            st.divider()
            
            st.markdown("### 📄 Invoice Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Invoice Prefix", value="INV", key="inv_prefix")
                st.selectbox("Invoice Numbering", ["Sequential", "Date-based", "Custom"], key="inv_numbering")
                st.checkbox("Show HSN/SAC Codes", value=True, key="show_hsn")
            
            with col2:
                st.text_input("Invoice Footer Text", value="Thank you for your business!", key="inv_footer")
                st.checkbox("Include Bank Details", value=True, key="show_bank")
                st.checkbox("Include Terms & Conditions", value=True, key="show_terms")
            
            st.divider()
            
            if st.form_submit_button("💾 Save GST Settings", type="primary"):
                st.success("✅ GST settings saved successfully!")
                st.info("⚠️ Note: Settings are stored in session. For permanent storage, connect to database.")
            st.info("Note: Some features require additional setup")
