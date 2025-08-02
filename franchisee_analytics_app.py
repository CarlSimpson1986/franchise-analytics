def calculate_product_campaign_attribution(transaction_df, marketing_df):
    """Calculate product performance and campaign attribution"""
    attribution_results = {}
    
    if len(marketing_df) == 0 or len(transaction_df) == 0:
        return {
            'has_attribution_data': False,
            'product_performance': pd.DataFrame(),
            'campaign_attribution': pd.DataFrame(),
            'total_attributed_revenue': 0
        }
    
    # Get campaign information
    campaign_col = 'Campaign name' if 'Campaign name' in marketing_df.columns else 'Campaign'
    if campaign_col not in marketing_df.columns:
        marketing_df['Campaign'] = 'General Campaign'
        campaign_col = 'Campaign'
    
    # Product performance analysis
    product_performance = transaction_df.groupby('Item').agg({
        'Amount Inc Tax': ['sum', 'count', 'mean'],
        'Date': ['min', 'max'],
        'Sold To': 'nunique'
    }).round(2)
    
    product_performance.columns = ['Total_Revenue', 'Transactions', 'Avg_Price', 'First_Sale', 'Last_Sale', 'Customers']
    product_performance = product_performance.reset_index()
    
    # Try to match products with campaigns (intelligent matching)
    campaign_attribution = []
    
    for _, campaign_row in marketing_df.iterrows():
        campaign_name = campaign_row[campaign_col]
        campaign_spend = campaign_row.get('Amount', 0)
        
        # Extract campaign dates if available
        campaign_start = None
        campaign_end = None
        
        if 'Reporting starts' in marketing_df.columns:
            try:
                campaign_start = pd.to_datetime(campaign_row['Reporting starts'], errors='coerce')
            except:
                pass
        
        if 'Reporting ends' in marketing_df.columns:
            try:
                campaign_end = pd.to_datetime(campaign_row['Reporting ends'], errors='coerce')
            except:
                pass
        
        # Find matching products based on campaign name
        attributed_revenue = 0
        attributed_transactions = 0
        attributed_products = []
        
        for _, product_row in product_performance.iterrows():
            product_name = product_row['Item']
            
            #import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="MyFitPod Complete Business Analytics",
    page_icon="🏋️",
    layout="wide"
)

st.title("🏋️ MyFitPod Complete Business Analytics")
st.markdown("### Professional Business Intelligence with Marketing ROI Tracking")
st.markdown("---")

# Sidebar for file uploads
st.sidebar.title("📊 Upload Your Data")
st.sidebar.markdown("**Upload your business data for comprehensive analytics**")

# Transaction data upload (required)
st.sidebar.markdown("#### 📈 Transaction Data (Required)")
uploaded_transaction_files = st.sidebar.file_uploader(
    "Upload transaction CSV files",
    type=['csv'],
    accept_multiple_files=True,
    help="Upload your monthly transaction/revenue data",
    key="transactions"
)

# Marketing data upload (optional)
st.sidebar.markdown("#### 📱 Marketing Data (Optional)")
st.sidebar.markdown("*Export from Facebook Ads Manager, Google Ads, etc.*")
uploaded_marketing_files = st.sidebar.file_uploader(
    "Upload marketing spend CSV files",
    type=['csv'],
    accept_multiple_files=True,
    help="Upload your ad spend data for ROI analysis",
    key="marketing"
)

# Marketing CSV format help
with st.sidebar.expander("📋 Marketing CSV Format"):
    st.markdown("""
    **Required columns:**
    - Date (YYYY-MM-DD or DD/MM/YYYY)
    - Amount (spend amount)
    
    **Optional columns:**
    - Campaign (campaign name)
    - Platform (Facebook, Google, etc.)
    
    **Example:**
    ```
    Date,Platform,Campaign,Amount
    2025-07-01,Facebook,Summer,150.50
    2025-07-15,Google,Local,200.00
    ```
    """)

st.sidebar.markdown("---")

# Show upload status
if uploaded_transaction_files:
    st.sidebar.success(f"✅ {len(uploaded_transaction_files)} transaction files uploaded")
    for file in uploaded_transaction_files:
        st.sidebar.write(f"📄 {file.name}")

