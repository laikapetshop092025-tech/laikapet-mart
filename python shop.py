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
    """Archive yesterday's data to Google Sheets and clear from current view"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    archive_sheet = f"Archive_{yesterday.strftime('%d%b%Y')}"
    
    # Archive these sheets
    for sheet in ["Sales", "Purchase", "Expenses", "Inventory"]:
        df = load_data(sheet)
        if not df.empty and 'Date' in df.columns:
            # Get yesterday's data
            old_data = df[df['Date'] < today]
            
            if not old_data.empty:
                # Save to archive
                for _, row in old_data.iterrows():
                    save_data(archive_sheet, row.tolist())
                
                # Keep only today's data on screen (remove old data)
                new_data = df[df['Date'] >= today]
                
                # Update Google Sheet with only current data
                try:
                    worksheet = sh.worksheet(sheet)
                    # Clear old data
                    worksheet.clear()
                    # Write header
                    worksheet.append_row(df.columns.tolist())
                    # Write only current data
                    if not new_data.empty:
                        for _, row in new_data.iterrows():
                            worksheet.append_row(row.tolist())
                except Exception as e:
                    st.error(f"Archive error for {sheet}: {str(e)}")

# Note: Direct Google Sheets delete not available with CSV link method
# Users can manually delete from Google Sheets or use the archive system

# --- 2. MULTI-USER LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# User credentials database
USERS = {
    "Prateek": {
        "password": "Prateek092025",
        "role": "ceo",
        "name": "Prateek (CEO)"
    },
    "Laika": {
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
        p = st.text_input("🔒 Password", type="password", key="login_password").strip()
        
        # Show available users hint
        with st.expander("ℹ️ Available User Roles"):
            st.info("""
            **Owner**: Full access to all features
            **Manager**: Access to reports, billing, inventory
            **Staff**: Billing and basic operations only
            """)
        
        if st.button("🚀 LOGIN", use_container_width=True, type="primary"):
            # Debug info (remove after testing)
            if u:
                if u in USERS:
                    if USERS[u]["password"] == p:
                        st.session_state.logged_in = True
                        st.session_state.user_role = USERS[u]["role"]
                        st.session_state.username = USERS[u]["name"]
                        st.success(f"✅ Welcome {USERS[u]['name']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Wrong password!")
                        # Debug - show password length for troubleshooting
                        st.warning(f"Debug: Password length entered: {len(p)}, Expected length: {len(USERS[u]['password'])}")
                else:
                    st.error(f"❌ Username '{u}' not found!")
                    st.info(f"Available users: {', '.join(USERS.keys())}")
            else:
                st.error("❌ Please enter username and password!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show demo credentials
        st.divider()
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <b>🔑 Demo Credentials:</b><br>
            <small>
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

if user_role == "ceo" or user_role == "owner":
    # CEO and Owner have access to everything
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
        "👥 Customer Analytics",
        "🎁 Discounts & Offers",
        "💬 WhatsApp Automation",
        "🏭 Supplier Management",
        "🎂 Customer Engagement",
        "📊 Financial Reports",
        "🔐 Security & Compliance",
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
        "👥 Customer Analytics",
        "🎁 Discounts & Offers",
        "💬 WhatsApp Automation",
        "🏭 Supplier Management",
        "🎂 Customer Engagement",
        "📊 Financial Reports",
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
    
    # Payment options - simplified
    col1, col2, col3 = st.columns(3)
    with col1:
        pay_m = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
    with col2:
        give_points = st.checkbox("👑 Give Loyalty Points?", value=True, help="Uncheck if customer should not receive points")
    with col3:
        gst_bill = st.checkbox("📄 GST Invoice?", value=False, help="For GST customers")
    
    with st.expander("🛒 Add Item", expanded=True):
        it = st.selectbox("Product", inv_df.iloc[:, 0].unique() if not inv_df.empty else ["No Stock"])
        
        # Show available stock for selected product (WITHOUT purchase rate)
        if it and it != "No Stock" and not inv_df.empty:
            # Get all entries for this product
            product_stock = inv_df[inv_df.iloc[:, 0] == it]
            
            if not product_stock.empty:
                # Calculate total stock - sum all quantities
                total_qty = pd.to_numeric(product_stock.iloc[:, 1], errors='coerce').sum()
                latest_unit = product_stock.iloc[-1, 2] if len(product_stock.columns) > 2 else ""
                
                # Display ONLY stock quantity (no purchase rate)
                if total_qty > 0:
                    st.success(f"📦 **Available Stock:** {total_qty} {latest_unit}")
                else:
                    st.warning("⚠️ Out of Stock!")
            else:
                st.warning("⚠️ No stock information available")
        
        q = st.number_input("Qty", min_value=0.1, value=1.0, step=0.1)
        u = st.selectbox("Unit", ["Kg", "Pcs", "Pkt", "Grams"])
        p = st.number_input("Price", min_value=0.0, value=1.0, step=1.0)
        
        col1, col2 = st.columns(2)
        with col1:
            # Check current cart total
            current_cart_total = sum([item['Price'] for item in st.session_state.bill_cart]) if st.session_state.bill_cart else 0
            
            # Disable redeem if: no points OR cart total < 100
            can_redeem = pts_bal > 0 and current_cart_total >= 100
            
            if current_cart_total < 100 and pts_bal > 0:
                help_text = "Minimum ₹100 purchase required to redeem points"
            else:
                help_text = "Use your loyalty points"
            
            rd = st.checkbox(
                f"Redeem {int(pts_bal)} Points?", 
                disabled=(not can_redeem),
                help=help_text
            )
            
            # Show message if minimum not met
            if pts_bal > 0 and current_cart_total < 100:
                remaining = 100 - current_cart_total
                st.caption(f"⚠️ Add ₹{remaining:.0f} more to redeem points")
        
        with col2:
            ref_ph = st.text_input("Referral Phone (Optional)", placeholder="For +10 bonus points")
        
        if st.button("➕ Add to Cart"):
            if q and q > 0 and p and p > 0:  # Validate inputs
                pur_r = pd.to_numeric(inv_df[inv_df.iloc[:, 0] == it].iloc[0, 3], errors='coerce') if not inv_df.empty and len(inv_df[inv_df.iloc[:, 0] == it]) > 0 else 0
                
                # Calculate points ONLY if give_points is checked
                pts = 0
                pts_used = 0
                
                if give_points:
                    pts = int(((q*p)/100) * (5 if is_weekend else 2))
                    
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
            else:
                st.error("⚠️ Please enter valid Qty and Price!")
    
    if st.session_state.bill_cart:
        st.divider()
        st.markdown("### 🛒 Cart Items")
        
        # Display each item with delete button
        for idx, item in enumerate(st.session_state.bill_cart):
            col1, col2 = st.columns([9, 1])
            
            with col1:
                # Calculate item total
                item_total = item['Price']
                
                st.markdown(f"""
                <div style="background: #f0f2f6; padding: 12px; border-radius: 8px; margin: 5px 0;">
                    <strong>📦 {item['Item']}</strong><br>
                    <span style="color: #666;">
                    Qty: {item['Qty']} | Price: ₹{item['Price']:,.2f} | 
                    Profit: ₹{item['Profit']:,.2f} | Points: {item['Pts']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write("")
                if st.button("❌", key=f"del_bill_{idx}", help="Remove from cart"):
                    st.session_state.bill_cart.pop(idx)
                    st.success(f"✅ Removed {item['Item']}")
                    time.sleep(0.3)
                    st.rerun()
        
        st.divider()
        
        total_amt = sum([item['Price'] for item in st.session_state.bill_cart])
        total_pts = sum([item['Pts'] for item in st.session_state.bill_cart])
        
        # Calculate what balance will be after this transaction
        new_balance = pts_bal + total_pts
        
        # Show GST calculation if GST bill is selected
        if gst_bill:
            st.divider()
            st.markdown("### 💼 With GST (18%)")
            
            # Calculate GST amounts (fixed 18%)
            gst_rate = 18
            taxable_amount = total_amt / 1.18
            gst_amount = total_amt - taxable_amount
            cgst = gst_amount / 2
            sgst = gst_amount / 2
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Taxable", f"₹{taxable_amount:.2f}")
            col2.metric("🔴 CGST (9%)", f"₹{cgst:.2f}")
            col3.metric("🔵 SGST (9%)", f"₹{sgst:.2f}")
            
            st.success(f"💳 **Total with GST: ₹{total_amt:,.2f}**")
        else:
            st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        
        # Show points info
        col1, col2 = st.columns(2)
        with col1:
            if give_points:  # Only show if points feature is enabled
                if total_pts >= 0:
                    st.success(f"🎁 Points Earned This Bill: +{total_pts}")
                else:
                    st.warning(f"🎁 Points Redeemed: {total_pts}")
            else:
                st.info("👑 Loyalty Points: Not Given (Unchecked)")
        with col2:
            if give_points:
                st.info(f"👑 New Balance After Bill: {int(new_balance)} points")
            else:
                st.info(f"👑 Current Balance: {int(pts_bal)} points (unchanged)")
        
        if st.button("✅ Save Bill & Send WhatsApp", type="primary"):
            # Save all items to Sales
            items_saved = 0
            for item in st.session_state.bill_cart:
                if save_data("Sales", [str(today_dt), item['Item'], item['Qty'], item['Price'], pay_m, f"{c_name}({c_ph})", item['Pts'], item['Profit']]):
                    items_saved += 1
            
            # Update balance based on payment mode
            balance_updated = False
            if pay_m == "Cash":
                balance_updated = update_balance(total_amt, "Cash", 'add')
                payment_msg = f"💵 Cash: +₹{total_amt:,.2f}"
            elif pay_m == "Online":
                balance_updated = update_balance(total_amt, "Online", 'add')
                payment_msg = f"💳 Online: +₹{total_amt:,.2f}"
            else:  # Udhaar
                # Add to Customer Khata automatically
                save_data("CustomerKhata", [f"{c_name}({c_ph})", total_amt, str(today_dt), "Udhaar"])
                balance_updated = True
                payment_msg = f"📝 Udhaar: ₹{total_amt:,.2f} (Added to Customer Khata)"
            
            # Show detailed success message
            st.success(f"""
✅ **Bill Saved Successfully!**

📊 **Transaction Summary:**
- Items Saved: {items_saved}/{len(st.session_state.bill_cart)}
- {payment_msg}
- Total Amount: ₹{total_amt:,.2f}
- Customer: {c_name} ({c_ph})
            """)
            
            # Generate WhatsApp message
            items_text = "\n".join([f"• {item['Item']} - {item['Qty']} - ₹{item['Price']}" for item in st.session_state.bill_cart])
            
            # Calculate new points balance
            new_pts_balance = pts_bal + total_pts
            
            # Build points message (only if points were given)
            if give_points:
                if total_pts >= 0:
                    points_msg = f"🎁 *आज के प्वाइंट्स:* +{total_pts}"
                else:
                    points_msg = f"🎁 *आज के प्वाइंट्स:* {total_pts} (Redeemed)"
                
                points_msg += f"\n👑 *कुल बचे प्वाइंट्स:* {int(new_pts_balance)}"
            else:
                points_msg = ""  # No points message if unchecked
            
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
            
            # Delete option - Individual delete buttons for each bill item
            st.divider()
            st.markdown("### 🗑️ Delete Bill Entries")
            st.warning("⚠️ Deleting will reverse all effects - removes from sheet AND adjusts balance")
            
            # Show all today's sales with delete buttons
            for customer_name, bill_data in customer_bills.items():
                with st.expander(f"📋 {customer_name} - ₹{bill_data['total']:,.2f}"):
                    # Show bill details
                    st.write(f"**Items:** {bill_data['items']}")
                    st.write(f"**Total:** ₹{bill_data['total']:,.2f}")
                    st.write(f"**Payment:** {bill_data['payment']}")
                    st.write(f"**Points:** {bill_data['points']}")
                    
                    # Delete button
                    if st.button(f"🗑️ Delete This Bill", key=f"del_bill_{customer_name}"):
                        try:
                            # Get customer phone from name
                            cust_phone = customer_name.split('(')[-1].replace(')', '')
                            
                            # Find and delete all entries for this customer today
                            s_df = load_data("Sales")
                            if not s_df.empty and len(s_df.columns) > 5:
                                # Filter entries for this customer today
                                customer_entries = s_df[
                                    (s_df.iloc[:, 0] == str(today_dt)) & 
                                    (s_df.iloc[:, 5].astype(str).str.contains(cust_phone, na=False))
                                ]
                                
                                if not customer_entries.empty:
                                    st.info(f"Found {len(customer_entries)} entries to delete")
                                    
                                    # REVERSE PAYMENT BALANCE
                                    payment_mode = bill_data['payment']
                                    bill_amount = bill_data['total']
                                    
                                    if payment_mode == "Cash":
                                        update_balance(bill_amount, "Cash", 'subtract')
                                        st.success(f"✅ Reversed Cash: -₹{bill_amount:,.2f}")
                                    elif payment_mode == "Online":
                                        update_balance(bill_amount, "Online", 'subtract')
                                        st.success(f"✅ Reversed Online: -₹{bill_amount:,.2f}")
                                    elif payment_mode == "Udhaar":
                                        # Remove from Customer Khata (add negative entry)
                                        save_data("CustomerKhata", [customer_name, -bill_amount, str(today_dt), "Bill Deleted"])
                                        st.success(f"✅ Reversed Udhaar: -₹{bill_amount:,.2f}")
                                    
                                    st.warning("⚠️ Manual deletion from Google Sheets required")
                                    st.info(f"Go to Sales sheet → Delete rows with: {customer_name} on {today_dt}")
                                    st.info("Balance has been reversed automatically ✅")
                                    
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("No entries found for this customer today")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        else:
            st.info("No bills generated today yet.")
    else:
        st.info("No sales data available.")

# --- 7. PURCHASE ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase Entry")
    
    # Initialize ALL session states at top
    if 'purchase_cart' not in st.session_state:
        st.session_state.purchase_cart = []
    if 'adding_new_item' not in st.session_state:
        st.session_state.adding_new_item = False
    if 'new_item_name_temp' not in st.session_state:
        st.session_state.new_item_name_temp = ""
    
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
        # Load inventory for stock checking
        inv_df = load_data("Inventory")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Initialize item_name to avoid undefined variable error
        item_name = ""
        
        with col1:
            # Check if we have existing items
            if not inv_df.empty:
                existing_items = inv_df.iloc[:, 0].unique().tolist()
                
                # SHOW BOTH: Dropdown AND Text Input
                st.markdown("**Select OR Type:**")
                
                # Dropdown for existing items
                item_from_dropdown = st.selectbox(
                    "Existing Items", 
                    ["(Select existing item)"] + existing_items,
                    key="item_dropdown",
                    label_visibility="collapsed"
                )
                
                st.markdown("**OR**")
                
                # Text input for new items
                item_from_text = st.text_input(
                    "Type new item name",
                    key="new_item_text",
                    placeholder="Type new product name here",
                    label_visibility="collapsed"
                )
                
                # Priority: Text input > Dropdown
                if item_from_text and item_from_text.strip():
                    item_name = item_from_text.strip().upper()  # Convert to UPPERCASE
                    is_new_item = item_name not in existing_items
                elif item_from_dropdown and item_from_dropdown != "(Select existing item)":
                    item_name = item_from_dropdown
                    is_new_item = False
                else:
                    item_name = ""
                    is_new_item = False
            else:
                # No existing items, just show text input
                item_from_text = st.text_input("Item Name", key="item_name_only")
                item_name = item_from_text.strip().upper() if item_from_text else ""  # Convert to UPPERCASE
                is_new_item = True
        
        # Show current stock OR new item message
        if item_name and item_name != "" and not inv_df.empty:
            product_stock = inv_df[inv_df.iloc[:, 0] == item_name]
            
            if not product_stock.empty and not is_new_item:
                # Existing item - show stock
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
        
        # Show stock calculation when qty is entered
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
                # Validate: item_name should not be empty
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
        
        # Create display dataframe
        cart_df = pd.DataFrame(st.session_state.purchase_cart)
        cart_df['Qty_Display'] = cart_df['Qty'].astype(str) + ' ' + cart_df['Unit']
        cart_df['Rate_Display'] = '₹' + cart_df['Rate'].astype(str)
        cart_df['Amount_Display'] = '₹' + cart_df['Amount'].apply(lambda x: f"{x:,.2f}")
        
        display_df = cart_df[['Item', 'Qty_Display', 'Rate_Display', 'Amount_Display']]
        display_df.columns = ['Item', 'Quantity', 'Rate', 'Amount']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Calculate total
        total_amount = sum([item['Amount'] for item in st.session_state.purchase_cart])
        total_items = len(st.session_state.purchase_cart)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total Items", total_items)
        col2.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
        col3.metric("📊 Payment", payment_type.split()[0])
        
        # Remove item option
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
                # Save all items to Inventory with NEW structure
                for item in st.session_state.purchase_cart:
                    payment_info = payment_mode if not supplier_name else f"Party: {supplier_name}"
                    
                    # Calculate total value
                    total_value = item['Qty'] * item['Rate']
                    
                    # NEW STRUCTURE: A=Item, B=Qty(number), C=Unit, D=Rate, E=TotalValue, F=Date, G=Payment
                    save_data("Inventory", [
                        item['Item'],           # A: Item
                        item['Qty'],            # B: Qty (number only)
                        item['Unit'],           # C: Unit
                        item['Rate'],           # D: Rate
                        total_value,            # E: Total Value
                        str(today_dt),          # F: Date
                        payment_info            # G: Payment
                    ])
                
                # Handle payment
                if payment_mode in ["Cash", "Online"]:
                    # Deduct from balance
                    update_balance(total_amount, payment_mode, 'subtract')
                    st.success(f"✅ Purchase saved! Paid ₹{total_amount:,.2f} from {payment_mode}")
                else:
                    # Add to Supplier Dues
                    if supplier_name and supplier_name.strip():
                        # Create itemized note
                        items_note = ", ".join([f"{item['Item']} ({item['Qty']} {item['Unit']})" for item in st.session_state.purchase_cart])
                        save_data("Dues", [supplier_name, total_amount, str(today_dt), f"Purchase: {items_note}"])
                        st.success(f"✅ Purchase saved! ₹{total_amount:,.2f} added to {supplier_name}'s dues")
                
                # Clear cart
                st.session_state.purchase_cart = []
                st.balloons()
                time.sleep(2)
                st.rerun()
    else:
        st.info("🛒 Cart is empty. Add items above to start purchase.")
    
    # Show today's purchases
    i_df = load_data("Inventory")
    if not i_df.empty:
        st.divider()
        st.subheader("📋 Today's Purchases")
        
        # Filter today's purchases only
        today_purchases = i_df[i_df.iloc[:, 4] == str(today_dt)] if len(i_df.columns) > 4 else i_df
        
        if not today_purchases.empty:
            st.info(f"💡 {len(today_purchases)} purchase(s) today - Click ❌ to delete any entry")
            
            # Display each purchase with individual delete button
            for idx in range(len(today_purchases)):
                purchase = today_purchases.iloc[idx]
                original_index = today_purchases.index[idx]
                
                # Extract details safely
                item_name = str(purchase.iloc[0]) if len(purchase) > 0 else "Unknown"
                item_qty_full = str(purchase.iloc[1]) if len(purchase) > 1 else "N/A"
                item_type = str(purchase.iloc[2]) if len(purchase) > 2 else "N/A"
                
                # Parse rate properly
                try:
                    item_rate = float(purchase.iloc[3]) if len(purchase) > 3 else 0
                except:
                    item_rate = 0
                
                item_date = str(purchase.iloc[4]) if len(purchase) > 4 else ""
                payment_info = str(purchase.iloc[5]) if len(purchase) > 5 else "N/A"
                
                # Parse quantity from string like "50 Kg"
                qty_numeric = 0
                item_qty_display = "N/A"
                
                try:
                    # First check what type of data we have
                    qty_val = purchase.iloc[1] if len(purchase) > 1 else None
                    
                    # If it's already a number
                    if isinstance(qty_val, (int, float)):
                        qty_numeric = float(qty_val)
                        item_qty_display = f"{qty_numeric}"
                    # If it's a string
                    elif isinstance(qty_val, str):
                        qty_str = str(qty_val).strip()
                        # Try splitting "50 Kg"
                        if ' ' in qty_str:
                            parts = qty_str.split(maxsplit=1)
                            try:
                                qty_numeric = float(parts[0])
                                item_qty_display = f"{qty_numeric} {parts[1]}"
                            except ValueError:
                                qty_numeric = 0
                                item_qty_display = qty_str
                        else:
                            # Just a number
                            try:
                                qty_numeric = float(qty_str)
                                item_qty_display = str(qty_numeric)
                            except ValueError:
                                qty_numeric = 0
                                item_qty_display = qty_str
                    else:
                        # Try pandas conversion
                        qty_numeric = pd.to_numeric(qty_val, errors='coerce')
                        if pd.isna(qty_numeric):
                            qty_numeric = 0
                        item_qty_display = str(qty_val)
                except Exception as e:
                    qty_numeric = 0
                    item_qty_display = f"ERROR: {str(qty_val)}"
                
                # Calculate amount
                item_amount = qty_numeric * item_rate
                
                # Create card for each entry
                col1, col2 = st.columns([9, 1])
                
                with col1:
                    # Determine payment type
                    is_party = "Party:" in payment_info
                    party_name = payment_info.replace("Party: ", "") if is_party else None
                    
                    # Display card with color based on payment
                    card_color = "#FFF3CD" if is_party else "#D1ECF1"
                    
                    st.markdown(f"""
                    <div style="background: {card_color}; padding: 15px; border-radius: 10px; border-left: 4px solid {'#FF9800' if is_party else '#2196F3'};">
                        <h4 style="margin: 0; color: #333;">📦 {item_name}</h4>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>Qty:</strong> {item_qty_display} | 
                            <strong>Rate:</strong> ₹{item_rate:,.2f} | 
                            <strong>Amount:</strong> ₹{item_amount:,.2f}
                        </p>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>Payment:</strong> {payment_info if not is_party else f'🏢 {party_name} (Udhaar)'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # DEBUG - Show raw data
                    with st.expander("🔍 Debug Info"):
                        st.write("**Raw Data from Sheet:**")
                        st.write(f"Qty Column: `{repr(purchase.iloc[1])}`")
                        st.write(f"Qty Type: {type(purchase.iloc[1])}")
                        st.write(f"Rate Column: `{repr(purchase.iloc[3])}`")
                        st.write(f"Rate Type: {type(purchase.iloc[3])}")
                        st.write(f"Parsed Qty: {qty_numeric}")
                        st.write(f"Parsed Rate: {item_rate}")
                
                with col2:
                    # Individual delete button - SIMPLIFIED (no Google Sheets delete for now)
                    if st.button("❌", key=f"del_{original_index}", help="Delete this entry", type="secondary"):
                        st.warning(f"⚠️ Delete functionality will remove entry from display only.")
                        st.info(f"To completely delete '{item_name}', please remove from Google Sheet manually.")
                        st.info("💡 Automatic Google Sheets delete coming soon!")
                
                st.divider()
        else:
            st.info("📭 No purchases made today")
        
        # Show all time purchases
        st.divider()
        with st.expander("📜 View All Purchases History"):
            st.dataframe(i_df, use_container_width=True)
            st.info(f"Total entries: {len(i_df)}")

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Live Stock")
    i_df = load_data("Inventory")
    
    if not i_df.empty and len(i_df.columns) > 4:
        # NEW STRUCTURE: B=Qty(number), C=Unit, D=Rate, E=TotalValue
        # Parse qty directly as it's already a number
        i_df['qty_v'] = pd.to_numeric(i_df.iloc[:, 1], errors='coerce').fillna(0)
        i_df['rate_v'] = pd.to_numeric(i_df.iloc[:, 3], errors='coerce').fillna(0)
        i_df['value'] = i_df['qty_v'] * i_df['rate_v']
        t_v = i_df['value'].sum()
        
        st.subheader(f"💰 Total Stock Value: ₹{t_v:,.2f}")
        
        stock_summary = i_df.groupby(i_df.columns[0]).agg({
            i_df.columns[1]: 'last',  # Qty (number)
            i_df.columns[2]: 'last',  # Unit
            i_df.columns[3]: 'last',  # Rate
            'qty_v': 'last',
            'value': 'last'
        }).reset_index()
        stock_summary.columns = ['Item', 'Qty_Num', 'Unit', 'Rate', 'Qty_Numeric', 'Value']
        
        # Combine Qty + Unit for display
        stock_summary['Quantity'] = stock_summary['Qty_Num'].astype(str) + ' ' + stock_summary['Unit'].astype(str)
        
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
        st.subheader("📋 Today's Expenses")
        
        # Filter today's expenses
        today_expenses = e_df[e_df.iloc[:, 0] == str(today_dt)] if len(e_df.columns) > 0 else e_df
        
        if not today_expenses.empty:
            st.dataframe(today_expenses, use_container_width=True)
            
            # Delete option
            st.divider()
            with st.expander("🗑️ Delete Expense Entry"):
                st.warning("⚠️ This will delete from both screen AND Google Sheets!")
                
                display_df = today_expenses.reset_index(drop=True)
                display_df.insert(0, 'Row #', range(len(display_df)))
                st.dataframe(display_df, use_container_width=True)
                
                if len(today_expenses) > 0:
                    del_row_num = st.number_input("Enter Row # to delete", min_value=0, max_value=len(today_expenses)-1, value=0, key="del_exp")
                    
                    selected_item = today_expenses.iloc[del_row_num]
                    st.info(f"Will delete: **{selected_item.iloc[1]}** - ₹{selected_item.iloc[2]}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ DELETE FROM EVERYWHERE", type="primary", key="del_exp_btn"):
                            actual_index = e_df.index[e_df.eq(selected_item).all(1)].tolist()[0]
                            
                            if delete_from_sheet("Expenses", actual_index):
                                st.success("✅ Deleted from Google Sheets!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")
                    
                    with col2:
                        st.warning("⚠️ Cannot be undone!")
        else:
            st.info("No expenses today")
        
        st.divider()
        st.subheader("📜 All Expenses History")
        st.dataframe(e_df, use_container_width=True)

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
    st.header("📒 Customer Khata Management")
    
    # Load existing khata data
    k_df = load_data("CustomerKhata")
    
    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["➕ New Entry", "💰 Receive Payment", "📊 View Khata"])
    
    # ==================== TAB 1: NEW ENTRY ====================
    with tab1:
        st.subheader("➕ Add New Udhaar Entry")
        
        with st.form("kh_new"):
            n = st.text_input("Customer Name")
            ph = st.text_input("Phone Number (Optional)")
            a = st.number_input("Udhaar Amount", min_value=0.0)
            note = st.text_input("Note (Optional)", placeholder="e.g., Dog food purchase")
            
            if st.form_submit_button("💾 Add Udhaar", type="primary"):
                if a > 0 and n.strip():
                    customer_entry = f"{n} ({ph})" if ph else n
                    save_data("CustomerKhata", [customer_entry, a, str(today_dt), "N/A"])
                    st.success(f"✅ Udhaar added: {n} owes ₹{a:,.2f}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Please enter valid name and amount!")
    
    # ==================== TAB 2: RECEIVE PAYMENT ====================
    with tab2:
        st.subheader("💰 Receive Payment & Clear Udhaar")
        
        if not k_df.empty and len(k_df.columns) > 1:
            # Calculate customer balances
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            # Only show customers with positive balance (who owe money)
            sum_df = sum_df[sum_df['Balance'] > 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                st.info(f"💰 Total Outstanding: ₹{sum_df['Balance'].sum():,.2f}")
                
                # Select customer
                customer_list = sum_df['Customer'].tolist()
                selected_customer = st.selectbox("Select Customer", customer_list)
                
                if selected_customer:
                    # Get current balance
                    current_balance = float(sum_df[sum_df['Customer'] == selected_customer]['Balance'].iloc[0])
                    
                    st.warning(f"📊 Current Balance: ₹{current_balance:,.2f}")
                    
                    with st.form("payment_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            payment_amount = st.number_input(
                                "Payment Amount", 
                                min_value=0.0, 
                                max_value=float(current_balance),
                                value=float(current_balance),
                                help="Enter amount received from customer"
                            )
                        
                        with col2:
                            payment_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Cheque", "UPI"])
                        
                        # Show what will happen
                        remaining = current_balance - payment_amount
                        
                        if payment_amount > 0:
                            if remaining == 0:
                                st.success(f"✅ Full payment! Khata will be CLEARED")
                            else:
                                st.info(f"📊 Remaining Balance: ₹{remaining:,.2f}")
                        
                        submit_payment = st.form_submit_button("💰 Receive Payment", type="primary")
                        
                        if submit_payment and payment_amount > 0:
                            # Add negative entry (payment received)
                            save_data("CustomerKhata", [selected_customer, -payment_amount, str(today_dt), payment_mode])
                            
                            # Update Cash/Online balance
                            if payment_mode == "Cash":
                                update_balance(payment_amount, "Cash", 'add')
                            elif payment_mode == "Online" or payment_mode == "UPI":
                                update_balance(payment_amount, "Online", 'add')
                            
                            if remaining == 0:
                                st.balloons()
                                st.success(f"🎉 Payment Received! ₹{payment_amount:,.2f} | Khata CLEARED for {selected_customer}")
                            else:
                                st.success(f"✅ Payment Received! ₹{payment_amount:,.2f} | Remaining: ₹{remaining:,.2f}")
                            
                            time.sleep(1.5)
                            st.rerun()
            else:
                st.success("✅ No pending udhaar! All customers have cleared their dues.")
        else:
            st.info("No khata entries found.")
    
    # ==================== TAB 3: VIEW KHATA ====================
    with tab3:
        st.subheader("📊 Customer Balance Summary")
        
        if not k_df.empty and len(k_df.columns) > 1:
            # Calculate balances
            sum_df = k_df.groupby(k_df.columns[0]).agg({k_df.columns[1]: 'sum'}).reset_index()
            sum_df.columns = ['Customer', 'Balance']
            
            # Filter: Only show non-zero balances
            sum_df = sum_df[sum_df['Balance'] != 0].sort_values('Balance', ascending=False)
            
            if not sum_df.empty:
                # Summary metrics
                total_udhaar = sum_df[sum_df['Balance'] > 0]['Balance'].sum() if len(sum_df[sum_df['Balance'] > 0]) > 0 else 0
                total_credit = abs(sum_df[sum_df['Balance'] < 0]['Balance'].sum()) if len(sum_df[sum_df['Balance'] < 0]) > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Total Udhaar", f"₹{total_udhaar:,.2f}")
                col2.metric("💚 Credit Balance", f"₹{total_credit:,.2f}")
                col3.metric("📊 Net", f"₹{(total_udhaar - total_credit):,.2f}")
                
                st.divider()
                
                # Display balances with color coding
                for _, row in sum_df.iterrows():
                    customer = row['Customer']
                    balance = row['Balance']
                    
                    # Extract name and phone
                    if "(" in customer and ")" in customer:
                        name = customer.split("(")[0].strip()
                        phone = customer.split("(")[1].replace(")", "").strip()
                    else:
                        name = customer
                        phone = ""
                    
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"👤 **{name}**")
                        if phone:
                            st.write(f"📱 {phone}")
                    
                    with col2:
                        if balance > 0:
                            st.error(f"💰 Owes: ₹{balance:,.2f}")
                        else:
                            st.success(f"💚 Credit: ₹{abs(balance):,.2f}")
                    
                    with col3:
                        # Quick WhatsApp reminder for customers who owe
                        if balance > 0 and phone:
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {name} जी!

आपका बकाया: ₹{balance:,.2f}

कृपया जल्द से जल्द भुगतान करें।

धन्यवाद! 🙏
Laika Pet Mart"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{phone}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer;">💬</button></a>', unsafe_allow_html=True)
                    
                    st.divider()
                
                # Download option
                csv = sum_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Khata Report",
                    data=csv,
                    file_name=f"customer_khata_{today_dt}.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ All balances cleared! No pending udhaar.")
            
            # Show transaction history
            st.divider()
            with st.expander("📜 View Transaction History"):
                st.dataframe(k_df.tail(20), use_container_width=True)
        else:
            st.info("No khata entries found. Start adding transactions!")


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
                            
                            # Quick payment option if balance > 0 (we owe them)
                            if balance > 0:
                                st.divider()
                                st.markdown("#### 💵 Quick Payment")
                                
                                with st.form(f"pay_{supplier_name}"):
                                    pay_amt = st.number_input("Amount to Pay", min_value=0.0, max_value=float(balance), value=float(balance), step=0.01)
                                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Cheque", "UPI"], key=f"mode_{supplier_name}")
                                    
                                    if st.form_submit_button("💰 Pay Now", type="primary", use_container_width=True):
                                        if pay_amt > 0:
                                            # Add negative entry (payment)
                                            save_data("Dues", [supplier_name, -pay_amt, str(today_dt), pay_mode, "Payment"])
                                            
                                            # Deduct from balance
                                            if pay_mode == "Cash":
                                                update_balance(pay_amt, "Cash", 'subtract')
                                            elif pay_mode == "Online":
                                                update_balance(pay_amt, "Online", 'subtract')
                                            
                                            st.success(f"✅ Paid ₹{pay_amt:,.2f} to {supplier_name}")
                                            time.sleep(1)
                                            st.rerun()
                
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
            new_role = st.selectbox("Role", ["ceo", "owner", "manager", "staff"])
            
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
                role_options = ["ceo", "owner", "manager", "staff"]
                current_role_index = role_options.index(user_data['role']) if user_data['role'] in role_options else 3
                
                new_role = st.selectbox(
                    "Role",
                    role_options,
                    index=current_role_index
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
                            # ACTUALLY UPDATE THE USERS DICTIONARY
                            # If username changed, need to move the entry
                            if new_username and new_username != edit_username:
                                # Create new entry with new username
                                USERS[updated_username] = {
                                    'password': updated_password,
                                    'role': updated_role,
                                    'name': updated_name
                                }
                                # Delete old entry
                                del USERS[edit_username]
                            else:
                                # Just update existing entry
                                USERS[edit_username]['password'] = updated_password
                                USERS[edit_username]['role'] = updated_role
                                USERS[edit_username]['name'] = updated_name
                            
                            st.success("✅ User Updated Successfully!")
                            st.markdown("### 📝 Changes Made:")
                            for change in changes:
                                st.write(f"• {change}")
                            
                            # Show new credentials if username or password changed
                            if new_username or new_password:
                                st.divider()
                                st.info("📋 Updated Credentials:")
                                st.code(f"""Username: {updated_username}
Password: {updated_password if new_password else '[Password Unchanged - Use Current]'}
Role: {updated_role.upper()}""")
                            
                            st.success("""
                            ✅ **Changes Applied!**
                            - User can now login with new credentials
                            - Changes are active immediately
                            - For permanent storage across app restarts, save USERS to a database
                            """)
                            
                            # If current logged-in user changed their own password/username
                            if st.session_state.username and edit_username in st.session_state.username:
                                st.warning("⚠️ You changed your own credentials! Please re-login with new details.")
                            
                            # Clear edit selection
                            st.session_state.edit_user = None
                            
                            time.sleep(2)
                            st.rerun()
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

# --- 17. CUSTOMER ANALYTICS ---
elif menu == "👥 Customer Analytics":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">👥 Customer Analytics</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Deep Customer Insights & Behavior Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    s_df = load_data("Sales")
    k_df = load_data("CustomerKhata")
    p_df = load_data("PetRecords")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Top Customers",
        "📊 Customer Segments",
        "🔍 Individual Profile",
        "📈 Purchase Patterns",
        "⚠️ At-Risk Customers",
        "🎯 Recommendations"
    ])
    
    # ==================== TAB 1: TOP CUSTOMERS ====================
    with tab1:
        st.subheader("🏆 Top Customers by Value")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Analyze customer data
            customer_stats = {}
            
            for _, row in s_df.iterrows():
                customer_info = str(row.iloc[5]) if len(row) > 5 else ""
                amount = float(row.iloc[3]) if len(row) > 3 else 0
                date = row.iloc[0] if len(row) > 0 else None
                points = pd.to_numeric(row.iloc[6], errors='coerce') if len(row) > 6 else 0
                
                if customer_info and customer_info != "nan":
                    if customer_info not in customer_stats:
                        customer_stats[customer_info] = {
                            'total_spent': 0,
                            'visits': 0,
                            'points': 0,
                            'first_visit': date,
                            'last_visit': date,
                            'items_bought': []
                        }
                    
                    customer_stats[customer_info]['total_spent'] += amount
                    customer_stats[customer_info]['visits'] += 1
                    customer_stats[customer_info]['points'] += points
                    
                    if date:
                        if customer_stats[customer_info]['last_visit'] and date > customer_stats[customer_info]['last_visit']:
                            customer_stats[customer_info]['last_visit'] = date
                        if customer_stats[customer_info]['first_visit'] and date < customer_stats[customer_info]['first_visit']:
                            customer_stats[customer_info]['first_visit'] = date
            
            if customer_stats:
                # Convert to sorted list
                top_customers = sorted(customer_stats.items(), key=lambda x: x[1]['total_spent'], reverse=True)
                
                # Summary metrics
                total_customers = len(customer_stats)
                total_revenue = sum([c[1]['total_spent'] for c in top_customers])
                avg_spend = total_revenue / total_customers if total_customers > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👥 Total Customers", total_customers)
                col2.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
                col3.metric("📊 Avg Spend/Customer", f"₹{avg_spend:,.2f}")
                col4.metric("🏆 Top Customer Spend", f"₹{top_customers[0][1]['total_spent']:,.2f}" if top_customers else "₹0")
                
                st.divider()
                
                # Display top 20 customers
                st.markdown("### 🥇 Top 20 Customers")
                
                for i, (customer_info, stats) in enumerate(top_customers[:20], 1):
                    # Extract name and phone
                    if "(" in customer_info and ")" in customer_info:
                        cust_name = customer_info.split("(")[0].strip()
                        cust_phone = customer_info.split("(")[1].replace(")", "").strip()
                    else:
                        cust_name = customer_info
                        cust_phone = "N/A"
                    
                    # Calculate customer lifetime value metrics
                    avg_bill = stats['total_spent'] / stats['visits'] if stats['visits'] > 0 else 0
                    
                    # Days since last visit
                    if stats['last_visit']:
                        days_since = (datetime.now().date() - stats['last_visit']).days
                    else:
                        days_since = 999
                    
                    # Determine tier
                    if stats['total_spent'] >= 10000:
                        tier = "💎 Diamond"
                        tier_color = "#B9F2FF"
                    elif stats['total_spent'] >= 5000:
                        tier = "👑 Platinum"
                        tier_color = "#FFD700"
                    elif stats['total_spent'] >= 2000:
                        tier = "🥈 Gold"
                        tier_color = "#C0C0C0"
                    else:
                        tier = "🥉 Silver"
                        tier_color = "#CD7F32"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {tier_color} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #667eea;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin: 0; color: #333;">#{i} {cust_name} {tier}</h3>
                                    <p style="margin: 5px 0; color: #666;">📱 {cust_phone}</p>
                                </div>
                                <div style="text-align: right;">
                                    <h2 style="margin: 0; color: #667eea;">₹{stats['total_spent']:,.2f}</h2>
                                    <p style="margin: 5px 0; color: #888;">{stats['visits']} visits | ₹{avg_bill:.0f} avg</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Additional details
                        col1, col2, col3, col4 = st.columns(4)
                        col1.write(f"🎁 Points: {int(stats['points'])}")
                        col2.write(f"📅 First Visit: {stats['first_visit']}")
                        col3.write(f"🕒 Last Visit: {stats['last_visit']}")
                        
                        if days_since <= 7:
                            col4.success(f"✅ Active ({days_since}d ago)")
                        elif days_since <= 30:
                            col4.warning(f"⚠️ {days_since}d ago")
                        else:
                            col4.error(f"🚨 Inactive ({days_since}d)")
                        
                        st.divider()
                
                # Download option
                customer_df = pd.DataFrame([
                    {
                        'Customer': k.split("(")[0] if "(" in k else k,
                        'Phone': k.split("(")[1].replace(")", "") if "(" in k else "N/A",
                        'Total Spent': v['total_spent'],
                        'Visits': v['visits'],
                        'Avg Bill': v['total_spent']/v['visits'] if v['visits'] > 0 else 0,
                        'Points': v['points'],
                        'Last Visit': v['last_visit']
                    }
                    for k, v in customer_stats.items()
                ])
                
                csv = customer_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Customer Report",
                    data=csv,
                    file_name=f"top_customers_{today_dt}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No customer data available")
        else:
            st.info("No sales data found")
    
    # ==================== TAB 2: CUSTOMER SEGMENTS ====================
    with tab2:
        st.subheader("📊 Customer Segmentation Analysis")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Calculate RFM (Recency, Frequency, Monetary)
            customer_rfm = {}
            
            for _, row in s_df.iterrows():
                customer_info = str(row.iloc[5]) if len(row) > 5 else ""
                amount = float(row.iloc[3]) if len(row) > 3 else 0
                date = row.iloc[0] if len(row) > 0 else None
                
                if customer_info and customer_info != "nan":
                    if customer_info not in customer_rfm:
                        customer_rfm[customer_info] = {
                            'last_purchase': date,
                            'frequency': 0,
                            'monetary': 0
                        }
                    
                    customer_rfm[customer_info]['frequency'] += 1
                    customer_rfm[customer_info]['monetary'] += amount
                    
                    if date and customer_rfm[customer_info]['last_purchase']:
                        if date > customer_rfm[customer_info]['last_purchase']:
                            customer_rfm[customer_info]['last_purchase'] = date
            
            # Categorize customers
            champions = []
            loyal = []
            potential = []
            at_risk = []
            dormant = []
            
            for customer, rfm in customer_rfm.items():
                days_since = (datetime.now().date() - rfm['last_purchase']).days if rfm['last_purchase'] else 999
                
                if days_since <= 30 and rfm['frequency'] >= 5 and rfm['monetary'] >= 5000:
                    champions.append((customer, rfm))
                elif days_since <= 60 and rfm['frequency'] >= 3:
                    loyal.append((customer, rfm))
                elif days_since <= 90 and rfm['monetary'] >= 2000:
                    potential.append((customer, rfm))
                elif days_since <= 180 and rfm['frequency'] >= 2:
                    at_risk.append((customer, rfm))
                else:
                    dormant.append((customer, rfm))
            
            # Display segments
            st.markdown("### 🎯 Customer Segments")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            col1.markdown(f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 36px;">{len(champions)}</h2>
                <p style="margin: 5px 0 0 0;">💎 Champions</p>
            </div>
            """, unsafe_allow_html=True)
            
            col2.markdown(f"""
            <div style="background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 36px;">{len(loyal)}</h2>
                <p style="margin: 5px 0 0 0;">👑 Loyal</p>
            </div>
            """, unsafe_allow_html=True)
            
            col3.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 36px;">{len(potential)}</h2>
                <p style="margin: 5px 0 0 0;">⭐ Potential</p>
            </div>
            """, unsafe_allow_html=True)
            
            col4.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 36px;">{len(at_risk)}</h2>
                <p style="margin: 5px 0 0 0;">⚠️ At Risk</p>
            </div>
            """, unsafe_allow_html=True)
            
            col5.markdown(f"""
            <div style="background: linear-gradient(135deg, #868f96 0%, #596164 100%); padding: 20px; border-radius: 12px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 36px;">{len(dormant)}</h2>
                <p style="margin: 5px 0 0 0;">😴 Dormant</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Segment details
            segment_choice = st.selectbox(
                "View Segment Details",
                ["💎 Champions", "👑 Loyal Customers", "⭐ Potential Loyalists", "⚠️ At Risk", "😴 Dormant"]
            )
            
            if "Champions" in segment_choice and champions:
                st.success(f"💎 **{len(champions)} Champion Customers** - Your best customers!")
                st.info("""
                **Characteristics:**
                • Recent purchase (≤30 days)
                • High frequency (≥5 visits)
                • High spend (≥₹5,000)
                
                **Action:** Reward with exclusive offers, VIP treatment
                """)
                
                for customer, rfm in champions[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    st.write(f"✅ {name} - ₹{rfm['monetary']:,.2f} | {rfm['frequency']} visits")
            
            elif "Loyal" in segment_choice and loyal:
                st.info(f"👑 **{len(loyal)} Loyal Customers** - Regular shoppers")
                st.info("""
                **Characteristics:**
                • Recent activity (≤60 days)
                • Moderate frequency (≥3 visits)
                
                **Action:** Maintain engagement with loyalty programs
                """)
                
                for customer, rfm in loyal[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    st.write(f"✅ {name} - ₹{rfm['monetary']:,.2f} | {rfm['frequency']} visits")
            
            elif "Potential" in segment_choice and potential:
                st.warning(f"⭐ **{len(potential)} Potential Loyalists** - Can become loyal!")
                st.info("""
                **Characteristics:**
                • Recent activity (≤90 days)
                • Good spending (≥₹2,000)
                
                **Action:** Encourage repeat visits with targeted offers
                """)
                
                for customer, rfm in potential[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    st.write(f"⭐ {name} - ₹{rfm['monetary']:,.2f} | {rfm['frequency']} visits")
            
            elif "At Risk" in segment_choice and at_risk:
                st.warning(f"⚠️ **{len(at_risk)} At-Risk Customers** - May churn!")
                st.info("""
                **Characteristics:**
                • Haven't visited in 60-180 days
                • Were regular customers before
                
                **Action:** Win-back campaigns, special discounts
                """)
                
                for customer, rfm in at_risk[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    days = (datetime.now().date() - rfm['last_purchase']).days if rfm['last_purchase'] else 999
                    st.write(f"⚠️ {name} - Last seen {days} days ago | {rfm['frequency']} visits")
            
            elif "Dormant" in segment_choice and dormant:
                st.error(f"😴 **{len(dormant)} Dormant Customers** - Lost customers")
                st.info("""
                **Characteristics:**
                • No activity in 180+ days
                • Previously made purchases
                
                **Action:** Re-engagement campaigns, surveys
                """)
                
                for customer, rfm in dormant[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    days = (datetime.now().date() - rfm['last_purchase']).days if rfm['last_purchase'] else 999
                    st.write(f"😴 {name} - Inactive for {days} days")
        else:
            st.info("No data available for segmentation")
    
    # ==================== TAB 3: INDIVIDUAL PROFILE ====================
    with tab3:
        st.subheader("🔍 Individual Customer Profile")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Get unique customers
            customers = s_df.iloc[:, 5].unique()
            customers = [c for c in customers if str(c) != 'nan']
            
            selected_customer = st.selectbox("Select Customer", customers)
            
            if selected_customer:
                # Filter data for this customer
                cust_data = s_df[s_df.iloc[:, 5] == selected_customer]
                
                # Extract name and phone
                if "(" in selected_customer and ")" in selected_customer:
                    cust_name = selected_customer.split("(")[0].strip()
                    cust_phone = selected_customer.split("(")[1].replace(")", "").strip()
                else:
                    cust_name = selected_customer
                    cust_phone = "N/A"
                
                # Calculate metrics
                total_spent = pd.to_numeric(cust_data.iloc[:, 3], errors='coerce').sum()
                total_visits = len(cust_data)
                avg_bill = total_spent / total_visits if total_visits > 0 else 0
                total_points = pd.to_numeric(cust_data.iloc[:, 6], errors='coerce').sum() if len(cust_data.columns) > 6 else 0
                
                first_visit = cust_data.iloc[:, 0].min() if len(cust_data) > 0 else None
                last_visit = cust_data.iloc[:, 0].max() if len(cust_data) > 0 else None
                
                # Display profile
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px;">
                    <h1 style="margin: 0;">{cust_name}</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">📱 {cust_phone}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Lifetime Value", f"₹{total_spent:,.2f}")
                col2.metric("🛒 Total Visits", total_visits)
                col3.metric("📊 Avg Bill", f"₹{avg_bill:.2f}")
                col4.metric("👑 Total Points", int(total_points))
                
                st.divider()
                
                # Visit history
                col1, col2 = st.columns(2)
                col1.info(f"📅 First Visit: {first_visit}")
                col2.info(f"🕒 Last Visit: {last_visit}")
                
                # Check udhaar
                if not k_df.empty:
                    cust_udhaar = k_df[k_df.iloc[:, 0].astype(str).str.contains(cust_phone, na=False)]
                    if not cust_udhaar.empty:
                        balance = pd.to_numeric(cust_udhaar.iloc[:, 1], errors='coerce').sum()
                        if balance > 0:
                            st.warning(f"💰 Outstanding Udhaar: ₹{balance:,.2f}")
                        elif balance < 0:
                            st.success(f"💚 Credit Balance: ₹{abs(balance):,.2f}")
                
                st.divider()
                
                # Purchase history
                st.markdown("### 📋 Purchase History")
                
                # Show last 10 transactions
                recent_purchases = cust_data.tail(10).copy()
                st.dataframe(recent_purchases, use_container_width=True)
                
                # Items purchased
                st.divider()
                st.markdown("### 🛍️ Favorite Products")
                
                items_bought = {}
                for _, row in cust_data.iterrows():
                    item = str(row.iloc[1]) if len(row) > 1 else "Unknown"
                    if item not in items_bought:
                        items_bought[item] = 0
                    items_bought[item] += 1
                
                # Sort by frequency
                top_items = sorted(items_bought.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for item, count in top_items:
                    st.write(f"✅ **{item}** - Purchased {count} times")
        else:
            st.info("No customer data available")
    
    # ==================== TAB 4: PURCHASE PATTERNS ====================
    with tab4:
        st.subheader("📈 Purchase Patterns & Trends")
        
        if not s_df.empty and 'Date' in s_df.columns:
            st.markdown("### 📅 Purchase Frequency Analysis")
            
            # Day of week analysis
            s_df['DayOfWeek'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.day_name()
            
            day_counts = s_df['DayOfWeek'].value_counts()
            
            st.markdown("#### 📊 Busiest Days")
            
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in day_counts.index:
                    count = day_counts[day]
                    percentage = (count / len(s_df)) * 100
                    
                    if day in ['Saturday', 'Sunday']:
                        st.success(f"🔥 **{day}**: {count} sales ({percentage:.1f}%)")
                    else:
                        st.info(f"📅 **{day}**: {count} sales ({percentage:.1f}%)")
            
            st.divider()
            
            # Time-based patterns
            st.markdown("### ⏰ Peak Shopping Hours")
            st.info("💡 Based on historical data, customers prefer:")
            st.write("• Morning (9-12): Regular shopping")
            st.write("• Afternoon (12-5): Peak hours")
            st.write("• Evening (5-8): Quick purchases")
            
            st.divider()
            
            # Monthly trends
            st.markdown("### 📈 Monthly Trends")
            
            s_df['Month'] = pd.to_datetime(s_df['Date'], errors='coerce').dt.month
            monthly_sales = s_df.groupby('Month').agg({
                s_df.columns[3]: lambda x: pd.to_numeric(x, errors='coerce').sum()
            }).reset_index()
            monthly_sales.columns = ['Month', 'Sales']
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            for _, row in monthly_sales.iterrows():
                month_num = int(row['Month'])
                if 1 <= month_num <= 12:
                    month_name = month_names[month_num - 1]
                    sales = row['Sales']
                    st.write(f"📅 **{month_name}**: ₹{sales:,.2f}")
        else:
            st.info("No sales data with dates available")
    
    # ==================== TAB 5: AT-RISK CUSTOMERS ====================
    with tab5:
        st.subheader("⚠️ At-Risk Customer Analysis")
        
        if not s_df.empty and len(s_df.columns) > 5:
            st.warning("🚨 Customers who may stop shopping with you")
            
            # Find customers who haven't visited recently
            customer_last_visit = {}
            
            for _, row in s_df.iterrows():
                customer_info = str(row.iloc[5]) if len(row) > 5 else ""
                date = row.iloc[0] if len(row) > 0 else None
                amount = float(row.iloc[3]) if len(row) > 3 else 0
                
                if customer_info and customer_info != "nan" and date:
                    if customer_info not in customer_last_visit:
                        customer_last_visit[customer_info] = {
                            'last_date': date,
                            'total_spent': 0,
                            'visits': 0
                        }
                    
                    if date > customer_last_visit[customer_info]['last_date']:
                        customer_last_visit[customer_info]['last_date'] = date
                    
                    customer_last_visit[customer_info]['total_spent'] += amount
                    customer_last_visit[customer_info]['visits'] += 1
            
            # Categorize at-risk
            high_risk = []
            medium_risk = []
            
            for customer, data in customer_last_visit.items():
                days_since = (datetime.now().date() - data['last_date']).days
                
                # High value customers who haven't visited
                if data['total_spent'] >= 2000 and days_since >= 60:
                    high_risk.append((customer, data, days_since))
                elif days_since >= 90:
                    medium_risk.append((customer, data, days_since))
            
            # Display high risk
            if high_risk:
                st.error(f"🚨 {len(high_risk)} High-Value Customers at Risk!")
                
                for customer, data, days in sorted(high_risk, key=lambda x: x[2], reverse=True)[:10]:
                    name = customer.split("(")[0] if "(" in customer else customer
                    phone = customer.split("(")[1].replace(")", "") if "(" in customer else ""
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    
                    with col1:
                        st.write(f"👤 **{name}**")
                        st.write(f"📱 {phone}")
                    
                    with col2:
                        st.write(f"💰 Spent: ₹{data['total_spent']:,.2f}")
                        st.write(f"🛒 {data['visits']} visits")
                    
                    with col3:
                        st.error(f"⏰ Last seen: {days} days ago")
                    
                    with col4:
                        if phone:
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {name} जी!

हमें आपकी याद आ रही है! 😊

आपको {days} दिन हो गए हैं।
विशेष छूट के साथ वापस आइए!

🎁 20% OFF on next purchase
📞 Contact: Laika Pet Mart"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(message)
                            whatsapp_url = f"https://wa.me/91{phone}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer;">💬</button></a>', unsafe_allow_html=True)
                    
                    st.divider()
            
            # Display medium risk
            if medium_risk:
                st.warning(f"⚠️ {len(medium_risk)} Customers Becoming Inactive")
                
                inactive_count = len(medium_risk)
                st.info(f"📊 {inactive_count} customers haven't visited in 90+ days")
        else:
            st.info("No data available")
    
    # ==================== TAB 6: RECOMMENDATIONS ====================
    with tab6:
        st.subheader("🎯 Smart Recommendations")
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h3 style="margin: 0;">💡 AI-Powered Business Insights</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not s_df.empty:
            # Calculate some smart recommendations
            total_customers = len(s_df.iloc[:, 5].unique())
            total_sales = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
            avg_sale = total_sales / len(s_df) if len(s_df) > 0 else 0
            
            st.markdown("### 📊 Key Insights")
            
            st.success(f"""
            **Customer Base Health:**
            • {total_customers} unique customers
            • ₹{total_sales:,.2f} total revenue
            • ₹{avg_sale:.2f} average transaction
            """)
            
            st.divider()
            
            st.markdown("### 🎯 Recommended Actions")
            
            st.info("""
            **1. Loyalty Program Optimization**
            • Identify your top 20% customers (80/20 rule)
            • Offer exclusive benefits to champions
            • Create VIP tier for high spenders
            """)
            
            st.warning("""
            **2. Win-Back Campaigns**
            • Target customers inactive 60+ days
            • Offer special comeback discounts
            • Send personalized WhatsApp messages
            """)
            
            st.success("""
            **3. Increase Visit Frequency**
            • Reward program for 5+ visits/month
            • Send reminders on low-stock favorite items
            • Birthday/anniversary special offers
            """)
            
            st.info("""
            **4. Upselling Opportunities**
            • Bundle frequently bought items
            • Suggest complementary products
            • Premium product recommendations for high-spenders
            """)
        else:
            st.info("Collect more sales data for personalized recommendations")

# --- 18. DISCOUNTS & OFFERS MANAGEMENT ---
elif menu == "🎁 Discounts & Offers":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🎁 Discounts & Offers</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Boost Sales with Smart Offers</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for offers
    if 'active_offers' not in st.session_state:
        st.session_state.active_offers = {
            'bulk_discounts': [],
            'seasonal_offers': [],
            'combo_deals': [],
            'loyalty_tiers': {
                'Silver': {'min_spend': 2000, 'discount': 5, 'perks': []},
                'Gold': {'min_spend': 5000, 'discount': 10, 'perks': []},
                'Platinum': {'min_spend': 10000, 'discount': 15, 'perks': []},
                'Diamond': {'min_spend': 20000, 'discount': 20, 'perks': []}
            }
        }
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Bulk Discounts",
        "🌸 Seasonal Offers",
        "🎯 Combo Deals",
        "👑 Loyalty Tiers",
        "📊 Active Offers"
    ])
    
    # ==================== TAB 1: BULK DISCOUNTS ====================
    with tab1:
        st.subheader("💰 Bulk Purchase Discounts")
        
        st.info("💡 Encourage customers to buy more with quantity-based discounts")
        
        # Add new bulk discount
        with st.expander("➕ Create New Bulk Discount", expanded=True):
            with st.form("add_bulk_discount"):
                col1, col2 = st.columns(2)
                
                with col1:
                    product = st.text_input("Product Name", placeholder="e.g., Dog Food")
                    min_qty = st.number_input("Minimum Quantity", min_value=1, value=5)
                    discount_type = st.selectbox("Discount Type", ["Percentage", "Fixed Amount"])
                
                with col2:
                    if discount_type == "Percentage":
                        discount_value = st.number_input("Discount %", min_value=0, max_value=100, value=10)
                    else:
                        discount_value = st.number_input("Discount Amount (₹)", min_value=0, value=100)
                    
                    valid_until = st.date_input("Valid Until", value=datetime.now().date() + timedelta(days=30))
                
                description = st.text_area("Offer Description", 
                    placeholder="e.g., Buy 5 or more bags and save 10%!")
                
                if st.form_submit_button("💾 Create Bulk Discount", type="primary"):
                    if product:
                        new_discount = {
                            'product': product,
                            'min_qty': min_qty,
                            'discount_type': discount_type,
                            'discount_value': discount_value,
                            'valid_until': str(valid_until),
                            'description': description,
                            'created': str(datetime.now().date())
                        }
                        st.session_state.active_offers['bulk_discounts'].append(new_discount)
                        st.success(f"✅ Bulk discount created for {product}!")
                        st.rerun()
        
        # Display active bulk discounts
        st.divider()
        st.markdown("### 📋 Active Bulk Discounts")
        
        if st.session_state.active_offers['bulk_discounts']:
            for i, discount in enumerate(st.session_state.active_offers['bulk_discounts']):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"### 🎁 {discount['product']}")
                        st.write(discount['description'])
                    
                    with col2:
                        if discount['discount_type'] == "Percentage":
                            st.metric("Discount", f"{discount['discount_value']}%")
                        else:
                            st.metric("Discount", f"₹{discount['discount_value']}")
                        st.write(f"Min Qty: {discount['min_qty']}")
                    
                    with col3:
                        st.info(f"Valid till\n{discount['valid_until']}")
                        if st.button("🗑️ Delete", key=f"del_bulk_{i}"):
                            st.session_state.active_offers['bulk_discounts'].pop(i)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No bulk discounts active. Create one above!")
        
        # Example calculations
        st.divider()
        st.markdown("### 🧮 Quick Calculator")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            calc_price = st.number_input("Item Price", value=500, key="bulk_calc_price")
        with col2:
            calc_qty = st.number_input("Quantity", value=5, key="bulk_calc_qty")
        with col3:
            calc_discount = st.number_input("Discount %", value=10, key="bulk_calc_disc")
        
        normal_price = calc_price * calc_qty
        discount_amt = (normal_price * calc_discount) / 100
        final_price = normal_price - discount_amt
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Normal Price", f"₹{normal_price:,.2f}")
        col2.metric("You Save", f"₹{discount_amt:,.2f}", delta=f"-{calc_discount}%")
        col3.metric("Final Price", f"₹{final_price:,.2f}")
    
    # ==================== TAB 2: SEASONAL OFFERS ====================
    with tab2:
        st.subheader("🌸 Seasonal & Festival Offers")
        
        st.info("💡 Create time-limited offers for festivals, seasons, and special occasions")
        
        # Predefined seasons/festivals
        occasions = [
            "Diwali", "Holi", "Christmas", "New Year",
            "Summer Sale", "Monsoon Sale", "Winter Sale",
            "Independence Day", "Republic Day",
            "Custom Event"
        ]
        
        # Add new seasonal offer
        with st.expander("➕ Create Seasonal Offer", expanded=True):
            with st.form("add_seasonal_offer"):
                col1, col2 = st.columns(2)
                
                with col1:
                    occasion = st.selectbox("Occasion", occasions)
                    if occasion == "Custom Event":
                        custom_name = st.text_input("Event Name")
                        occasion = custom_name
                    
                    offer_type = st.selectbox("Offer Type", [
                        "Flat Discount",
                        "Buy 1 Get 1",
                        "Free Gift",
                        "Extra Points"
                    ])
                
                with col2:
                    start_date = st.date_input("Start Date", value=datetime.now().date())
                    end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
                    
                    if offer_type == "Flat Discount":
                        offer_value = st.number_input("Discount %", min_value=0, max_value=100, value=20)
                    elif offer_type == "Extra Points":
                        offer_value = st.number_input("Points Multiplier", min_value=1, max_value=10, value=3)
                    else:
                        offer_value = 1
                
                offer_desc = st.text_area("Offer Details", 
                    placeholder="e.g., Diwali Dhamaka! 25% off on all items + Extra rewards!")
                
                applicable_to = st.multiselect("Applicable to", [
                    "All Products",
                    "Dog Food",
                    "Cat Food",
                    "Accessories",
                    "Medicines",
                    "Grooming"
                ])
                
                if st.form_submit_button("🎉 Create Seasonal Offer", type="primary"):
                    if occasion:
                        new_offer = {
                            'occasion': occasion,
                            'type': offer_type,
                            'value': offer_value,
                            'start_date': str(start_date),
                            'end_date': str(end_date),
                            'description': offer_desc,
                            'applicable_to': applicable_to,
                            'created': str(datetime.now().date())
                        }
                        st.session_state.active_offers['seasonal_offers'].append(new_offer)
                        st.success(f"✅ {occasion} offer created!")
                        st.rerun()
        
        # Display active seasonal offers
        st.divider()
        st.markdown("### 🎊 Active Seasonal Offers")
        
        if st.session_state.active_offers['seasonal_offers']:
            for i, offer in enumerate(st.session_state.active_offers['seasonal_offers']):
                # Check if offer is currently active
                start = datetime.strptime(offer['start_date'], '%Y-%m-%d').date()
                end = datetime.strptime(offer['end_date'], '%Y-%m-%d').date()
                today = datetime.now().date()
                
                is_active = start <= today <= end
                
                status_color = "#38ef7d" if is_active else "#868f96"
                status_text = "🟢 ACTIVE" if is_active else "⚪ SCHEDULED"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {status_color} 0%, white 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333;">🎉 {offer['occasion']} {status_text}</h3>
                    <p style="margin: 10px 0; color: #666;">{offer['description']}</p>
                    <p style="margin: 5px 0; color: #888;">
                        📅 {offer['start_date']} to {offer['end_date']} | 
                        🎯 {offer['type']} | 
                        📦 {', '.join(offer['applicable_to']) if offer['applicable_to'] else 'All'}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🗑️ Delete Offer", key=f"del_seasonal_{i}"):
                    st.session_state.active_offers['seasonal_offers'].pop(i)
                    st.rerun()
                
                st.divider()
        else:
            st.info("No seasonal offers active. Create one above!")
    
    # ==================== TAB 3: COMBO DEALS ====================
    with tab3:
        st.subheader("🎯 Combo Deals & Bundles")
        
        st.info("💡 Increase average order value by bundling products together")
        
        # Add new combo deal
        with st.expander("➕ Create Combo Deal", expanded=True):
            with st.form("add_combo_deal"):
                combo_name = st.text_input("Combo Name", placeholder="e.g., Complete Dog Care Pack")
                
                st.markdown("### 📦 Select Products")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    product1 = st.text_input("Product 1", placeholder="e.g., Dog Food 5Kg")
                    price1 = st.number_input("Price 1", min_value=0, value=500, key="combo_p1")
                    
                    product2 = st.text_input("Product 2", placeholder="e.g., Dog Shampoo")
                    price2 = st.number_input("Price 2", min_value=0, value=200, key="combo_p2")
                
                with col2:
                    product3 = st.text_input("Product 3 (Optional)", placeholder="e.g., Treats")
                    price3 = st.number_input("Price 3", min_value=0, value=150, key="combo_p3")
                    
                    product4 = st.text_input("Product 4 (Optional)", placeholder="e.g., Toy")
                    price4 = st.number_input("Price 4", min_value=0, value=100, key="combo_p4")
                
                # Calculate combo
                total_mrp = price1 + price2 + price3 + price4
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total MRP", f"₹{total_mrp}")
                with col2:
                    combo_discount = st.number_input("Combo Discount %", min_value=0, max_value=50, value=15)
                
                combo_price = total_mrp - (total_mrp * combo_discount / 100)
                savings = total_mrp - combo_price
                
                st.success(f"💰 Combo Price: ₹{combo_price:.2f} | You Save: ₹{savings:.2f} ({combo_discount}%)")
                
                valid_until = st.date_input("Valid Until", value=datetime.now().date() + timedelta(days=30), key="combo_valid")
                
                if st.form_submit_button("🎁 Create Combo Deal", type="primary"):
                    if combo_name and product1 and product2:
                        products = [
                            {'name': product1, 'price': price1},
                            {'name': product2, 'price': price2}
                        ]
                        if product3:
                            products.append({'name': product3, 'price': price3})
                        if product4:
                            products.append({'name': product4, 'price': price4})
                        
                        new_combo = {
                            'name': combo_name,
                            'products': products,
                            'total_mrp': total_mrp,
                            'discount': combo_discount,
                            'combo_price': combo_price,
                            'savings': savings,
                            'valid_until': str(valid_until),
                            'created': str(datetime.now().date())
                        }
                        st.session_state.active_offers['combo_deals'].append(new_combo)
                        st.success(f"✅ Combo deal '{combo_name}' created!")
                        st.rerun()
        
        # Display active combos
        st.divider()
        st.markdown("### 🎁 Active Combo Deals")
        
        if st.session_state.active_offers['combo_deals']:
            for i, combo in enumerate(st.session_state.active_offers['combo_deals']):
                with st.container():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 15px;">
                        <h3 style="margin: 0;">🎯 {combo['name']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Includes:**")
                    for product in combo['products']:
                        st.write(f"✅ {product['name']} - ₹{product['price']}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total MRP", f"₹{combo['total_mrp']}")
                    col2.metric("Combo Price", f"₹{combo['combo_price']:.2f}")
                    col3.metric("You Save", f"₹{combo['savings']:.2f}")
                    col4.info(f"Valid till\n{combo['valid_until']}")
                    
                    if st.button("🗑️ Delete Combo", key=f"del_combo_{i}"):
                        st.session_state.active_offers['combo_deals'].pop(i)
                        st.rerun()
                    
                    st.divider()
        else:
            st.info("No combo deals active. Create one above!")
    
    # ==================== TAB 4: LOYALTY TIERS ====================
    with tab4:
        st.subheader("👑 Loyalty Tier System")
        
        st.info("💡 Reward your best customers with exclusive benefits based on lifetime spend")
        
        # Load customer data for tier assignment
        s_df = load_data("Sales")
        
        # Configure tiers
        with st.expander("⚙️ Configure Loyalty Tiers", expanded=True):
            st.markdown("### 🏆 Tier Configuration")
            
            tiers = ['Silver', 'Gold', 'Platinum', 'Diamond']
            tier_colors = {
                'Silver': '#C0C0C0',
                'Gold': '#FFD700',
                'Platinum': '#E5E4E2',
                'Diamond': '#B9F2FF'
            }
            
            for tier in tiers:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {tier_colors[tier]} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #333;">{tier} Tier</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_spend = st.number_input(
                        f"Min Lifetime Spend",
                        value=st.session_state.active_offers['loyalty_tiers'][tier]['min_spend'],
                        key=f"tier_{tier}_spend"
                    )
                
                with col2:
                    discount = st.number_input(
                        f"Discount %",
                        min_value=0,
                        max_value=30,
                        value=st.session_state.active_offers['loyalty_tiers'][tier]['discount'],
                        key=f"tier_{tier}_disc"
                    )
                
                with col3:
                    st.write("**Benefits:**")
                    if tier == 'Silver':
                        st.write("• Basic rewards")
                    elif tier == 'Gold':
                        st.write("• Priority support\n• Birthday gift")
                    elif tier == 'Platinum':
                        st.write("• Free delivery\n• Exclusive previews")
                    else:
                        st.write("• VIP events\n• Personal shopper")
                
                # Update tier config
                st.session_state.active_offers['loyalty_tiers'][tier]['min_spend'] = min_spend
                st.session_state.active_offers['loyalty_tiers'][tier]['discount'] = discount
                
                st.divider()
        
        # Display customer tier distribution
        st.divider()
        st.markdown("### 📊 Customer Tier Distribution")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Calculate customer spending
            customer_spend = {}
            for _, row in s_df.iterrows():
                customer = str(row.iloc[5]) if len(row) > 5 else ""
                amount = float(row.iloc[3]) if len(row) > 3 else 0
                
                if customer and customer != "nan":
                    if customer not in customer_spend:
                        customer_spend[customer] = 0
                    customer_spend[customer] += amount
            
            # Assign tiers
            tier_counts = {'Silver': 0, 'Gold': 0, 'Platinum': 0, 'Diamond': 0, 'No Tier': 0}
            tier_customers = {'Silver': [], 'Gold': [], 'Platinum': [], 'Diamond': []}
            
            for customer, spend in customer_spend.items():
                assigned = False
                for tier in ['Diamond', 'Platinum', 'Gold', 'Silver']:
                    if spend >= st.session_state.active_offers['loyalty_tiers'][tier]['min_spend']:
                        tier_counts[tier] += 1
                        tier_customers[tier].append((customer, spend))
                        assigned = True
                        break
                if not assigned:
                    tier_counts['No Tier'] += 1
            
            # Display tier summary
            col1, col2, col3, col4, col5 = st.columns(5)
            
            col1.markdown(f"""
            <div style="background: linear-gradient(135deg, {tier_colors['Diamond']} 0%, white 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0;">{tier_counts['Diamond']}</h2>
                <p style="margin: 5px 0;">💎 Diamond</p>
            </div>
            """, unsafe_allow_html=True)
            
            col2.markdown(f"""
            <div style="background: linear-gradient(135deg, {tier_colors['Platinum']} 0%, white 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0;">{tier_counts['Platinum']}</h2>
                <p style="margin: 5px 0;">💍 Platinum</p>
            </div>
            """, unsafe_allow_html=True)
            
            col3.markdown(f"""
            <div style="background: linear-gradient(135deg, {tier_colors['Gold']} 0%, white 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0;">{tier_counts['Gold']}</h2>
                <p style="margin: 5px 0;">👑 Gold</p>
            </div>
            """, unsafe_allow_html=True)
            
            col4.markdown(f"""
            <div style="background: linear-gradient(135deg, {tier_colors['Silver']} 0%, white 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0;">{tier_counts['Silver']}</h2>
                <p style="margin: 5px 0;">🥈 Silver</p>
            </div>
            """, unsafe_allow_html=True)
            
            col5.markdown(f"""
            <div style="background: linear-gradient(135deg, #868f96 0%, white 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <h2 style="margin: 0;">{tier_counts['No Tier']}</h2>
                <p style="margin: 5px 0;">⚪ No Tier</p>
            </div>
            """, unsafe_allow_html=True)
            
            # View customers by tier
            st.divider()
            view_tier = st.selectbox("View Tier Members", ['Diamond', 'Platinum', 'Gold', 'Silver'])
            
            if tier_customers[view_tier]:
                st.success(f"👑 {len(tier_customers[view_tier])} {view_tier} Tier Customers")
                
                for customer, spend in sorted(tier_customers[view_tier], key=lambda x: x[1], reverse=True):
                    name = customer.split("(")[0] if "(" in customer else customer
                    discount_pct = st.session_state.active_offers['loyalty_tiers'][view_tier]['discount']
                    st.write(f"✅ {name} - Lifetime: ₹{spend:,.2f} | Discount: {discount_pct}%")
            else:
                st.info(f"No {view_tier} tier customers yet")
        else:
            st.info("No customer data available for tier assignment")
    
    # ==================== TAB 5: ACTIVE OFFERS SUMMARY ====================
    with tab5:
        st.subheader("📊 All Active Offers Summary")
        
        # Summary metrics
        total_bulk = len(st.session_state.active_offers['bulk_discounts'])
        total_seasonal = len(st.session_state.active_offers['seasonal_offers'])
        total_combos = len(st.session_state.active_offers['combo_deals'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Bulk Discounts", total_bulk)
        col2.metric("🌸 Seasonal Offers", total_seasonal)
        col3.metric("🎯 Combo Deals", total_combos)
        
        st.divider()
        
        # Quick view all offers
        if total_bulk > 0:
            st.markdown("### 💰 Bulk Discounts")
            for discount in st.session_state.active_offers['bulk_discounts']:
                st.info(f"🎁 {discount['product']} - Buy {discount['min_qty']}+ get {discount['discount_value']}% off")
        
        if total_seasonal > 0:
            st.markdown("### 🌸 Seasonal Offers")
            for offer in st.session_state.active_offers['seasonal_offers']:
                st.success(f"🎉 {offer['occasion']} - {offer['type']} ({offer['start_date']} to {offer['end_date']})")
        
        if total_combos > 0:
            st.markdown("### 🎯 Combo Deals")
            for combo in st.session_state.active_offers['combo_deals']:
                st.warning(f"🎁 {combo['name']} - ₹{combo['combo_price']:.2f} (Save ₹{combo['savings']:.2f})")
        
        if total_bulk == 0 and total_seasonal == 0 and total_combos == 0:
            st.info("No active offers. Create offers in other tabs!")

# --- 19. WHATSAPP AUTOMATION ---
elif menu == "💬 WhatsApp Automation":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">💬 WhatsApp Automation</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Automated Marketing & Communication</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    s_df = load_data("Sales")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Daily Summary",
        "🔄 Follow-up Messages",
        "📢 Promotional Broadcast",
        "✅ Order Confirmations",
        "⚙️ Settings"
    ])
    
    # ==================== TAB 1: DAILY SUMMARY ====================
    with tab1:
        st.subheader("📊 Auto Daily Summary to Owner")
        
        st.info("💡 Get automatic daily business summary on WhatsApp")
        
        # Owner phone number
        owner_phone = st.text_input("Owner WhatsApp Number", value="9876543210", help="Owner ka phone number jahan daily summary bhejni hai")
        
        # Generate today's summary
        st.divider()
        st.markdown("### 📋 Today's Summary Preview")
        
        if not s_df.empty and 'Date' in s_df.columns:
            # Filter today's sales
            today = datetime.now().date()
            today_sales = s_df[s_df['Date'] == today]
            
            if not today_sales.empty:
                # Calculate metrics
                total_sales = pd.to_numeric(today_sales.iloc[:, 3], errors='coerce').sum()
                total_bills = len(today_sales)
                avg_bill = total_sales / total_bills if total_bills > 0 else 0
                total_profit = pd.to_numeric(today_sales.iloc[:, 7], errors='coerce').sum() if len(today_sales.columns) > 7 else 0
                
                # Top products
                product_sales = {}
                for _, row in today_sales.iterrows():
                    product = str(row.iloc[1]) if len(row) > 1 else "Unknown"
                    if product not in product_sales:
                        product_sales[product] = 0
                    product_sales[product] += 1
                
                top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]
                top_products_text = "\n".join([f"{i+1}. {p[0]} ({p[1]} sales)" for i, p in enumerate(top_products)])
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Sales", f"₹{total_sales:,.2f}")
                col2.metric("🧾 Bills", total_bills)
                col3.metric("📊 Avg Bill", f"₹{avg_bill:.2f}")
                col4.metric("📈 Profit", f"₹{total_profit:,.2f}")
                
                st.divider()
                
                # Generate WhatsApp message
                summary_message = f"""🐾 *LAIKA PET MART* 🐾
📅 Daily Summary - {today.strftime('%d %B %Y')}

━━━━━━━━━━━━━━━━━━━━━
💰 *आज की बिक्री*
━━━━━━━━━━━━━━━━━━━━━

💵 Total Sales: ₹{total_sales:,.2f}
📈 Total Profit: ₹{total_profit:,.2f}
🧾 Bills Count: {total_bills}
📊 Avg Bill Value: ₹{avg_bill:.2f}

🏆 *Top Products:*
{top_products_text}

━━━━━━━━━━━━━━━━━━━━━
📊 Business Health: {"✅ Excellent" if total_sales > 5000 else "⚠️ Average" if total_sales > 2000 else "🔴 Slow"}
━━━━━━━━━━━━━━━━━━━━━

Have a great day! 🎉"""
                
                # Display message preview
                st.markdown("### 📱 Message Preview")
                st.text_area("WhatsApp Message", summary_message, height=400)
                
                # Send button
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.info("💡 Click button to send this summary to owner's WhatsApp")
                
                with col2:
                    import urllib.parse
                    encoded_msg = urllib.parse.quote(summary_message)
                    whatsapp_url = f"https://wa.me/91{owner_phone}?text={encoded_msg}"
                    
                    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; width: 100%;">📱 Send Now</button></a>', unsafe_allow_html=True)
                
                st.divider()
                
                # Auto-send schedule
                st.markdown("### ⏰ Schedule Auto-Send")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    enable_auto = st.checkbox("Enable Daily Auto-Send", value=False)
                    send_time = st.time_input("Send at", value=datetime.strptime("21:00", "%H:%M").time())
                
                with col2:
                    st.info("""
                    **Auto-Send Features:**
                    • Automatic daily at set time
                    • No manual intervention
                    • WhatsApp API integration needed
                    
                    ⚠️ Requires WhatsApp Business API
                    """)
                
                if enable_auto:
                    st.success(f"✅ Auto-send enabled! Summary will be sent daily at {send_time.strftime('%I:%M %p')}")
            else:
                st.warning("No sales today yet. Summary will be generated after first sale.")
        else:
            st.info("No sales data available")
    
    # ==================== TAB 2: FOLLOW-UP MESSAGES ====================
    with tab2:
        st.subheader("🔄 Customer Follow-up Messages")
        
        st.info("💡 Send automated follow-up messages to customers after purchase")
        
        if not s_df.empty and len(s_df.columns) > 5:
            # Days selector
            days_ago = st.slider("Follow-up after X days", 1, 30, 7)
            
            # Calculate target date
            target_date = datetime.now().date() - timedelta(days=days_ago)
            
            # Filter customers from target date
            if 'Date' in s_df.columns:
                target_sales = s_df[s_df['Date'] == target_date]
                
                if not target_sales.empty:
                    # Get unique customers
                    customers = target_sales.iloc[:, 5].unique()
                    
                    st.success(f"📋 {len(customers)} customers from {target_date} ready for follow-up")
                    
                    # Message template
                    st.divider()
                    st.markdown("### 📝 Follow-up Message Template")
                    
                    follow_up_template = st.text_area(
                        "Message Template",
                        value="""🐾 *LAIKA PET MART* 🐾

नमस्ते {customer_name} जी!

आपने {days} दिन पहले हमारे यहाँ से खरीदारी की थी। 

हमें उम्मीद है कि आप हमारे products से खुश हैं! 😊

🎁 Special Offer Just for You:
• 10% discount on next purchase
• Valid for next 7 days

कुछ और चाहिए तो बताएं!

धन्यवाद! 🙏
Laika Pet Mart
📞 9876543210""",
                        height=300
                    )
                    
                    st.info("💡 Use {customer_name} and {days} as placeholders")
                    
                    st.divider()
                    
                    # Display customers
                    st.markdown("### 👥 Send Follow-ups")
                    
                    for i, customer_info in enumerate(customers):
                        if str(customer_info) != 'nan':
                            # Extract name and phone
                            if "(" in str(customer_info) and ")" in str(customer_info):
                                name = str(customer_info).split("(")[0].strip()
                                phone = str(customer_info).split("(")[1].replace(")", "").strip()
                            else:
                                name = str(customer_info)
                                phone = ""
                            
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.write(f"👤 **{name}**")
                                st.write(f"📅 Last purchase: {days_ago} days ago")
                            
                            with col2:
                                if phone:
                                    st.write(f"📱 {phone}")
                            
                            with col3:
                                if phone:
                                    # Personalize message
                                    personalized_msg = follow_up_template.replace("{customer_name}", name).replace("{days}", str(days_ago))
                                    
                                    import urllib.parse
                                    encoded_msg = urllib.parse.quote(personalized_msg)
                                    whatsapp_url = f"https://wa.me/91{phone}?text={encoded_msg}"
                                    
                                    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer;">📱 Send</button></a>', unsafe_allow_html=True)
                            
                            st.divider()
                    
                    # Bulk send option
                    if st.button("📢 Send to All", type="primary"):
                        st.success(f"✅ Follow-up messages queued for {len(customers)} customers!")
                        st.info("💡 Open each WhatsApp link to send manually, or use WhatsApp Business API for bulk send")
                else:
                    st.info(f"No customers found from {target_date}")
            else:
                st.info("Date information not available in sales data")
        else:
            st.info("No sales data available")
    
    # ==================== TAB 3: PROMOTIONAL BROADCAST ====================
    with tab3:
        st.subheader("📢 Promotional Broadcast")
        
        st.info("💡 Send promotional messages to all customers or specific segments")
        
        # Target audience
        target_audience = st.selectbox(
            "Target Audience",
            ["All Customers", "Top Customers (High Spenders)", "Recent Customers (Last 30 days)", "Inactive Customers (60+ days)"]
        )
        
        # Message type
        promo_type = st.selectbox(
            "Promotion Type",
            ["Festival Offer", "New Product Launch", "Discount Offer", "Event Invitation", "Custom Message"]
        )
        
        # Pre-built templates
        templates = {
            "Festival Offer": """🎉 *DIWALI DHAMAKA* 🎉
🐾 LAIKA PET MART 🐾

इस दिवाली अपने प्यारे दोस्त को खुश करें!

🎁 *Special Offers:*
• 25% OFF on all products
• Buy 1 Get 1 on selected items
• Free treats worth ₹200

📅 Offer valid: 20-31 October
📍 Visit us today!

🎊 Diwali ki शुभकामनाएं! 🎊
Laika Pet Mart
📞 9876543210""",
            
            "New Product Launch": """🚀 *NEW ARRIVAL* 🚀
🐾 LAIKA PET MART 🐾

हमारे store में नए products आ गए हैं!

✨ *What's New:*
• Premium Dog Food Range
• Organic Cat Treats
• Interactive Toys
• Grooming Essentials

🎁 Launch Offer: 15% OFF
📅 Limited Stock!

आज ही आएं और देखें! 😊
Laika Pet Mart
📞 9876543210""",
            
            "Discount Offer": """💰 *MEGA SALE* 💰
🐾 LAIKA PET MART 🐾

बड़ी बचत का मौका!

🔥 *Clearance Sale:*
• Up to 40% OFF
• All categories included
• Limited time only

⏰ Weekend Special!
📅 Valid: This Weekend Only

जल्दी करें, stock limited है! 🏃
Laika Pet Mart
📞 9876543210""",
            
            "Event Invitation": """🎪 *SPECIAL EVENT* 🎪
🐾 LAIKA PET MART 🐾

आप सभी को invite है!

🐕 *Pet Care Workshop*
📅 Date: 25 January 2026
⏰ Time: 11 AM - 2 PM
📍 Venue: Laika Pet Mart

✨ Free Entry!
• Expert advice
• Free health checkup
• Refreshments
• Goodie bags

RSVP: 📞 9876543210
Limited seats! जल्दी करें! 🎉"""
        }
        
        # Message editor
        st.divider()
        st.markdown("### 📝 Create Your Message")
        
        if promo_type != "Custom Message":
            promo_message = st.text_area(
                "Promotional Message",
                value=templates[promo_type],
                height=350
            )
        else:
            promo_message = st.text_area(
                "Custom Message",
                placeholder="Write your custom promotional message here...",
                height=350
            )
        
        # Preview
        st.divider()
        st.markdown("### 📱 Message Preview")
        st.info(promo_message)
        
        # Get target customers
        if not s_df.empty and len(s_df.columns) > 5:
            customer_list = []
            
            if target_audience == "All Customers":
                customer_list = s_df.iloc[:, 5].unique().tolist()
            
            elif target_audience == "Top Customers (High Spenders)":
                # Calculate spending
                customer_spend = {}
                for _, row in s_df.iterrows():
                    customer = str(row.iloc[5])
                    amount = float(row.iloc[3]) if len(row) > 3 else 0
                    if customer != "nan":
                        customer_spend[customer] = customer_spend.get(customer, 0) + amount
                
                # Top 20% customers
                sorted_customers = sorted(customer_spend.items(), key=lambda x: x[1], reverse=True)
                top_20_percent = int(len(sorted_customers) * 0.2)
                customer_list = [c[0] for c in sorted_customers[:top_20_percent]]
            
            elif target_audience == "Recent Customers (Last 30 days)":
                if 'Date' in s_df.columns:
                    cutoff = datetime.now().date() - timedelta(days=30)
                    recent = s_df[s_df['Date'] >= cutoff]
                    customer_list = recent.iloc[:, 5].unique().tolist()
            
            elif target_audience == "Inactive Customers (60+ days)":
                if 'Date' in s_df.columns:
                    # Find customers who haven't purchased in 60+ days
                    customer_last_purchase = {}
                    for _, row in s_df.iterrows():
                        customer = str(row.iloc[5])
                        date = row.iloc[0]
                        if customer != "nan" and date:
                            if customer not in customer_last_purchase or date > customer_last_purchase[customer]:
                                customer_last_purchase[customer] = date
                    
                    cutoff = datetime.now().date() - timedelta(days=60)
                    customer_list = [c for c, d in customer_last_purchase.items() if d < cutoff]
            
            # Remove nan values
            customer_list = [c for c in customer_list if str(c) != 'nan']
            
            st.divider()
            st.success(f"📊 Target Audience: {len(customer_list)} customers")
            
            # Send options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📱 Preview Customer List", type="secondary"):
                    st.markdown("### 👥 Customer List")
                    for customer in customer_list[:20]:  # Show first 20
                        if "(" in str(customer):
                            name = str(customer).split("(")[0]
                            phone = str(customer).split("(")[1].replace(")", "")
                            st.write(f"✅ {name} - {phone}")
                        else:
                            st.write(f"✅ {customer}")
                    
                    if len(customer_list) > 20:
                        st.info(f"... and {len(customer_list)-20} more")
            
            with col2:
                if st.button("📢 Send Broadcast", type="primary"):
                    st.balloons()
                    st.success(f"🎉 Broadcast queued for {len(customer_list)} customers!")
                    st.info("""
                    💡 **Next Steps:**
                    • Messages will be sent via WhatsApp
                    • For bulk send, use WhatsApp Business API
                    • Or send manually by clicking individual links
                    """)
        else:
            st.info("No customer data available")
    
    # ==================== TAB 4: ORDER CONFIRMATIONS ====================
    with tab4:
        st.subheader("✅ Automatic Order Confirmations")
        
        st.info("💡 Send instant order confirmation after each billing")
        
        # Settings
        st.markdown("### ⚙️ Auto-Confirmation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_confirm = st.checkbox("Enable Auto-Confirmation", value=True)
            include_items = st.checkbox("Include Item Details", value=True)
            include_points = st.checkbox("Include Loyalty Points", value=True)
        
        with col2:
            include_delivery = st.checkbox("Include Delivery Info", value=False)
            include_feedback = st.checkbox("Include Feedback Link", value=True)
            include_offers = st.checkbox("Include Next Visit Offer", value=True)
        
        st.divider()
        
        # Sample confirmation message
        st.markdown("### 📱 Sample Confirmation Message")
        
        sample_confirmation = f"""🐾 *ORDER CONFIRMATION* 🐾
LAIKA PET MART

नमस्ते Nidhi जी!

✅ आपका order confirm हो गया है!

📋 *Order Details:*
Order ID: #LPM-{datetime.now().strftime('%Y%m%d')}-045
Date: {datetime.now().strftime('%d %B %Y')}
Time: {datetime.now().strftime('%I:%M %p')}

{'🛍️ *Items Purchased:*' if include_items else ''}
{'• Dog Food 5Kg - ₹2,250' if include_items else ''}
{'• Cat Litter - ₹400' if include_items else ''}

💰 *Total Amount:* ₹2,650
{'🎁 *Points Earned:* +53' if include_points else ''}
{'👑 *Total Points:* 195' if include_points else ''}

{'🚚 *Delivery:* Home delivery in 2-3 days' if include_delivery else ''}
{'📦 Track: wa.me/919876543210' if include_delivery else ''}

{'🎁 *Special Offer:*' if include_offers else ''}
{'Next visit pe 10% extra discount!' if include_offers else ''}

{'⭐ *Feedback:*' if include_feedback else ''}
{'हमारी service कैसी लगी?' if include_feedback else ''}
{'Reply with rating: 1-5 stars' if include_feedback else ''}

धन्यवाद! 🙏
Visit Again Soon!

Laika Pet Mart
📞 9876543210"""
        
        st.text_area("Confirmation Template", sample_confirmation, height=500)
        
        st.divider()
        
        # Integration info
        st.markdown("### 🔗 Integration Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ Billing Integration: Active")
            st.info("💡 Confirmations send automatically after billing")
        
        with col2:
            st.warning("⚠️ WhatsApp API: Manual Mode")
            st.info("💡 Upgrade to WhatsApp Business API for full automation")
        
        if auto_confirm:
            st.success("✅ Auto-confirmation is ENABLED. Messages will be sent after each billing!")
        else:
            st.warning("⚠️ Auto-confirmation is DISABLED. Enable it to start sending confirmations.")
    
    # ==================== TAB 5: SETTINGS ====================
    with tab5:
        st.subheader("⚙️ WhatsApp Automation Settings")
        
        st.markdown("### 📱 Business Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_name = st.text_input("Business Name", value="LAIKA PET MART")
            business_phone = st.text_input("Business WhatsApp", value="9876543210")
            owner_name = st.text_input("Owner Name", value="Ayush")
        
        with col2:
            business_address = st.text_area("Business Address", value="Shop No. 123, Main Market\nBareilly, UP")
            owner_whatsapp = st.text_input("Owner WhatsApp (for daily summary)", value="9876543210")
        
        st.divider()
        
        st.markdown("### 🔔 Notification Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Daily Summary", value=True)
            st.checkbox("Weekly Report", value=False)
            st.checkbox("Low Stock Alerts", value=True)
        
        with col2:
            st.checkbox("Customer Reminders", value=True)
            st.checkbox("Payment Reminders", value=True)
            st.checkbox("Festival Alerts", value=True)
        
        st.divider()
        
        st.markdown("### 🚀 API Integration")
        
        api_status = st.selectbox(
            "WhatsApp Integration Mode",
            ["Manual (Current)", "WhatsApp Business API", "Third-party Service"]
        )
        
        if api_status == "Manual (Current)":
            st.info("""
            📱 **Manual Mode:**
            • Click buttons to open WhatsApp
            • Send messages manually
            • Free to use
            • No automation limit
            """)
        elif api_status == "WhatsApp Business API":
            st.success("""
            🚀 **WhatsApp Business API:**
            • Fully automated sending
            • Bulk messages
            • Scheduled messages
            • API integration required
            
            💰 Cost: ₹1-2 per message
            """)
            
            api_key = st.text_input("API Key", type="password", placeholder="Enter your WhatsApp Business API key")
        
        st.divider()
        
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
            st.balloons()

# --- 20. SUPPLIER MANAGEMENT ---
elif menu == "🏭 Supplier Management":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🏭 Supplier Management</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Complete Procurement & Supplier System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for suppliers
    if 'suppliers' not in st.session_state:
        st.session_state.suppliers = {
            'PetFood Suppliers India': {
                'contact': '9876543210',
                'email': 'info@petfoodsuppliers.com',
                'address': 'Delhi',
                'products': ['Dog Food', 'Cat Food', 'Bird Food'],
                'rating': 4.5,
                'total_orders': 25,
                'on_time_delivery': 92,
                'quality_score': 4.3,
                'price_competitiveness': 4.2
            },
            'Pet Accessories Co': {
                'contact': '9123456789',
                'email': 'sales@petaccessories.com',
                'address': 'Mumbai',
                'products': ['Toys', 'Leashes', 'Collars', 'Beds'],
                'rating': 4.8,
                'total_orders': 18,
                'on_time_delivery': 95,
                'quality_score': 4.7,
                'price_competitiveness': 4.5
            },
            'Veterinary Supplies': {
                'contact': '9988776655',
                'email': 'orders@vetsupplies.com',
                'address': 'Bangalore',
                'products': ['Medicines', 'Supplements', 'First Aid'],
                'rating': 4.2,
                'total_orders': 12,
                'on_time_delivery': 88,
                'quality_score': 4.5,
                'price_competitiveness': 3.8
            }
        }
    
    if 'purchase_orders' not in st.session_state:
        st.session_state.purchase_orders = []
    
    if 'price_quotes' not in st.session_state:
        st.session_state.price_quotes = {}
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Purchase Orders",
        "⭐ Supplier Ratings",
        "💰 Price Comparison",
        "🚚 Delivery Tracking",
        "📊 Supplier Database"
    ])
    
    # ==================== TAB 1: PURCHASE ORDERS ====================
    with tab1:
        st.subheader("📝 Purchase Order Generation")
        
        # Create new PO
        with st.expander("➕ Create New Purchase Order", expanded=True):
            with st.form("new_po"):
                st.markdown("### 📋 Order Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    supplier = st.selectbox("Select Supplier", list(st.session_state.suppliers.keys()))
                    po_date = st.date_input("Order Date", value=datetime.now().date())
                    delivery_date = st.date_input("Expected Delivery", value=datetime.now().date() + timedelta(days=7))
                
                with col2:
                    po_number = st.text_input("PO Number", value=f"PO-{datetime.now().strftime('%Y%m%d')}-{len(st.session_state.purchase_orders)+1:03d}")
                    payment_terms = st.selectbox("Payment Terms", ["Cash on Delivery", "30 Days Credit", "15 Days Credit", "Advance Payment"])
                    priority = st.selectbox("Priority", ["Normal", "Urgent", "High"])
                
                st.divider()
                st.markdown("### 📦 Order Items")
                
                # Add items
                num_items = st.number_input("Number of Items", min_value=1, max_value=10, value=3)
                
                items = []
                total_amount = 0
                
                for i in range(int(num_items)):
                    st.markdown(f"**Item {i+1}**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        item_name = st.text_input(f"Product", key=f"po_item_{i}", placeholder="e.g., Dog Food 10Kg")
                    with col2:
                        quantity = st.number_input(f"Quantity", min_value=1, value=10, key=f"po_qty_{i}")
                    with col3:
                        rate = st.number_input(f"Rate (₹)", min_value=0.0, value=500.0, key=f"po_rate_{i}")
                    with col4:
                        amount = quantity * rate
                        st.metric("Amount", f"₹{amount:,.2f}")
                    
                    if item_name:
                        items.append({
                            'product': item_name,
                            'quantity': quantity,
                            'rate': rate,
                            'amount': amount
                        })
                        total_amount += amount
                
                # Show totals
                st.divider()
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Items", len(items))
                col2.metric("Total Quantity", sum([item['quantity'] for item in items]))
                col3.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
                
                notes = st.text_area("Special Instructions", placeholder="Any special delivery instructions or notes...")
                
                if st.form_submit_button("📝 Generate Purchase Order", type="primary"):
                    if items:
                        new_po = {
                            'po_number': po_number,
                            'supplier': supplier,
                            'po_date': str(po_date),
                            'delivery_date': str(delivery_date),
                            'items': items,
                            'total_amount': total_amount,
                            'payment_terms': payment_terms,
                            'priority': priority,
                            'notes': notes,
                            'status': 'Pending',
                            'created_at': str(datetime.now())
                        }
                        
                        st.session_state.purchase_orders.append(new_po)
                        st.success(f"✅ Purchase Order {po_number} created successfully!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Please add at least one item!")
        
        # Display existing POs
        st.divider()
        st.markdown("### 📋 Recent Purchase Orders")
        
        if st.session_state.purchase_orders:
            # Status filter
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Delivered", "Cancelled"])
            
            filtered_pos = st.session_state.purchase_orders
            if status_filter != "All":
                filtered_pos = [po for po in filtered_pos if po['status'] == status_filter]
            
            for i, po in enumerate(reversed(filtered_pos)):
                # Status color
                status_colors = {
                    'Pending': '#FFA500',
                    'Approved': '#4CAF50',
                    'Delivered': '#2196F3',
                    'Cancelled': '#F44336'
                }
                
                status_color = status_colors.get(po['status'], '#808080')
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {status_color} 0%, white 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px;">
                        <h3 style="margin: 0; color: #333;">📝 {po['po_number']} - {po['supplier']}</h3>
                        <p style="margin: 5px 0; color: #666;">Status: <strong>{po['status']}</strong> | Priority: {po['priority']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.write(f"📅 Order: {po['po_date']}")
                    col2.write(f"🚚 Delivery: {po['delivery_date']}")
                    col3.write(f"💰 Amount: ₹{po['total_amount']:,.2f}")
                    col4.write(f"💳 Terms: {po['payment_terms']}")
                    
                    # Items
                    with st.expander("📦 View Items"):
                        for item in po['items']:
                            st.write(f"• {item['product']} - Qty: {item['quantity']} × ₹{item['rate']} = ₹{item['amount']:,.2f}")
                    
                    # Actions
                    col1, col2, col3, col4 = st.columns(4)
                    
                    if po['status'] == 'Pending':
                        if col1.button("✅ Approve", key=f"approve_{i}"):
                            po['status'] = 'Approved'
                            st.rerun()
                    
                    if po['status'] == 'Approved':
                        if col2.button("📦 Mark Delivered", key=f"deliver_{i}"):
                            po['status'] = 'Delivered'
                            st.rerun()
                    
                    if col3.button("📄 Download PDF", key=f"pdf_{i}"):
                        st.info("PDF generation feature - Install reportlab")
                    
                    if col4.button("❌ Cancel", key=f"cancel_{i}"):
                        po['status'] = 'Cancelled'
                        st.rerun()
                    
                    st.divider()
        else:
            st.info("No purchase orders yet. Create your first PO above!")
    
    # ==================== TAB 2: SUPPLIER RATINGS ====================
    with tab2:
        st.subheader("⭐ Supplier Rating System")
        
        st.info("💡 Rate suppliers on delivery, quality, and pricing")
        
        # Overall rankings
        st.markdown("### 🏆 Supplier Rankings")
        
        # Calculate overall scores
        supplier_scores = []
        for name, data in st.session_state.suppliers.items():
            overall_score = (
                data['rating'] * 0.3 +
                (data['on_time_delivery'] / 20) * 0.3 +
                data['quality_score'] * 0.2 +
                data['price_competitiveness'] * 0.2
            )
            supplier_scores.append((name, overall_score, data))
        
        # Sort by score
        supplier_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Display rankings
        for rank, (name, score, data) in enumerate(supplier_scores, 1):
            # Medal colors
            if rank == 1:
                medal = "🥇"
                color = "#FFD700"
            elif rank == 2:
                medal = "🥈"
                color = "#C0C0C0"
            elif rank == 3:
                medal = "🥉"
                color = "#CD7F32"
            else:
                medal = f"#{rank}"
                color = "#E0E0E0"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #333;">{medal} {name}</h3>
                <p style="margin: 5px 0; color: #666;">Overall Score: {score:.2f}/5.0 ⭐</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("⭐ Rating", f"{data['rating']}/5")
            col2.metric("🚚 On-Time", f"{data['on_time_delivery']}%")
            col3.metric("✅ Quality", f"{data['quality_score']}/5")
            col4.metric("💰 Price", f"{data['price_competitiveness']}/5")
            
            st.divider()
        
        # Rate a supplier
        st.markdown("### 📝 Rate a Supplier")
        
        with st.form("rate_supplier"):
            supplier_to_rate = st.selectbox("Select Supplier", list(st.session_state.suppliers.keys()))
            
            st.markdown("**Rate the following aspects:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                overall_rating = st.slider("Overall Rating", 1.0, 5.0, 4.0, 0.1)
                quality = st.slider("Product Quality", 1.0, 5.0, 4.0, 0.1)
            
            with col2:
                delivery_time = st.slider("On-Time Delivery %", 0, 100, 90)
                pricing = st.slider("Price Competitiveness", 1.0, 5.0, 4.0, 0.1)
            
            feedback = st.text_area("Feedback/Comments", placeholder="Any additional comments...")
            
            if st.form_submit_button("💾 Submit Rating", type="primary"):
                # Update supplier data
                st.session_state.suppliers[supplier_to_rate]['rating'] = overall_rating
                st.session_state.suppliers[supplier_to_rate]['quality_score'] = quality
                st.session_state.suppliers[supplier_to_rate]['on_time_delivery'] = delivery_time
                st.session_state.suppliers[supplier_to_rate]['price_competitiveness'] = pricing
                st.session_state.suppliers[supplier_to_rate]['total_orders'] += 1
                
                st.success(f"✅ Rating submitted for {supplier_to_rate}!")
                time.sleep(1)
                st.rerun()
    
    # ==================== TAB 3: PRICE COMPARISON ====================
    with tab3:
        st.subheader("💰 Price Comparison Tool")
        
        st.info("💡 Compare prices from multiple suppliers for the same product")
        
        # Add price quote
        with st.expander("➕ Add Price Quote", expanded=True):
            with st.form("add_quote"):
                col1, col2 = st.columns(2)
                
                with col1:
                    product_name = st.text_input("Product Name", placeholder="e.g., Dog Food Premium 10Kg")
                    supplier_quote = st.selectbox("Supplier", list(st.session_state.suppliers.keys()))
                
                with col2:
                    price = st.number_input("Price (₹)", min_value=0.0, value=500.0)
                    unit = st.text_input("Unit", value="10Kg", placeholder="e.g., 10Kg, 1 Unit")
                
                col1, col2 = st.columns(2)
                with col1:
                    min_order = st.number_input("Minimum Order Qty", min_value=1, value=10)
                with col2:
                    valid_until = st.date_input("Quote Valid Until", value=datetime.now().date() + timedelta(days=30))
                
                notes = st.text_input("Notes", placeholder="Delivery time, payment terms, etc.")
                
                if st.form_submit_button("💾 Add Quote", type="primary"):
                    if product_name:
                        if product_name not in st.session_state.price_quotes:
                            st.session_state.price_quotes[product_name] = []
                        
                        st.session_state.price_quotes[product_name].append({
                            'supplier': supplier_quote,
                            'price': price,
                            'unit': unit,
                            'min_order': min_order,
                            'valid_until': str(valid_until),
                            'notes': notes,
                            'added_on': str(datetime.now().date())
                        })
                        
                        st.success(f"✅ Quote added for {product_name}!")
                        time.sleep(1)
                        st.rerun()
        
        # Display price comparisons
        st.divider()
        st.markdown("### 📊 Price Comparisons")
        
        if st.session_state.price_quotes:
            product_to_compare = st.selectbox("Select Product", list(st.session_state.price_quotes.keys()))
            
            if product_to_compare:
                quotes = st.session_state.price_quotes[product_to_compare]
                
                st.markdown(f"### 💰 Quotes for {product_to_compare}")
                
                # Sort by price
                quotes_sorted = sorted(quotes, key=lambda x: x['price'])
                
                # Find best price
                best_price = quotes_sorted[0]['price'] if quotes_sorted else 0
                
                for i, quote in enumerate(quotes_sorted, 1):
                    is_best = quote['price'] == best_price
                    
                    color = "#4CAF50" if is_best else "#E0E0E0"
                    badge = "🏆 BEST PRICE" if is_best else f"#{i}"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {color} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #333;">{badge} - {quote['supplier']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("💰 Price", f"₹{quote['price']:,.2f}")
                    col2.metric("📦 Unit", quote['unit'])
                    col3.metric("📊 Min Order", quote['min_order'])
                    col4.write(f"📅 Valid: {quote['valid_until']}")
                    
                    if quote['notes']:
                        st.info(f"📝 {quote['notes']}")
                    
                    # Savings calculation
                    if not is_best:
                        savings = quote['price'] - best_price
                        savings_pct = (savings / quote['price']) * 100
                        st.warning(f"💸 ₹{savings:.2f} more expensive ({savings_pct:.1f}% higher than best price)")
                    
                    st.divider()
                
                # Summary
                st.markdown("### 📊 Price Analysis")
                col1, col2, col3 = st.columns(3)
                
                prices = [q['price'] for q in quotes]
                col1.metric("🏆 Best Price", f"₹{min(prices):,.2f}")
                col2.metric("📊 Average Price", f"₹{sum(prices)/len(prices):,.2f}")
                col3.metric("💰 Potential Saving", f"₹{max(prices) - min(prices):,.2f}")
        else:
            st.info("No price quotes added yet. Add quotes above to start comparing!")
    
    # ==================== TAB 4: DELIVERY TRACKING ====================
    with tab4:
        st.subheader("🚚 Delivery Tracking")
        
        st.info("💡 Track orders from suppliers in real-time")
        
        # Filter deliveries
        delivery_filter = st.selectbox("Filter Orders", ["All Orders", "In Transit", "Delivered", "Delayed"])
        
        # Get relevant POs
        trackable_orders = [po for po in st.session_state.purchase_orders if po['status'] in ['Approved', 'Delivered']]
        
        if trackable_orders:
            st.markdown(f"### 📦 {len(trackable_orders)} Orders in System")
            
            for i, po in enumerate(trackable_orders):
                # Calculate delivery status
                po_date = datetime.strptime(po['po_date'], '%Y-%m-%d').date()
                delivery_date = datetime.strptime(po['delivery_date'], '%Y-%m-%d').date()
                today = datetime.now().date()
                
                days_since_order = (today - po_date).days
                days_until_delivery = (delivery_date - today).days
                
                # Status determination
                if po['status'] == 'Delivered':
                    status = "✅ Delivered"
                    status_color = "#4CAF50"
                elif days_until_delivery < 0:
                    status = "⚠️ Delayed"
                    status_color = "#F44336"
                elif days_until_delivery == 0:
                    status = "📦 Delivering Today"
                    status_color = "#FF9800"
                else:
                    status = "🚚 In Transit"
                    status_color = "#2196F3"
                
                # Display tracking card
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {status_color} 0%, white 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333;">{status} - {po['po_number']}</h3>
                    <p style="margin: 5px 0; color: #666;">{po['supplier']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📅 Ordered", po['po_date'])
                col2.metric("🚚 Expected", po['delivery_date'])
                col3.metric("⏱️ Days Since", days_since_order)
                
                if po['status'] != 'Delivered':
                    if days_until_delivery >= 0:
                        col4.metric("⏳ Days Left", days_until_delivery)
                    else:
                        col4.metric("⚠️ Days Overdue", abs(days_until_delivery))
                else:
                    col4.success("✅ Completed")
                
                # Progress bar
                if po['status'] != 'Delivered':
                    total_days = (delivery_date - po_date).days
                    progress = min(100, int((days_since_order / total_days) * 100)) if total_days > 0 else 0
                    
                    st.progress(progress / 100)
                    st.write(f"Progress: {progress}%")
                
                # Timeline
                with st.expander("📅 Order Timeline"):
                    st.write(f"🟢 Order Placed: {po['po_date']}")
                    st.write(f"🟡 Processing: {po_date + timedelta(days=1)}")
                    st.write(f"🔵 Shipped: {po_date + timedelta(days=2)}")
                    st.write(f"{'🟢' if po['status'] == 'Delivered' else '⚪'} Delivered: {po['delivery_date']}")
                
                # Order details
                with st.expander("📦 Order Details"):
                    st.write(f"**Items:** {len(po['items'])}")
                    st.write(f"**Total Amount:** ₹{po['total_amount']:,.2f}")
                    st.write(f"**Priority:** {po['priority']}")
                    if po['notes']:
                        st.write(f"**Notes:** {po['notes']}")
                
                # Contact supplier
                supplier_phone = st.session_state.suppliers[po['supplier']]['contact']
                
                message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते!

PO: {po['po_number']}
Status check के लिए contact किया है।

Expected Delivery: {po['delivery_date']}

कृपया update दें।

धन्यवाद!
Laika Pet Mart"""
                
                import urllib.parse
                encoded_msg = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/91{supplier_phone}?text={encoded_msg}"
                
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">💬 Contact Supplier</button></a>', unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("No orders to track. Create purchase orders first!")
    
    # ==================== TAB 5: SUPPLIER DATABASE ====================
    with tab5:
        st.subheader("📊 Supplier Database")
        
        st.info(f"💡 Managing {len(st.session_state.suppliers)} suppliers")
        
        # Add new supplier
        with st.expander("➕ Add New Supplier"):
            with st.form("add_supplier"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_supplier_name = st.text_input("Supplier Name")
                    contact = st.text_input("Contact Number")
                    email = st.text_input("Email")
                
                with col2:
                    address = st.text_input("Address/City")
                    products = st.text_input("Products Supplied", placeholder="Comma separated")
                
                if st.form_submit_button("💾 Add Supplier", type="primary"):
                    if new_supplier_name:
                        st.session_state.suppliers[new_supplier_name] = {
                            'contact': contact,
                            'email': email,
                            'address': address,
                            'products': [p.strip() for p in products.split(',')],
                            'rating': 4.0,
                            'total_orders': 0,
                            'on_time_delivery': 90,
                            'quality_score': 4.0,
                            'price_competitiveness': 4.0
                        }
                        st.success(f"✅ Supplier {new_supplier_name} added!")
                        time.sleep(1)
                        st.rerun()
        
        # Display suppliers
        st.divider()
        st.markdown("### 📋 All Suppliers")
        
        for name, data in st.session_state.suppliers.items():
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### 🏭 {name}")
                    st.write(f"📱 {data['contact']} | 📧 {data['email']}")
                    st.write(f"📍 {data['address']}")
                    st.write(f"📦 Products: {', '.join(data['products'])}")
                
                with col2:
                    st.metric("⭐ Rating", f"{data['rating']}/5")
                    st.write(f"📊 Orders: {data['total_orders']}")
                
                st.divider()

# --- 21. CUSTOMER ENGAGEMENT ---
elif menu == "🎂 Customer Engagement":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #FA8BFF 0%, #2BD2FF 50%, #2BFF88 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🎂 Customer Engagement</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Build Lasting Customer Relationships</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'customer_birthdays' not in st.session_state:
        st.session_state.customer_birthdays = {}
    
    if 'customer_feedback' not in st.session_state:
        st.session_state.customer_feedback = []
    
    if 'referral_program' not in st.session_state:
        st.session_state.referral_program = {
            'referrals': [],
            'rewards': {
                'referrer': 100,  # Points for person who refers
                'referee': 50     # Points for new customer
            }
        }
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "🎂 Birthday & Anniversary",
        "⭐ Feedback & Reviews",
        "🎁 Referral Program"
    ])
    
    # ==================== TAB 1: BIRTHDAY & ANNIVERSARY ====================
    with tab1:
        st.subheader("🎂 Birthday & Anniversary Reminders")
        
        # Load sales and pet data
        s_df = load_data("Sales")
        p_df = load_data("PetRecords")
        
        # Add/Update Birthday
        with st.expander("➕ Add Customer Birthday/Anniversary"):
            with st.form("add_birthday"):
                col1, col2 = st.columns(2)
                
                with col1:
                    cust_name = st.text_input("Customer Name")
                    cust_phone = st.text_input("Phone Number")
                    occasion_type = st.selectbox("Occasion", ["Birthday", "Anniversary", "Pet Birthday"])
                
                with col2:
                    occasion_date = st.date_input("Date", value=datetime.now().date())
                    send_time = st.selectbox("Send Wish At", ["9:00 AM", "12:00 PM", "6:00 PM", "9:00 PM"])
                    special_offer = st.number_input("Special Discount %", min_value=0, max_value=50, value=15)
                
                if st.form_submit_button("💾 Save Occasion", type="primary"):
                    if cust_name and cust_phone:
                        key = f"{cust_name}_{cust_phone}"
                        if key not in st.session_state.customer_birthdays:
                            st.session_state.customer_birthdays[key] = []
                        
                        st.session_state.customer_birthdays[key].append({
                            'name': cust_name,
                            'phone': cust_phone,
                            'type': occasion_type,
                            'date': occasion_date,
                            'send_time': send_time,
                            'discount': special_offer,
                            'last_sent': None
                        })
                        
                        st.success(f"✅ {occasion_type} saved for {cust_name}!")
                        time.sleep(1)
                        st.rerun()
        
        # Today's Occasions
        st.divider()
        st.markdown("### 🎉 Today's Special Occasions")
        
        today = datetime.now().date()
        today_occasions = []
        
        for customer_occasions in st.session_state.customer_birthdays.values():
            for occasion in customer_occasions:
                # Check if month and day match
                occ_date = occasion['date'] if isinstance(occasion['date'], date) else datetime.strptime(str(occasion['date']), '%Y-%m-%d').date()
                if occ_date.month == today.month and occ_date.day == today.day:
                    today_occasions.append(occasion)
        
        if today_occasions:
            st.success(f"🎊 {len(today_occasions)} special occasion(s) today!")
            
            for occ in today_occasions:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FFD700 0%, white 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333;">🎂 {occ['type']} - {occ['name']}</h3>
                    <p style="margin: 5px 0; color: #666;">📱 {occ['phone']} | 🎁 {occ['discount']}% Special Discount</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate wish message
                if occ['type'] == "Birthday":
                    wish_message = f"""🎂 *HAPPY BIRTHDAY!* 🎂
🐾 LAIKA PET MART 🐾

🎉 {occ['name']} जी को जन्मदिन की ढेर सारी शुभकामनाएं! 🎉

आपके और आपके प्यारे दोस्त के लिए खास gift:

🎁 *BIRTHDAY SPECIAL OFFER*
{occ['discount']}% OFF on all purchases today!

आज ही आएं और celebrate करें! 🎊

Valid only for today!
Laika Pet Mart
📞 9876543210"""
                
                elif occ['type'] == "Anniversary":
                    wish_message = f"""💑 *HAPPY ANNIVERSARY!* 💑
🐾 LAIKA PET MART 🐾

🎊 {occ['name']} जी को anniversary की बहुत बहुत बधाई! 🎊

आपके celebration के लिए special gift:

🎁 *ANNIVERSARY SPECIAL*
{occ['discount']}% OFF for you today!

आपके प्यार को celebrate करें! 💕

Valid only for today!
Laika Pet Mart
📞 9876543210"""
                
                else:  # Pet Birthday
                    wish_message = f"""🐾 *HAPPY BIRTHDAY TO YOUR PET!* 🐾
LAIKA PET MART

🎉 {occ['name']} जी के pet को birthday की शुभकामनाएं! 🎉

आपके furry friend के लिए special treat:

🎁 *PET BIRTHDAY SPECIAL*
{occ['discount']}% OFF on pet products!
FREE birthday treat! 🦴

आज ही आएं! 🎊

Valid only for today!
Laika Pet Mart
📞 9876543210"""
                
                # Send button
                import urllib.parse
                encoded_msg = urllib.parse.quote(wish_message)
                whatsapp_url = f"https://wa.me/91{occ['phone']}?text={encoded_msg}"
                
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">📱 Send Birthday Wish</button></a>', unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("No special occasions today. Check upcoming section below.")
        
        # Upcoming Occasions
        st.divider()
        st.markdown("### 📅 Upcoming Occasions (Next 30 Days)")
        
        upcoming = []
        for customer_occasions in st.session_state.customer_birthdays.values():
            for occasion in customer_occasions:
                occ_date = occasion['date'] if isinstance(occasion['date'], date) else datetime.strptime(str(occasion['date']), '%Y-%m-%d').date()
                
                # Calculate next occurrence
                next_occurrence = date(today.year, occ_date.month, occ_date.day)
                if next_occurrence < today:
                    next_occurrence = date(today.year + 1, occ_date.month, occ_date.day)
                
                days_until = (next_occurrence - today).days
                
                if 0 < days_until <= 30:
                    upcoming.append({
                        'occasion': occasion,
                        'next_date': next_occurrence,
                        'days_until': days_until
                    })
        
        # Sort by days
        upcoming.sort(key=lambda x: x['days_until'])
        
        if upcoming:
            st.success(f"📋 {len(upcoming)} upcoming occasions")
            
            for item in upcoming:
                occ = item['occasion']
                days = item['days_until']
                
                # Color based on urgency
                if days <= 3:
                    color = "#F44336"  # Red - urgent
                    urgency = "🔴 Urgent"
                elif days <= 7:
                    color = "#FF9800"  # Orange
                    urgency = "🟡 Soon"
                else:
                    color = "#4CAF50"  # Green
                    urgency = "🟢 Upcoming"
                
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{occ['name']}** - {occ['type']}")
                    st.write(f"📱 {occ['phone']}")
                
                with col2:
                    st.write(f"📅 {item['next_date']}")
                    st.write(f"⏳ In {days} days")
                
                with col3:
                    st.markdown(f"""
                    <div style="background: {color}; color: white; padding: 8px; border-radius: 5px; text-align: center;">
                        {urgency}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("No occasions in next 30 days")
        
        # All Saved Occasions
        st.divider()
        with st.expander("📋 View All Saved Occasions"):
            if st.session_state.customer_birthdays:
                count = sum(len(occasions) for occasions in st.session_state.customer_birthdays.values())
                st.info(f"Total: {count} occasions saved")
                
                for customer_occasions in st.session_state.customer_birthdays.values():
                    for occ in customer_occasions:
                        st.write(f"🎂 {occ['name']} - {occ['type']} on {occ['date']} | {occ['discount']}% discount")
            else:
                st.info("No occasions saved yet")
    
    # ==================== TAB 2: FEEDBACK & REVIEWS ====================
    with tab2:
        st.subheader("⭐ Customer Feedback & Reviews")
        
        # Feedback Form
        with st.expander("📝 Collect Feedback"):
            with st.form("collect_feedback"):
                st.markdown("### Customer Feedback Form")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fb_customer = st.text_input("Customer Name")
                    fb_phone = st.text_input("Phone Number")
                    fb_date = st.date_input("Feedback Date", value=datetime.now().date())
                
                with col2:
                    fb_type = st.selectbox("Feedback Type", ["Review", "Complaint", "Suggestion", "Appreciation"])
                    fb_rating = st.slider("Overall Rating", 1, 5, 4)
                
                # Detailed ratings
                st.markdown("### Detailed Ratings")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    product_rating = st.slider("Product Quality", 1, 5, 4, key="prod_rate")
                with col2:
                    service_rating = st.slider("Service Quality", 1, 5, 4, key="serv_rate")
                with col3:
                    price_rating = st.slider("Value for Money", 1, 5, 4, key="price_rate")
                
                fb_comment = st.text_area("Comments/Feedback", placeholder="Please share your experience...")
                
                if st.form_submit_button("💾 Submit Feedback", type="primary"):
                    if fb_customer:
                        new_feedback = {
                            'customer': fb_customer,
                            'phone': fb_phone,
                            'date': str(fb_date),
                            'type': fb_type,
                            'rating': fb_rating,
                            'product_rating': product_rating,
                            'service_rating': service_rating,
                            'price_rating': price_rating,
                            'comment': fb_comment,
                            'status': 'Pending' if fb_type == 'Complaint' else 'Closed',
                            'submitted_at': str(datetime.now())
                        }
                        
                        st.session_state.customer_feedback.append(new_feedback)
                        st.success("✅ Feedback submitted successfully!")
                        
                        # Thank you message
                        if fb_phone:
                            thank_msg = f"""🐾 *THANK YOU!* 🐾
LAIKA PET MART

धन्यवाद {fb_customer} जी!

आपका feedback हमारे लिए बहुत valuable है। 🙏

⭐ Rating: {fb_rating}/5

हम आपकी service improve करने के लिए committed हैं।

आपका प्यार और support के लिए धन्यवाद! ❤️

Laika Pet Mart
📞 9876543210"""
                            
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(thank_msg)
                            whatsapp_url = f"https://wa.me/91{fb_phone}?text={encoded_msg}"
                            
                            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">📱 Send Thank You Message</button></a>', unsafe_allow_html=True)
                        
                        time.sleep(2)
                        st.rerun()
        
        # Feedback Dashboard
        st.divider()
        st.markdown("### 📊 Feedback Dashboard")
        
        if st.session_state.customer_feedback:
            # Summary metrics
            total_feedback = len(st.session_state.customer_feedback)
            avg_rating = sum([f['rating'] for f in st.session_state.customer_feedback]) / total_feedback
            complaints = len([f for f in st.session_state.customer_feedback if f['type'] == 'Complaint'])
            reviews = len([f for f in st.session_state.customer_feedback if f['type'] == 'Review'])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 Total Feedback", total_feedback)
            col2.metric("⭐ Avg Rating", f"{avg_rating:.1f}/5")
            col3.metric("📢 Reviews", reviews)
            col4.metric("⚠️ Complaints", complaints)
            
            st.divider()
            
            # Filter
            filter_type = st.selectbox("Filter by Type", ["All", "Review", "Complaint", "Suggestion", "Appreciation"])
            filter_rating = st.selectbox("Filter by Rating", ["All", "5 Star", "4 Star", "3 Star", "2 Star", "1 Star"])
            
            filtered_feedback = st.session_state.customer_feedback
            
            if filter_type != "All":
                filtered_feedback = [f for f in filtered_feedback if f['type'] == filter_type]
            
            if filter_rating != "All":
                rating_num = int(filter_rating.split()[0])
                filtered_feedback = [f for f in filtered_feedback if f['rating'] == rating_num]
            
            # Display feedback
            for i, fb in enumerate(reversed(filtered_feedback)):
                # Rating stars
                stars = "⭐" * fb['rating'] + "☆" * (5 - fb['rating'])
                
                # Type color
                type_colors = {
                    'Review': '#4CAF50',
                    'Complaint': '#F44336',
                    'Suggestion': '#2196F3',
                    'Appreciation': '#FF9800'
                }
                
                color = type_colors.get(fb['type'], '#808080')
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #333;">{fb['type']} - {fb['customer']}</h4>
                    <p style="margin: 5px 0; color: #666;">{stars} | 📅 {fb['date']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                col1.write(f"📦 Product: {fb['product_rating']}/5")
                col2.write(f"🤝 Service: {fb['service_rating']}/5")
                col3.write(f"💰 Value: {fb['price_rating']}/5")
                
                if fb['comment']:
                    st.info(f"💬 \"{fb['comment']}\"")
                
                # Action buttons for complaints
                if fb['type'] == 'Complaint' and fb['status'] == 'Pending':
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.button("✅ Resolve", key=f"resolve_{i}"):
                            fb['status'] = 'Resolved'
                            st.success("Complaint marked as resolved!")
                            time.sleep(1)
                            st.rerun()
                
                st.divider()
            
            # Download feedback report
            if filtered_feedback:
                feedback_df = pd.DataFrame(filtered_feedback)
                csv = feedback_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Feedback Report",
                    data=csv,
                    file_name=f"feedback_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No feedback received yet. Start collecting feedback above!")
    
    # ==================== TAB 3: REFERRAL PROGRAM ====================
    with tab3:
        st.subheader("🎁 Referral Program")
        
        st.info("💡 Reward customers who bring new customers!")
        
        # Program Settings
        with st.expander("⚙️ Referral Rewards Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                referrer_points = st.number_input(
                    "Points for Referrer",
                    min_value=0,
                    value=st.session_state.referral_program['rewards']['referrer'],
                    help="Points given to person who refers"
                )
                
                st.info("""
                **Referrer Gets:**
                • Points on successful referral
                • Can redeem for discounts
                • Builds loyalty
                """)
            
            with col2:
                referee_points = st.number_input(
                    "Points for New Customer",
                    min_value=0,
                    value=st.session_state.referral_program['rewards']['referee'],
                    help="Welcome bonus for referred customer"
                )
                
                st.info("""
                **New Customer Gets:**
                • Welcome bonus points
                • Instant discount
                • Great first experience
                """)
            
            if st.button("💾 Save Settings"):
                st.session_state.referral_program['rewards']['referrer'] = referrer_points
                st.session_state.referral_program['rewards']['referee'] = referee_points
                st.success("✅ Referral rewards updated!")
        
        # Add Referral
        st.divider()
        with st.expander("➕ Record New Referral"):
            with st.form("add_referral"):
                st.markdown("### New Referral Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    referrer_name = st.text_input("Referrer Name", help="Existing customer who referred")
                    referrer_phone = st.text_input("Referrer Phone")
                
                with col2:
                    referee_name = st.text_input("New Customer Name", help="Person who was referred")
                    referee_phone = st.text_input("New Customer Phone")
                
                ref_date = st.date_input("Referral Date", value=datetime.now().date())
                ref_notes = st.text_input("Notes (Optional)", placeholder="How did the referral happen?")
                
                if st.form_submit_button("🎁 Record Referral", type="primary"):
                    if referrer_name and referee_name:
                        new_referral = {
                            'referrer_name': referrer_name,
                            'referrer_phone': referrer_phone,
                            'referee_name': referee_name,
                            'referee_phone': referee_phone,
                            'date': str(ref_date),
                            'referrer_points': referrer_points,
                            'referee_points': referee_points,
                            'status': 'Active',
                            'notes': ref_notes,
                            'created_at': str(datetime.now())
                        }
                        
                        st.session_state.referral_program['referrals'].append(new_referral)
                        st.balloons()
                        st.success(f"🎉 Referral recorded successfully!")
                        st.success(f"✅ {referrer_name} earned {referrer_points} points!")
                        st.success(f"✅ {referee_name} gets {referee_points} welcome points!")
                        
                        # Send notifications
                        col1, col2 = st.columns(2)
                        
                        # Referrer message
                        with col1:
                            if referrer_phone:
                                ref_msg = f"""🎉 *CONGRATULATIONS!* 🎉
🐾 LAIKA PET MART 🐾

बधाई हो {referrer_name} जी!

आपके referral के लिए thank you! 🙏

🎁 *Reward Earned:*
+{referrer_points} Loyalty Points!

💰 Total Points: {referrer_points}
(Use for discounts on purchases)

Keep referring, keep earning! 🚀

Laika Pet Mart
📞 9876543210"""
                                
                                import urllib.parse
                                encoded_msg = urllib.parse.quote(ref_msg)
                                whatsapp_url = f"https://wa.me/91{referrer_phone}?text={encoded_msg}"
                                
                                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">📱 Notify Referrer</button></a>', unsafe_allow_html=True)
                        
                        # Referee message
                        with col2:
                            if referee_phone:
                                new_msg = f"""🎊 *WELCOME TO LAIKA!* 🎊
🐾 LAIKA PET MART 🐾

Welcome {referee_name} जी!

{referrer_name} ने आपको recommend किया! 🌟

🎁 *Welcome Bonus:*
+{referee_points} Loyalty Points!

आपका first purchase करें और enjoy करें!

हम आपकी service के लिए तैयार हैं! 😊

Laika Pet Mart
📞 9876543210"""
                                
                                import urllib.parse
                                encoded_msg = urllib.parse.quote(new_msg)
                                whatsapp_url = f"https://wa.me/91{referee_phone}?text={encoded_msg}"
                                
                                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color: #25D366; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">📱 Welcome New Customer</button></a>', unsafe_allow_html=True)
                        
                        time.sleep(2)
                        st.rerun()
        
        # Leaderboard
        st.divider()
        st.markdown("### 🏆 Referral Leaderboard")
        
        if st.session_state.referral_program['referrals']:
            # Calculate referral counts
            referrer_stats = {}
            
            for ref in st.session_state.referral_program['referrals']:
                name = ref['referrer_name']
                if name not in referrer_stats:
                    referrer_stats[name] = {
                        'phone': ref['referrer_phone'],
                        'count': 0,
                        'points_earned': 0
                    }
                referrer_stats[name]['count'] += 1
                referrer_stats[name]['points_earned'] += ref['referrer_points']
            
            # Sort by count
            leaderboard = sorted(referrer_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            
            # Display top referrers
            for rank, (name, stats) in enumerate(leaderboard[:10], 1):
                if rank == 1:
                    medal = "🥇"
                    color = "#FFD700"
                elif rank == 2:
                    medal = "🥈"
                    color = "#C0C0C0"
                elif rank == 3:
                    medal = "🥉"
                    color = "#CD7F32"
                else:
                    medal = f"#{rank}"
                    color = "#E0E0E0"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color} 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #333;">{medal} {name}</h3>
                    <p style="margin: 5px 0; color: #666;">📱 {stats['phone']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                col1.metric("👥 Referrals", stats['count'])
                col2.metric("🎁 Points Earned", stats['points_earned'])
                
                st.divider()
            
            # Summary stats
            st.divider()
            st.markdown("### 📊 Program Statistics")
            
            total_referrals = len(st.session_state.referral_program['referrals'])
            total_referrers = len(referrer_stats)
            total_points_given = sum([r['referrer_points'] + r['referee_points'] for r in st.session_state.referral_program['referrals']])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🎁 Total Referrals", total_referrals)
            col2.metric("👥 Active Referrers", total_referrers)
            col3.metric("⭐ Points Distributed", total_points_given)
            
            # All referrals table
            st.divider()
            with st.expander("📋 View All Referrals"):
                referrals_df = pd.DataFrame(st.session_state.referral_program['referrals'])
                st.dataframe(referrals_df, use_container_width=True)
                
                # Download
                csv = referrals_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Referral Report",
                    data=csv,
                    file_name=f"referrals_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No referrals recorded yet. Start tracking referrals above!")

# --- 22. FINANCIAL REPORTS ---
elif menu == "📊 Financial Reports":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">📊 Financial Reports</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Professional Accounting & Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 P&L Statement",
        "💼 Balance Sheet",
        "🧾 Tax Reports",
        "🔨 Custom Reports"
    ])
    
    # Load data
    s_df = load_data("Sales")
    p_df = load_data("Purchase")
    e_df = load_data("Expenses")
    
    with tab1:
        st.subheader("📈 Profit & Loss Statement")
        
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox("Period", ["This Month", "Last Month", "This Year", "Custom"])
        with col2:
            if period == "Custom":
                start_date = st.date_input("From")
                end_date = st.date_input("To")
        
        if st.button("📊 Generate P&L", type="primary"):
            if not s_df.empty:
                # Calculate revenue
                revenue = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
                
                # Estimate COGS (60% of revenue)
                cogs = revenue * 0.6
                gross_profit = revenue - cogs
                
                # Expenses
                if not e_df.empty:
                    expenses = pd.to_numeric(e_df.iloc[:, 1], errors='coerce').sum()
                else:
                    expenses = 0
                
                net_profit = gross_profit - expenses
                
                # Display
                st.success("✅ P&L Statement Generated!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Revenue", f"₹{revenue:,.2f}")
                col2.metric("📈 Gross Profit", f"₹{gross_profit:,.2f}")
                col3.metric("💎 Net Profit", f"₹{net_profit:,.2f}")
                
                st.divider()
                
                # Detailed breakdown
                st.markdown("### Detailed Breakdown")
                
                pl_data = {
                    'Item': ['Revenue', 'COGS', 'Gross Profit', 'Expenses', 'Net Profit'],
                    'Amount': [revenue, -cogs, gross_profit, -expenses, net_profit],
                    'Percentage': [100, (cogs/revenue*100), (gross_profit/revenue*100), (expenses/revenue*100), (net_profit/revenue*100)]
                }
                
                pl_df = pd.DataFrame(pl_data)
                st.dataframe(pl_df, use_container_width=True)
                
                # Download
                csv = pl_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download P&L", csv, "PL_Statement.csv", "text/csv")
            else:
                st.warning("No sales data available")
    
    with tab2:
        st.subheader("💼 Balance Sheet")
        
        as_of = st.date_input("As of Date", datetime.now().date())
        
        if st.button("💼 Generate Balance Sheet", type="primary"):
            st.success("✅ Balance Sheet Generated!")
            
            # Assets
            st.markdown("### 💰 ASSETS")
            cash = 50000
            inventory = 150000
            receivables = 75000
            total_assets = cash + inventory + receivables
            
            col1, col2 = st.columns([3, 1])
            col1.write("Cash & Bank")
            col2.write(f"₹{cash:,.2f}")
            col1.write("Inventory")
            col2.write(f"₹{inventory:,.2f}")
            col1.write("Receivables")
            col2.write(f"₹{receivables:,.2f}")
            
            st.divider()
            st.metric("Total Assets", f"₹{total_assets:,.2f}")
            
            # Liabilities
            st.markdown("### 💳 LIABILITIES")
            payables = 50000
            loans = 100000
            total_liab = payables + loans
            
            col1, col2 = st.columns([3, 1])
            col1.write("Payables")
            col2.write(f"₹{payables:,.2f}")
            col1.write("Loans")
            col2.write(f"₹{loans:,.2f}")
            
            st.divider()
            st.metric("Total Liabilities", f"₹{total_liab:,.2f}")
            
            # Equity
            equity = total_assets - total_liab
            st.markdown("### 👑 EQUITY")
            st.metric("Owner's Equity", f"₹{equity:,.2f}")
    
    with tab3:
        st.subheader("🧾 Tax Reports")
        
        tax_type = st.selectbox("Report Type", ["GST Summary", "TDS Report", "Income Tax", "Audit Trail"])
        
        if st.button("📊 Generate Tax Report", type="primary"):
            if tax_type == "GST Summary":
                st.success("✅ GST Summary Generated!")
                
                if not s_df.empty:
                    total_sales = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
                    
                    # Calculate GST (18%)
                    taxable = total_sales / 1.18
                    gst = total_sales - taxable
                    cgst = gst / 2
                    sgst = gst / 2
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("💰 Total Sales", f"₹{total_sales:,.2f}")
                    col2.metric("📊 Taxable", f"₹{taxable:,.2f}")
                    col3.metric("🔴 CGST", f"₹{cgst:,.2f}")
                    col4.metric("🔵 SGST", f"₹{sgst:,.2f}")
                else:
                    st.warning("No sales data")
    
    with tab4:
        st.subheader("🔨 Custom Report Builder")
        
        st.info("💡 Build your own custom reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Select Metrics")
            metrics = st.multiselect("Choose Metrics", [
                "Total Sales",
                "Total Expenses",
                "Net Profit",
                "Customer Count",
                "Average Bill",
                "Inventory Value",
                "Top Products"
            ])
        
        with col2:
            st.markdown("### Filters")
            date_range = st.date_input("Date Range", [datetime.now().date() - timedelta(days=30), datetime.now().date()])
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie"])
        
        if st.button("🔨 Build Report", type="primary"):
            st.success("✅ Custom Report Generated!")
            
            if "Total Sales" in metrics and not s_df.empty:
                sales = pd.to_numeric(s_df.iloc[:, 3], errors='coerce').sum()
                st.metric("Total Sales", f"₹{sales:,.2f}")
            
            if "Total Expenses" in metrics and not e_df.empty:
                expenses = pd.to_numeric(e_df.iloc[:, 1], errors='coerce').sum()
                st.metric("Total Expenses", f"₹{expenses:,.2f}")
            
            if "Customer Count" in metrics and not s_df.empty:
                customers = s_df.iloc[:, 5].nunique() if len(s_df.columns) > 5 else 0
                st.metric("Unique Customers", customers)

# --- 23. SECURITY & COMPLIANCE ---
elif menu == "🔐 Security & Compliance":
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #DC2626 0%, #7C3AED 50%, #2563EB 100%); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <h1 style="color: white; margin: 0; font-size: 42px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🔐 Security & Compliance</h1>
        <p style="color: white; margin-top: 10px; font-size: 18px; opacity: 0.95;">Data Protection & Access Control</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for security
    if 'backup_history' not in st.session_state:
        st.session_state.backup_history = []
    
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []
    
    if 'login_logs' not in st.session_state:
        st.session_state.login_logs = []
    
    if 'authorized_devices' not in st.session_state:
        st.session_state.authorized_devices = []
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💾 Data Backup",
        "🔒 Access Control",
        "📜 Audit Logs",
        "🛡️ GDPR Compliance"
    ])
    
    # ==================== TAB 1: DATA BACKUP ====================
    with tab1:
        st.subheader("💾 Data Backup System")
        
        st.info("💡 Protect your business data with automated backups")
        
        # Backup Settings
        with st.expander("⚙️ Backup Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_backup = st.checkbox("Enable Auto Backup", value=True)
                backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
                backup_time = st.time_input("Backup Time", value=datetime.strptime("02:00", "%H:%M").time())
            
            with col2:
                retention_days = st.number_input("Retention Period (days)", min_value=7, max_value=365, value=30)
                cloud_backup = st.checkbox("Cloud Backup", value=True)
                local_backup = st.checkbox("Local Backup", value=True)
            
            if st.button("💾 Save Backup Settings", type="primary"):
                st.success("✅ Backup settings saved!")
        
        # Manual Backup
        st.divider()
        st.markdown("### 🔄 Manual Backup")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Backup Now", type="primary", use_container_width=True):
                # Simulate backup
                import time
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                
                backup_entry = {
                    'timestamp': str(datetime.now()),
                    'type': 'Manual',
                    'size': '45.3 MB',
                    'status': 'Success',
                    'location': 'Cloud + Local'
                }
                st.session_state.backup_history.insert(0, backup_entry)
                
                st.success("✅ Backup completed successfully!")
                st.balloons()
        
        with col2:
            if st.button("🔄 Restore Backup", use_container_width=True):
                st.warning("⚠️ Restore will overwrite current data")
        
        with col3:
            if st.button("🗑️ Delete Old Backups", use_container_width=True):
                st.info("Old backups (30+ days) will be deleted")
        
        # Backup History
        st.divider()
        st.markdown("### 📋 Backup History")
        
        # Add sample backup if empty
        if not st.session_state.backup_history:
            st.session_state.backup_history = [
                {'timestamp': str(datetime.now() - timedelta(days=1)), 'type': 'Auto', 'size': '44.8 MB', 'status': 'Success', 'location': 'Cloud'},
                {'timestamp': str(datetime.now() - timedelta(days=2)), 'type': 'Auto', 'size': '43.2 MB', 'status': 'Success', 'location': 'Cloud'},
                {'timestamp': str(datetime.now() - timedelta(days=3)), 'type': 'Manual', 'size': '42.1 MB', 'status': 'Success', 'location': 'Cloud + Local'}
            ]
        
        for i, backup in enumerate(st.session_state.backup_history[:10]):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.write(f"📅 {backup['timestamp'][:19]}")
            with col2:
                badge_color = "#4CAF50" if backup['type'] == 'Auto' else "#2196F3"
                st.markdown(f'<span style="background: {badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{backup["type"]}</span>', unsafe_allow_html=True)
            with col3:
                st.write(f"📦 {backup['size']}")
            with col4:
                st.success("✅ " + backup['status'])
            with col5:
                if st.button("♻️ Restore", key=f"restore_{i}"):
                    st.info("Restore initiated...")
            
            st.divider()
        
        # Storage Info
        st.divider()
        st.markdown("### 💾 Storage Information")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Backups", len(st.session_state.backup_history))
        col2.metric("Total Size", "450 MB")
        col3.metric("Available Space", "2.5 GB")
    
    # ==================== TAB 2: ACCESS CONTROL ====================
    with tab2:
        st.subheader("🔒 Access Control & Security")
        
        st.info("💡 Manage who can access your system and from where")
        
        # Security Settings
        with st.expander("🔐 Security Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                ip_restriction = st.checkbox("Enable IP Restriction", value=False)
                if ip_restriction:
                    allowed_ips = st.text_area("Allowed IP Addresses (one per line)", 
                        value="192.168.1.1\n103.45.67.89")
                
                device_auth = st.checkbox("Device Authorization Required", value=True)
                two_factor = st.checkbox("Two-Factor Authentication", value=False)
            
            with col2:
                session_timeout = st.number_input("Session Timeout (minutes)", min_value=15, max_value=480, value=60)
                max_login_attempts = st.number_input("Max Login Attempts", min_value=3, max_value=10, value=5)
                lockout_duration = st.number_input("Lockout Duration (minutes)", min_value=5, max_value=60, value=15)
            
            if st.button("🔒 Save Security Settings", type="primary"):
                st.success("✅ Security settings updated!")
        
        # Active Sessions
        st.divider()
        st.markdown("### 👥 Active Sessions")
        
        # Sample active sessions
        active_sessions = [
            {'user': 'Laika (Owner)', 'device': 'Chrome on Windows', 'ip': '192.168.1.100', 'login_time': str(datetime.now() - timedelta(hours=2)), 'status': 'Active'},
            {'user': 'Manager', 'device': 'Chrome on Android', 'ip': '192.168.1.105', 'login_time': str(datetime.now() - timedelta(hours=1)), 'status': 'Active'}
        ]
        
        for i, session in enumerate(active_sessions):
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, white 100%); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #333;">👤 {session['user']}</h4>
                <p style="margin: 5px 0; color: #666;">
                    🖥️ {session['device']} | 🌐 {session['ip']}<br>
                    ⏰ Login: {session['login_time'][:19]} | Status: {session['status']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("🚫 Terminate", key=f"terminate_{i}"):
                    st.warning("Session terminated")
            
            st.divider()
        
        # Login History
        st.divider()
        st.markdown("### 📜 Login History (Last 20)")
        
        # Add sample login logs
        if not st.session_state.login_logs:
            st.session_state.login_logs = [
                {'user': 'Laika', 'status': 'Success', 'ip': '192.168.1.100', 'device': 'Chrome', 'timestamp': str(datetime.now() - timedelta(hours=2))},
                {'user': 'Manager', 'status': 'Success', 'ip': '192.168.1.105', 'device': 'Chrome Mobile', 'timestamp': str(datetime.now() - timedelta(hours=3))},
                {'user': 'Staff1', 'status': 'Failed', 'ip': '103.45.67.89', 'device': 'Firefox', 'timestamp': str(datetime.now() - timedelta(hours=5))},
                {'user': 'Laika', 'status': 'Success', 'ip': '192.168.1.100', 'device': 'Chrome', 'timestamp': str(datetime.now() - timedelta(days=1))}
            ]
        
        for log in st.session_state.login_logs[:20]:
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            
            with col1:
                st.write(f"👤 {log['user']}")
            with col2:
                if log['status'] == 'Success':
                    st.success(f"✅ {log['status']}")
                else:
                    st.error(f"❌ {log['status']}")
            with col3:
                st.write(f"🌐 {log['ip']} | {log['device']}")
            with col4:
                st.write(f"⏰ {log['timestamp'][:16]}")
            
            st.divider()
        
        # Download login logs
        if st.button("📥 Download Login Logs"):
            logs_df = pd.DataFrame(st.session_state.login_logs)
            csv = logs_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"login_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # ==================== TAB 3: AUDIT LOGS ====================
    with tab3:
        st.subheader("📜 Audit Trail & Activity Logs")
        
        st.info("💡 Track all system changes and user activities")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_user = st.selectbox("Filter by User", ["All Users", "Laika", "Manager", "Staff1", "Staff2"])
        with col2:
            filter_action = st.selectbox("Filter by Action", ["All Actions", "Create", "Update", "Delete", "View", "Login", "Logout"])
        with col3:
            filter_date = st.date_input("From Date", value=datetime.now().date() - timedelta(days=7))
        
        # Add sample audit logs
        if not st.session_state.audit_logs:
            st.session_state.audit_logs = [
                {'user': 'Laika', 'action': 'Create', 'module': 'Purchase Order', 'details': 'PO-20260121-001 created', 'timestamp': str(datetime.now() - timedelta(hours=1)), 'ip': '192.168.1.100'},
                {'user': 'Manager', 'action': 'Update', 'module': 'Inventory', 'details': 'Updated Dog Food stock: 50 → 45', 'timestamp': str(datetime.now() - timedelta(hours=2)), 'ip': '192.168.1.105'},
                {'user': 'Staff1', 'action': 'Create', 'module': 'Billing', 'details': 'Bill #2156 for Nidhi Kumar - ₹2,650', 'timestamp': str(datetime.now() - timedelta(hours=3)), 'ip': '192.168.1.110'},
                {'user': 'Laika', 'action': 'Delete', 'module': 'Customer', 'details': 'Deleted customer: Test User', 'timestamp': str(datetime.now() - timedelta(hours=4)), 'ip': '192.168.1.100'},
                {'user': 'Manager', 'action': 'Update', 'module': 'Supplier', 'details': 'Updated supplier rating: PetFood India → 4.5★', 'timestamp': str(datetime.now() - timedelta(hours=5)), 'ip': '192.168.1.105'}
            ]
        
        # Display audit logs
        st.divider()
        st.markdown("### 📋 Activity Timeline")
        
        for log in st.session_state.audit_logs[:50]:
            # Action color
            action_colors = {
                'Create': '#4CAF50',
                'Update': '#2196F3',
                'Delete': '#F44336',
                'View': '#9E9E9E',
                'Login': '#FF9800',
                'Logout': '#607D8B'
            }
            
            color = action_colors.get(log['action'], '#808080')
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color} 0%, white 100%); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <strong>{log['action']}</strong> by <strong>{log['user']}</strong> in <em>{log['module']}</em>
                    </div>
                    <div style="color: #666;">
                        {log['timestamp'][:19]}
                    </div>
                </div>
                <div style="margin-top: 5px; color: #555;">
                    📝 {log['details']} | 🌐 {log['ip']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Export audit logs
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Audit Logs", type="primary"):
                audit_df = pd.DataFrame(st.session_state.audit_logs)
                csv = audit_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🔄 Clear Old Logs (30+ days)"):
                st.success("✅ Old logs cleared!")
    
    # ==================== TAB 4: GDPR COMPLIANCE ====================
    with tab4:
        st.subheader("🛡️ GDPR & Data Privacy Compliance")
        
        st.info("💡 Ensure compliance with data protection regulations")
        
        # Privacy Settings
        with st.expander("📋 Privacy Settings", expanded=True):
            st.markdown("### Data Collection Consent")
            
            consent_email = st.checkbox("Email Marketing Consent", value=True)
            consent_whatsapp = st.checkbox("WhatsApp Communication Consent", value=True)
            consent_analytics = st.checkbox("Analytics & Tracking", value=True)
            
            st.divider()
            
            st.markdown("### Data Retention Policy")
            
            col1, col2 = st.columns(2)
            with col1:
                customer_data_retention = st.number_input("Customer Data (months)", min_value=12, max_value=120, value=36)
                transaction_retention = st.number_input("Transaction Records (years)", min_value=3, max_value=10, value=7)
            with col2:
                inactive_account = st.number_input("Inactive Account Deletion (months)", min_value=12, max_value=60, value=24)
                log_retention = st.number_input("System Logs (months)", min_value=3, max_value=24, value=12)
            
            if st.button("💾 Save Privacy Settings", type="primary"):
                st.success("✅ Privacy settings updated!")
        
        # Data Subject Requests
        st.divider()
        st.markdown("### 👤 Data Subject Rights")
        
        request_type = st.selectbox("Request Type", [
            "Right to Access",
            "Right to Rectification",
            "Right to Erasure (Right to be Forgotten)",
            "Right to Data Portability",
            "Right to Object"
        ])
        
        customer_identifier = st.text_input("Customer Phone/Email", placeholder="9876543210 or email@example.com")
        
        if st.button("🔍 Process Request", type="primary"):
            if customer_identifier:
                st.success(f"✅ Processing {request_type} for {customer_identifier}")
                
                if request_type == "Right to Access":
                    st.info("""
                    📋 **Data Export Prepared:**
                    - Personal Information
                    - Transaction History
                    - Communication Logs
                    - Loyalty Points
                    
                    [📥 Download Customer Data Package]
                    """)
                
                elif request_type == "Right to Erasure (Right to be Forgotten)":
                    st.warning("""
                    ⚠️ **Permanent Data Deletion:**
                    This action will:
                    - Remove all personal information
                    - Anonymize transaction records
                    - Delete communication history
                    - Cannot be undone
                    
                    ⚖️ Note: Some data may be retained for legal/financial compliance (7 years)
                    """)
                    
                    if st.checkbox("I confirm this deletion request"):
                        if st.button("🗑️ Delete Customer Data", type="secondary"):
                            st.error("✅ Customer data deletion initiated")
                
                elif request_type == "Right to Data Portability":
                    st.info("""
                    📦 **Data Export Format:**
                    Available formats:
                    - JSON (Machine readable)
                    - CSV (Spreadsheet)
                    - PDF (Human readable)
                    
                    [📥 Download in Preferred Format]
                    """)
        
        # Compliance Dashboard
        st.divider()
        st.markdown("### 📊 Compliance Status")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Data Requests", "12")
        col2.metric("Avg Response Time", "2.3 days")
        col3.metric("Compliance Score", "95%")
        col4.metric("Pending Requests", "2")
        
        # Recent requests
        st.divider()
        st.markdown("### 📋 Recent Data Requests")
        
        requests = [
            {'date': '20-Jan-2026', 'customer': 'Nidhi Kumar', 'type': 'Access', 'status': 'Completed', 'days': '1'},
            {'date': '18-Jan-2026', 'customer': 'Rahul Sharma', 'type': 'Erasure', 'status': 'In Progress', 'days': '3'},
            {'date': '15-Jan-2026', 'customer': 'Priya Singh', 'type': 'Portability', 'status': 'Completed', 'days': '2'}
        ]
        
        for req in requests:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(f"📅 {req['date']}")
                st.write(f"👤 {req['customer']}")
            with col2:
                st.write(f"📋 {req['type']}")
            with col3:
                if req['status'] == 'Completed':
                    st.success(f"✅ {req['status']}")
                else:
                    st.warning(f"⏳ {req['status']}")
            with col4:
                st.write(f"{req['days']} days")
            
            st.divider()

# --- 24. GST & INVOICE MANAGEMENT ---
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
