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

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password")
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. CHECK NEW DAY ---
today_dt = datetime.now().date()
if st.session_state.last_check_date != today_dt:
    if st.session_state.last_check_date is not None:
        archive_daily_data()
    st.session_state.last_check_date = today_dt

# --- 4. SIDEBAR MENU WITH BUTTONS ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 20px;'>📋 Main Menu</h2>", unsafe_allow_html=True)

# Initialize selected menu in session state
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "📊 Dashboard"

# Menu items
menu_items = [
    "📊 Dashboard",
    "🧾 Billing", 
    "📦 Purchase",
    "📋 Live Stock",
    "💰 Expenses",
    "🐾 Pet Register",
    "📒 Customer Khata",
    "🏢 Supplier Dues",
    "👑 Royalty Points"
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
    # Clear login AND balance session so it reloads fresh from sheets
    st.session_state.logged_in = False
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
    
    # Calculate 18 Jan 2026 purchase total
    jan18_date = datetime(2026, 1, 18).date()
    i_jan18 = i_df[i_df['Date'] == jan18_date] if not i_df.empty and 'Date' in i_df.columns else pd.DataFrame()
    jan18_pur = 0
    jan18_items_count = 0
    if not i_jan18.empty and len(i_jan18.columns) > 3:
        qty_vals_jan18 = pd.to_numeric(i_jan18.iloc[:, 1].astype(str).str.split().str[0], errors='coerce').fillna(0)
        rate_vals_jan18 = pd.to_numeric(i_jan18.iloc[:, 3], errors='coerce').fillna(0)
        jan18_pur = (qty_vals_jan18 * rate_vals_jan18).sum()
        jan18_items_count = len(i_jan18)
    
    today_exp = pd.to_numeric(e_today.iloc[:, 2], errors='coerce').sum() if not e_today.empty and len(e_today.columns) > 2 else 0
    today_profit = pd.to_numeric(s_today.iloc[:, 7], errors='coerce').sum() if not s_today.empty and len(s_today.columns) > 7 else 0
    
    # Show 18 Jan Purchase Alert (if exists)
    if jan18_pur > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(255,107,107,0.4);">
            <div style="text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 24px;">🚨 18 January 2026 Purchase</h3>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Total Items: {jan18_items_count} | Total Amount: ₹{jan18_pur:,.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show detailed items
        with st.expander("📋 View 18 Jan Purchase Details"):
            st.dataframe(i_jan18, use_container_width=True)
    
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
    
    # Add 18 Jan purchase to monthly total if it's in current month
    if jan18_date.month == curr_m and jan18_date.year == today_dt.year:
        month_pur += jan18_pur
        st.info(f"📌 18 Jan Purchase (₹{jan18_pur:,.2f}) is included in Monthly Purchase Total")
    
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
        # Calculate points for this customer
        if c_ph and not s_df.empty and len(s_df.columns) > 6:
            customer_sales = s_df[s_df.iloc[:, 5].astype(str).str.contains(str(c_ph), na=False)]
            pts_bal = pd.to_numeric(customer_sales.iloc[:, 6], errors='coerce').sum()
        else:
            pts_bal = 0
        
        st.metric("👑 Available Points", int(pts_bal))
    
    pay_m = st.selectbox("Payment Mode", ["Cash", "Online", "Udhaar"])
    
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
        
        st.subheader(f"💰 Total: ₹{total_amt:,.2f}")
        st.info(f"🎁 Points Earned: +{total_pts}")
        
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
            
            message = f"""🐾 *LAIKA PET MART* 🐾
            
नमस्ते {c_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{total_amt:,.2f}
👑 *आपके प्वाइंट्स:* +{total_pts}

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
                            # Create WhatsApp message
                            items_text = "\n".join(bill_data['items'])
                            message = f"""🐾 *LAIKA PET MART* 🐾

नमस्ते {cust_name} जी!

आपकी आज की खरीदारी:
{items_text}

💰 *कुल राशि:* ₹{bill_data['total']:,.2f}
👑 *आपके प्वाइंट्स:* +{bill_data['points']}

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
        
        # Calculate points per customer
        customer_points = {}
        for _, row in s_df.iterrows():
            customer_info = str(row.iloc[5]) if len(row) > 5 else ""
            points = pd.to_numeric(row.iloc[6], errors='coerce') if len(row) > 6 else 0
            
            if customer_info and customer_info != "nan":
                if customer_info in customer_points:
                    customer_points[customer_info] += points
                else:
                    customer_points[customer_info] = points
        
        # Convert to dataframe
        if customer_points:
            points_df = pd.DataFrame([
                {
                    "Customer": k.split("(")[0] if "(" in k else k,
                    "Phone": k.split("(")[1].replace(")", "") if "(" in k else "N/A",
                    "Total Points": int(v)
                }
                for k, v in customer_points.items()
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
            c1.metric("👥 Total Customers", len(customer_points))
            c2.metric("🎁 Total Points Given", sum(customer_points.values()))
            c3.metric("⭐ Active Customers", len([v for v in customer_points.values() if v > 0]))
            
            st.divider()
            st.subheader("📊 Customer Points Leaderboard")
            
            # Color code the dataframe
            def highlight_points(row):
                if row['Total Points'] >= 100:
                    return ['background-color: #D4EDDA'] * len(row)
                elif row['Total Points'] >= 50:
                    return ['background-color: #FFF3CD'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = points_df.style.apply(highlight_points, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Download option
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