if uploaded_marketing_files:
    st.sidebar.success(f"📱 {len(uploaded_marketing_files)} marketing files uploaded")
    for file in uploaded_marketing_files:
        st.sidebar.write(f"📄 {file.name}")

def load_and_combine_files(uploaded_files, file_type="transaction"):
    """Load and combine multiple CSV files"""
    combined_df = pd.DataFrame()
    file_info = []
    
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df['Source_File'] = file.name
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            file_info.append({
                'filename': file.name,
                'rows': len(df),
                'type': file_type,
                'status': 'Success'
            })
        except Exception as e:
            file_info.append({
                'filename': file.name,
                'rows': 0,
                'type': file_type,
                'status': f'Error: {str(e)}'
            })
    
    return combined_df, file_info

def process_marketing_data(marketing_df):
    """Process marketing data and standardize format"""
    if len(marketing_df) == 0:
        return marketing_df
    
    # Try to standardize date column
    date_columns = ['Date', 'date', 'DATE', 'Day', 'day']
    date_col = None
    for col in date_columns:
        if col in marketing_df.columns:
            date_col = col
            break
    
    if date_col:
        try:
            marketing_df['Date'] = pd.to_datetime(marketing_df[date_col], errors='coerce', dayfirst=True)
        except:
            pass
    
    # Try to find amount/spend column
    amount_columns = ['Amount', 'amount', 'Spend', 'spend', 'Cost', 'cost', 'Amount Spent', 'Amount spent (GBP)', 'Amount spent (USD)', 'Amount (GBP)', 'Amount (USD)', 'Spent']
    amount_col = None
    for col in amount_columns:
        if col in marketing_df.columns:
            amount_col = col
            break
    
    if amount_col:
        try:
            marketing_df['Amount'] = pd.to_numeric(marketing_df[amount_col], errors='coerce')
        except:
            marketing_df['Amount'] = 0
    else:
        # No amount column found - create a default one
        marketing_df['Amount'] = 0
        st.warning(f"⚠️ No amount/spend column found in marketing data. Expected columns: {amount_columns}")
    
    # Add platform if not present
    if 'Platform' not in marketing_df.columns and 'platform' not in marketing_df.columns:
        marketing_df['Platform'] = 'Unknown'
    
    # Add campaign if not present
    if 'Campaign' not in marketing_df.columns and 'campaign' not in marketing_df.columns:
        marketing_df['Campaign'] = 'General'
    
    return marketing_df

def calculate_business_metrics(df):
    """Calculate key business metrics"""
    total_revenue = df['Amount Inc Tax'].sum()
    total_transactions = len(df)
    unique_customers = df['Sold To'].nunique() if 'Sold To' in df.columns else 0
    
    # Revenue by category
    membership_revenue = df[df['Category'] == 'MEMBERSHIP']['Amount Inc Tax'].sum()
    payg_revenue = df[df['Category'] == 'CREDIT_PACK']['Amount Inc Tax'].sum()
    
    # Calculate percentages
    membership_pct = (membership_revenue / total_revenue * 100) if total_revenue > 0 else 0
    payg_pct = (payg_revenue / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'unique_customers': unique_customers,
        'membership_revenue': membership_revenue,
        'payg_revenue': payg_revenue,
        'membership_pct': membership_pct,
        'payg_pct': payg_pct,
        'avg_transaction': total_revenue / total_transactions if total_transactions > 0 else 0,
        'revenue_per_customer': total_revenue / unique_customers if unique_customers > 0 else 0
    }

