import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import urllib.parse
import plotly.express as px

# --- 1. SETUP & CONNECTION (Unchanged) ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxE0gzek4xRRBELWXKjyUq78vMjZ0A9tyUvR_hJ3rkOFeI1k1Agn16lD4kPXbCuVQ/exec" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

if 'bill_cart' not in st.session_state: st.session_state.bill_cart = []
if 'pur_cart' not in st.session_state: st.session_state.pur_cart = []

def save_data(sheet_name, data_list):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
        return response.text == "Success"
    except: return False

def delete_row(sheet_name, row_index):
    try:
        response = requests.post(f"{SCRIPT_URL}?sheet={sheet_name}&action=delete&row={row_index + 2}")
        return "Success" in response.text
    except: return False

def load_data(sheet_name):
    try:
        url = f"{SHEET_LINK}{sheet_name}&cache={time.time()}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        elif not df.empty:
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 LAIKA PET MART LOGIN</h1>", unsafe_allow_html=True)
    u = st.text_input("Username").strip(); p = st.text_input("Password", type="password")
    if st.button("LOGIN", use_container_width=True):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. SIDEBAR & LOGOUT ---
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "📒 Customer Khata", "🎖️ Loyalty Club", "⚙️ Admin Settings"])
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

today_dt = datetime.now().date()
curr_m = datetime.now().month
curr_m_name = datetime.now().strftime('%B')

# --- 4. DASHBOARD (FIXED CALCULATION FOR BACKLOG) ---
if menu == "📊 Dashboard":
    st.markdown("<h1 style='text-align: center; color: #FF9800;'>🐾 Welcome to Laika Pet Mart 🐾</h1>", unsafe_allow_html=True)
    s_df = load_data("Sales"); e_df = load_data("Expenses"); b_df = load_data("Balances"); k_df = load_data("CustomerKhata"); i_df = load_data("Inventory"); d_df = load_data("Dues")
    
    # Financial Boxes Calculation
    bc = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Cash"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    bo = pd.to_numeric(b_df[b_df.iloc[:, 0] == "Online"].iloc[:, 1], errors='coerce').sum() if not b_df.empty else 0
    sc = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Cash"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    so = pd.to_numeric(s_df[s_df.iloc[:, 4] == "Online"].iloc[:, 3], errors='coerce').sum() if not s_df.empty else 0
    ec = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Cash"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    eo = pd.to_numeric(e_df[e_df.iloc[:, 3] == "Online"].iloc[:, 2], errors='coerce').sum() if not e_df.empty else 0
    
    # FIX: Ismein se filter hata diya hai taaki Dashboard ka Galla sahi dikhe
    pc = pd.to_numeric(i_df[i_df.iloc[:, 5] == "Cash"].apply(lambda x: pd.to_numeric(x.iloc[1])*pd.to_numeric(x.iloc[3]), axis=1), errors='coerce').sum() if not i_df.empty else 0
    po = pd.to_numeric(i_df[i_df.iloc[:, 5] == "Online"].apply(lambda x: pd.to_numeric(x.iloc[1])*pd.to_numeric(x.iloc[3]), axis=1), errors='coerce').sum() if not i_df.empty else 0
    
    total_u = pd.to_numeric(k_df.iloc[:, 1], errors='coerce').sum() if not k_df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-around;">
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 10px; border-left: 8px solid #D32F2F; width: 24%;">
            <p style="color: #D32F2F; margin: 0;">💵 Galla (Cash)</p> <h2 style="margin: 0;">₹{bc + sc - ec - pc:,.2f}</h2>
        </div>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 8px solid #1976D2; width: 24%;">
            <p style="color: #1976D2; margin: 0;">🏦 Online (Bank)</p> <h2 style="margin: 0;">₹{bo + so - eo - po:,.2f}</h2>
        </div>
        <div style="background-color: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 8px solid #F57C00; width: 24%;">
            <p style="color: #F57C00; margin: 0;">📒 Cust. Udhaar</p> <h2 style="margin: 0;">₹{total_u:,.2f}</h2>
        </div>
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 10px; border-left: 8px solid #388E3C; width: 24%;">
            <p style="color: #388E3C; margin: 0;">💰 Total Net</p> <h2 style="margin: 0;">₹{(bc+sc-ec-pc+bo+so-eo-po):,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def show_metrics(df_s, df_e, df_i, title, p_type="today"):
        # Filter Logic
        m = (df_s['Date'].dt.date == today_dt) if (not df_s.empty and p_type == "today") else (df_s['Date'].dt.month == curr_m if not df_s.empty else False)
        mi = (df_i['Date'].dt.date == today_dt) if (not df_i.empty and p_type == "today") else (df_i['Date'].dt.month == curr_m if not df_i.empty else False)
        me = (df_e['Date'].dt.date == today_dt) if (not df_e.empty and p_type == "today") else (df_e['Date'].dt.month == curr_m if not df_e.empty else False)
        
        ts = pd.to_numeric(df_s[m].iloc[:, 3], errors='coerce').sum() if not df_s.empty else 0
        tp = pd.to_numeric(df_i[mi].apply(lambda x: pd.to_numeric(x.iloc[1])*pd.to_numeric(x.iloc[3]), axis=1), errors='coerce').sum() if not df_i.empty else 0
        te = pd.to_numeric(df_e[me].iloc[:, 2], errors='coerce').sum() if not df_e.empty else 0
        tprof = pd.to_numeric(df_s[m].iloc[:, 7], errors='coerce').sum() if not df_s.empty and len(df_s.columns)>7 else 0
        
        st.subheader(f"📈 {title} Report"); c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sale", f"₹{ts}"); c2.metric("Total Purchase", f"₹{tp}"); c3.metric("Total Expense", f"₹{te}"); c4.metric("Total Profit", f"₹{tprof}")

    show_metrics(s_df, e_df, i_df, f"Daily ({today_dt})", "today")
    st.divider(); show_metrics(s_df, e_df, i_df, f"Monthly ({curr_m_name})", "month")
    
    if not s_df.empty:
        fig = px.line(s_df.groupby(s_df['Date'].dt.date).agg({s_df.columns[3]: 'sum'}).reset_index().tail(7), x='Date', y=s_df.columns[3])
        st.plotly_chart(fig, use_container_width=True)

# --- BAAKI SECTIONS (100% SAME AS BEFORE) ---
# ... (Billing, Purchase, etc. remains word-to-word as you wanted)
