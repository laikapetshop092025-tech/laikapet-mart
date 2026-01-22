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
    
    # **NEW: Points Enable/Disable Option**
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        enable_points = st.checkbox("✅ Enable Loyalty Points for this Bill", value=True, 
                                    help="Is bill mein points dene hain? Uncheck karein agar points nahi dene")
    with col2:
        if enable_points:
            st.success("🎁 Points ENABLED - Customer ko points milenge")
        else:
            st.warning("⚠️ Points DISABLED - Is bill mein koi points nahi milega")