def calculate_marketing_metrics(marketing_df, total_revenue):
    """Calculate marketing ROI metrics - FIXED VERSION"""
    # Return safe defaults if no marketing data or no Amount column
    if len(marketing_df) == 0 or 'Amount' not in marketing_df.columns:
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }
    
    # Calculate metrics only if we have valid Amount data
    try:
        total_spend = marketing_df['Amount'].sum()
        roi = (total_revenue / total_spend) if total_spend > 0 else 0
        cost_per_revenue = (total_spend / total_revenue) if total_revenue > 0 else 0
        
        return {
            'total_spend': total_spend,
            'roi': roi,
            'cost_per_revenue': cost_per_revenue,
            'profit_after_ads': total_revenue - total_spend
        }
    except:
        # Fallback to safe defaults if anything goes wrong
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }
    """Calculate promo code performance and attribution"""
    promo_results = {}
    
    # Look for promo code columns in transaction data
    promo_columns = ['Promo Code', 'promo_code', 'Promotion', 'promotion', 'Code', 'code', 'Discount Code']
    promo_col = None
    
    for col in promo_columns:
        if col in transaction_df.columns:
            promo_col = col
            break
    
    if promo_col and len(marketing_df) > 0:
        # Get promo code usage
        promo_usage = transaction_df[transaction_df[promo_col].notna()]
        
        if len(promo_usage) > 0:
            promo_performance = promo_usage.groupby(promo_col).agg({
                'Amount Inc Tax': ['sum', 'count'],
                'Sold To': 'nunique'
            }).round(2)
            
            promo_performance.columns = ['Revenue', 'Transactions', 'Customers']
            promo_performance = promo_performance.reset_index()
            promo_performance.columns = ['Promo_Code', 'Revenue', 'Transactions', 'Customers']
            
            # Try to match promo codes with campaigns
            if 'Campaign name' in marketing_df.columns or 'Campaign' in marketing_df.columns:
                campaign_col = 'Campaign name' if 'Campaign name' in marketing_df.columns else 'Campaign'
                
                # Create campaign mapping (this would need to be enhanced based on naming conventions)
                promo_performance['Estimated_Campaign'] = promo_performance['Promo_Code'].str.upper()
                
                # Calculate ROI per promo code if we can match campaigns
                campaign_spend = marketing_df.groupby(campaign_col)['Amount'].sum().to_dict()
                
                promo_performance['Campaign_Spend'] = 0
                promo_performance['ROI'] = 0
                
                for idx, row in promo_performance.iterrows():
                    # Simple matching - enhance this based on your naming convention
                    for campaign, spend in campaign_spend.items():
                        if any(word in campaign.upper() for word in row['Promo_Code'].upper().split()):
                            promo_performance.at[idx, 'Campaign_Spend'] = spend
                            promo_performance.at[idx, 'ROI'] = row['Revenue'] / spend if spend > 0 else 0
                            break
            
            promo_results = {
                'has_promo_data': True,
                'promo_performance': promo_performance,
                'total_promo_revenue': promo_usage['Amount Inc Tax'].sum(),
                'total_promo_transactions': len(promo_usage),
                'promo_customers': promo_usage['Sold To'].nunique()
            }
    
    if not promo_results:
        promo_results = {
            'has_promo_data': False,
            'promo_performance': pd.DataFrame(),
            'total_promo_revenue': 0,
            'total_promo_transactions': 0,
            'promo_customers': 0
        }
    
    return promo_results
    """Calculate marketing ROI metrics - FIXED VERSION"""
    # Return safe defaults if no marketing data or no Amount column
    if len(marketing_df) == 0 or 'Amount' not in marketing_df.columns:
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }
    
    # Calculate metrics only if we have valid Amount data
    try:
        total_spend = marketing_df['Amount'].sum()
        roi = (total_revenue / total_spend) if total_spend > 0 else 0
        cost_per_revenue = (total_spend / total_revenue) if total_revenue > 0 else 0
        
        return {
            'total_spend': total_spend,
            'roi': roi,
            'cost_per_revenue': cost_per_revenue,
            'profit_after_ads': total_revenue - total_spend
        }
    except:
        # Fallback to safe defaults if anything goes wrong
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }

if uploaded_transaction_files:
    # Load transaction data
    with st.spinner("Loading transaction data..."):
        transaction_df, transaction_file_info = load_and_combine_files(uploaded_transaction_files, "transaction")
    
    # Load marketing data if available
    marketing_df = pd.DataFrame()
    marketing_file_info = []
    if uploaded_marketing_files:
        with st.spinner("Loading marketing data..."):
            marketing_df, marketing_file_info = load_and_combine_files(uploaded_marketing_files, "marketing")
            marketing_df = process_marketing_data(marketing_df)
    
    # Show file loading status
    if len(transaction_file_info) > 0 or len(marketing_file_info) > 0:
        st.markdown("### 📁 File Loading Status")
        all_file_info = transaction_file_info + marketing_file_info
        status_df = pd.DataFrame(all_file_info)
        st.dataframe(status_df, use_container_width=True)
    
    if len(transaction_df) > 0:
        # Process transaction data
        transaction_df['Date'] = pd.to_datetime(transaction_df['Date'], dayfirst=True)
        transaction_df['Month'] = transaction_df['Date'].dt.to_period('M')
        transaction_df['Month_Name'] = transaction_df['Date'].dt.strftime('%B %Y')
        
        # Process marketing data dates if available
        if len(marketing_df) > 0 and 'Date' in marketing_df.columns:
            try:
                marketing_df['Month'] = marketing_df['Date'].dt.to_period('M')
                marketing_df['Month_Name'] = marketing_df['Date'].dt.strftime('%B %Y')
            except:
                pass
        
        # Determine data range
        unique_months = transaction_df['Month'].nunique()
        date_range = f"{transaction_df['Date'].min().strftime('%B %Y')} to {transaction_df['Date'].max().strftime('%B %Y')}" if unique_months > 1 else transaction_df['Date'].dt.strftime('%B %Y').iloc[0]
        
        marketing_status = f" + Marketing data" if len(marketing_df) > 0 else ""
        st.success(f"✅ Loaded {len(transaction_df)} transactions across {unique_months} months: {date_range}{marketing_status}")
        
        # Calculate metrics
        business_metrics = calculate_business_metrics(transaction_df)
        marketing_metrics = calculate_marketing_metrics(marketing_df, business_metrics['total_revenue'])
        promotion_analysis = calculate_promotion_analysis(transaction_df, marketing_df)
        
        # Executive Summary
        st.markdown("## 📊 Executive Summary")
        
        if len(marketing_df) > 0 and marketing_metrics['total_spend'] > 0:
            # With marketing data - 5 columns
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("💰 Total Revenue", f"£{business_metrics['total_revenue']:,.0f}")
            with col2:
                st.metric("📱 Marketing Spend", f"£{marketing_metrics['total_spend']:,.0f}")
            with col3:
                st.metric("🎯 Marketing ROI", f"{marketing_metrics['roi']:.1f}x")
            with col4:
                st.metric("👥 Customers", f"{business_metrics['unique_customers']:,}")
            with col5:
                if unique_months > 1:
                    monthly_avg = business_metrics['total_revenue'] / unique_months
                    st.metric("📅 Monthly Avg Revenue", f"£{monthly_avg:,.0f}")
                else:
                    st.metric("💰 Profit After Ads", f"£{marketing_metrics['profit_after_ads']:,.0f}")
        else:
            # Without marketing data - 4 columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Total Revenue", f"£{business_metrics['total_revenue']:,.0f}")
            with col2:
                st.metric("📈 Transactions", f"{business_metrics['total_transactions']:,}")
            with col3:
                st.metric("👥 Customers", f"{business_metrics['unique_customers']:,}")
            with col4:
                if unique_months > 1:
                    monthly_avg = business_metrics['total_revenue'] / unique_months
                    st.metric("📅 Monthly Average", f"£{monthly_avg:,.0f}")
                else:
                    st.metric("💳 Avg Transaction", f"£{business_metrics['avg_transaction']:.2f}")
        
        st.markdown("---")
        
        # Marketing ROI Analysis (if marketing data available)
        if len(marketing_df) > 0 and marketing_metrics['total_spend'] > 0:
            st.markdown("## 📱 Marketing ROI Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # ROI gauge
                roi_value = marketing_metrics['roi']
                fig_roi = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = roi_value,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Overall Marketing ROI"},
                    gauge = {
                        'axis': {'range': [None, 20]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 3], 'color': "lightgray"},
                            {'range': [3, 5], 'color': "yellow"},
                            {'range': [5, 20], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 5
                        }
                    }
                ))
                fig_roi.update_layout(height=300)
                st.plotly_chart(fig_roi, use_container_width=True)
            
            with col2:
                # Marketing insights
                st.markdown("### 💡 Marketing Insights")
                
                roi_insights = []
                if roi_value > 10:
                    roi_insights.append("🚀 **Excellent ROI** - Marketing is highly profitable")
                elif roi_value > 5:
                    roi_insights.append("✅ **Good ROI** - Marketing is profitable")
                elif roi_value > 3:
                    roi_insights.append("⚠️ **Moderate ROI** - Room for optimization")
                else:
                    roi_insights.append("❌ **Low ROI** - Review marketing strategy")
                
                cost_per_pound = marketing_metrics['cost_per_revenue']
                roi_insights.append(f"💰 **Cost efficiency**: £{cost_per_pound:.2f} spent per £1 revenue")
                
                for insight in roi_insights:
                    st.info(insight)
            
            # Promo Code Performance Analysis
            if promo_results['has_promo_data']:
                st.markdown("### 🎟️ Promo Code Performance")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Promo code metrics
                    st.metric("🎁 Promo Revenue", f"£{promo_results['total_promo_revenue']:,.0f}")
                    st.metric("📊 Promo Transactions", f"{promo_results['total_promo_transactions']:,}")
                    st.metric("👥 Promo Customers", f"{promo_results['promo_customers']:,}")
                    
                    # Attribution percentage
                    attribution_pct = (promo_results['total_promo_revenue'] / business_metrics['total_revenue']) * 100
                    st.metric("🎯 Attributed Revenue", f"{attribution_pct:.1f}%")
                
                with col2:
                    # Promo code performance table
                    if len(promo_results['promo_performance']) > 0:
                        st.markdown("**Performance by Promo Code:**")
                        display_promo = promo_results['promo_performance'].copy()
                        display_promo['Revenue'] = display_promo['Revenue'].apply(lambda x: f"£{x:,.0f}")
                        if 'ROI' in display_promo.columns:
                            display_promo['ROI'] = display_promo['ROI'].apply(lambda x: f"{x:.1f}x" if x > 0 else "N/A")
                        st.dataframe(display_promo, use_container_width=True, hide_index=True)
                
                # Promo vs Non-Promo Analysis
                st.markdown("### 🔍 Attribution Analysis")
                
                non_promo_revenue = business_metrics['total_revenue'] - promo_results['total_promo_revenue']
                non_promo_transactions = business_metrics['total_transactions'] - promo_results['total_promo_transactions']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🎟️ Promo Code Sales:**")
                    st.write(f"Revenue: £{promo_results['total_promo_revenue']:,.0f}")
                    st.write(f"Transactions: {promo_results['total_promo_transactions']:,}")
                    if promo_results['total_promo_transactions'] > 0:
                        avg_promo = promo_results['total_promo_revenue'] / promo_results['total_promo_transactions']
                        st.write(f"Avg Transaction: £{avg_promo:.2f}")
                
                with col2:
                    st.markdown("**🔄 Non-Promo Sales:**")
                    st.write(f"Revenue: £{non_promo_revenue:,.0f}")
                    st.write(f"Transactions: {non_promo_transactions:,}")
                    if non_promo_transactions > 0:
                        avg_non_promo = non_promo_revenue / non_promo_transactions
                        st.write(f"Avg Transaction: £{avg_non_promo:.2f}")
                
                with col3:
                    st.markdown("**📊 Attribution:**")
                    st.write(f"Directly Attributed: {attribution_pct:.1f}%")
                    st.write(f"Organic/Other: {100-attribution_pct:.1f}%")
                    
                    # Attribution insights
                    if attribution_pct > 30:
                        st.success("🎯 Strong attribution tracking")
                    elif attribution_pct > 15:
                        st.info("📈 Good attribution coverage")
                    else:
                        st.warning("⚠️ Low attribution - consider more promo codes")
            
            else:
                st.markdown("### 🎟️ Promo Code Tracking")
                st.info("""
                **💡 No promo code data found in your transactions.**
                
                To track campaign performance:
                1. Add promo codes to your marketing campaigns
                2. Include a 'Promo Code' column in your transaction CSV
                3. Get direct attribution and campaign ROI tracking!
                
                **Example campaigns:**
                - Facebook Ad: "Use code FACEBOOK20 for 20% off"
                - Google Ad: "Use code GOOGLE15 for 15% off"
                - Instagram: "Use code INSTA25 for 25% off"
                """)
        
        
        # Revenue Analysis
        st.markdown("## 💰 Revenue Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Business model breakdown
            revenue_data = pd.DataFrame({
                'Type': ['Membership', 'Pay-as-you-go'],
                'Revenue': [business_metrics['membership_revenue'], business_metrics['payg_revenue']],
                'Percentage': [business_metrics['membership_pct'], business_metrics['payg_pct']]
            })
            
            fig_pie = px.pie(revenue_data, values='Revenue', names='Type',
                            title="Revenue by Business Model")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Top products
            top_products = transaction_df.groupby('Item')['Amount Inc Tax'].sum().nlargest(8)
            fig_products = px.bar(x=top_products.values, y=top_products.index, 
                                orientation='h', title="Top Products by Revenue")
            st.plotly_chart(fig_products, use_container_width=True)
        
        # Business Intelligence Insights
        st.markdown("## 💡 Business Intelligence Insights")
        
        insights = []
        
        # Revenue model insights
        if business_metrics['membership_pct'] > 60:
            insights.append("✅ **Strong subscription focus** - Solid recurring revenue base")
        elif business_metrics['membership_pct'] > 40:
            insights.append("⚖️ **Balanced revenue model** - Good mix of recurring and flexible revenue")
        else:
            insights.append("📈 **Growth opportunity** - Focus on converting PAYG customers to memberships")
        
        # Marketing insights
        if len(marketing_df) > 0 and marketing_metrics['total_spend'] > 0:
            roi_value = marketing_metrics['roi']
            if roi_value > 8:
                insights.append("🚀 **Excellent marketing ROI** - Scale up advertising investment")
            elif roi_value > 5:
                insights.append("✅ **Profitable marketing** - Current strategy is working well")
            elif roi_value > 3:
                insights.append("⚠️ **Optimize marketing** - ROI could be improved")
            else:
                insights.append("❌ **Review marketing strategy** - Low ROI needs attention")
        
        # Performance insights
        if unique_months > 1:
            monthly_avg = business_metrics['total_revenue'] / unique_months
            if monthly_avg >= 6000:
                insights.append("🎯 **Monthly target achieved** - Consistently above £6K")
            else:
                gap = 6000 - monthly_avg
                insights.append(f"📈 **Growth needed** - £{gap:,.0f} more monthly to hit £6K target")
        
        # Customer insights
        if business_metrics['unique_customers'] > 0:
            if business_metrics['revenue_per_customer'] > 50:
                insights.append("💎 **High customer value** - Strong revenue per customer")
            else:
                insights.append("🎯 **Upsell opportunity** - Focus on increasing customer spend")
        
        for insight in insights:
            st.info(insight)
    
    else:
        st.error("❌ No valid transaction data found. Please check your CSV format.")

else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to MyFitPod Complete Business Analytics
    
    ### Upload your data for comprehensive business intelligence:
    
    **📈 Transaction Analytics:**
    - Revenue performance vs £6K monthly target
    - Business model analysis (Membership vs Pay-as-you-go)
    - Customer behavior insights
    - Multi-month trend analysis
    
    **📱 Marketing ROI Tracking:**
    - Marketing spend analysis
    - Return on investment calculation
    - Platform performance comparison
    - Marketing vs revenue correlation
    
    **💡 Intelligent Insights:**
    - Automated business recommendations
    - Growth opportunity identification
    - Performance optimization suggestions
    - Strategic planning support
    
    **📊 Key Features:**
    - **Multi-file upload** - Combine multiple months of data
    - **Marketing integration** - Upload ad spend from any platform
    - **Professional dashboards** - Executive-ready reports
    - **Real-time calculations** - Instant ROI and performance metrics
    
    **👈 Use the sidebar to upload your CSV files and get started!**
    
    ### 📋 Quick Start Guide:
    
    **Step 1:** Upload your transaction CSV files (from your pod system)
    **Step 2:** Optionally upload marketing spend CSV files (from Facebook Ads, Google Ads, etc.)
    **Step 3:** Get comprehensive business intelligence with marketing ROI analysis!
    
    *Transform your raw data into actionable business insights in minutes!*
    """)
