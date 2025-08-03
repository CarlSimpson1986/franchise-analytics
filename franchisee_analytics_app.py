import streamlit as st
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

# Add Help Guide Section
def show_help_guide():
    """Display help guide for franchisees"""
    with st.expander("📋 **What Do These Numbers Mean? - Franchisee Guide**", expanded=False):
        st.markdown("""
        ### 💰 **Revenue Metrics**
        
        **Total Revenue**: Your total sales across all periods
        - 🟢 **Excellent**: Meeting or exceeding targets consistently
        - 🟡 **Good**: Close to targets, room for improvement  
        - 🔴 **Needs Attention**: Below targets, action required
        
        **Monthly Average Revenue**: Your average monthly sales
        - **Target**: £6,000 per month
        - 🟢 **£6,000+**: Hitting targets consistently
        - 🟡 **£4,800-6,000**: Close to target (80%+)
        - 🔴 **Under £4,800**: Need to boost sales
        
        ### 📱 **Marketing Metrics**
        
        **Marketing ROI**: Return on your advertising spend
        - **Formula**: Revenue ÷ Marketing Spend
        - 🟢 **10x+**: Exceptional - scale up marketing immediately!
        - 🟡 **5-10x**: Good - profitable marketing
        - 🔴 **Under 5x**: Review marketing efficiency
        
        **Marketing Spend**: How much you invested in advertising
        - Track this to understand your investment vs returns
        
        ### 👥 **Customer Metrics**
        
        **Customer LTV** (Lifetime Value): Average total spend per customer
        - 🟢 **£100+**: Excellent customer value
        - 🟡 **£50-100**: Good customer base
        - 🔴 **Under £50**: Focus on retention and upselling
        
        **CAC** (Customer Acquisition Cost): Cost to acquire each new customer
        - 🟢 **£15 or less**: Very efficient acquisition
        - 🟡 **£15-30**: Good efficiency
        - 🔴 **£30+**: Review marketing targeting
        
        **LTV:CAC Ratio**: Customer value vs acquisition cost
        - 🟢 **5:1 or higher**: Excellent - scale marketing!
        - 🟡 **3:1 to 5:1**: Good profitability
        - 🔴 **Under 3:1**: Improve efficiency or reduce CAC
        
        **Payback Period**: How long to recover customer acquisition cost
        - 🟢 **Under 3 months**: Excellent cash flow
        - 🟡 **3-6 months**: Good performance
        - 🔴 **Over 6 months**: Improve customer value or reduce CAC
        
        ### 🎯 **What Should I Do?**
        
        **If you see lots of 🟢**: Scale up what's working! Increase marketing spend.
        
        **If you see 🟡**: Good performance, optimize to reach excellent.
        
        **If you see 🔴**: Priority action needed - review strategy or get support.
        
        ### 📞 **Need Help?**
        Use these insights to:
        - Plan marketing budgets
        - Set monthly targets  
        - Identify best-performing products
        - Make data-driven business decisions
        """)

# Benchmarking functions
def get_performance_indicator(value, benchmarks):
    """Return performance indicator based on benchmarks"""
    if value >= benchmarks['excellent']:
        return "🟢"
    elif value >= benchmarks['good']:
        return "🟡"
    else:
        return "🔴"

def get_marketing_roi_indicator(roi):
    """Get performance indicator for marketing ROI"""
    return get_performance_indicator(roi, {'excellent': 10, 'good': 5})

def get_monthly_revenue_indicator(revenue, target=6000):
    """Get performance indicator for monthly revenue vs target"""
    percentage = (revenue / target) * 100
    return get_performance_indicator(percentage, {'excellent': 100, 'good': 80})

def get_ltv_indicator(ltv):
    """Get performance indicator for customer LTV"""
    return get_performance_indicator(ltv, {'excellent': 100, 'good': 50})

def get_cac_indicator(cac):
    """Get performance indicator for CAC (lower is better)"""
    if cac <= 15:
        return "🟢"
    elif cac <= 30:
        return "🟡"
    else:
        return "🔴"

def get_ltv_cac_ratio_indicator(ratio):
    """Get performance indicator for LTV:CAC ratio"""
    return get_performance_indicator(ratio, {'excellent': 5, 'good': 3})

# Business logic functions (keeping all existing functions)
def load_and_process_data(uploaded_files):
    """Load and combine multiple CSV files"""
    dataframes = []
    file_info = []
    
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file)
            df['Source_File'] = uploaded_file.name
            dataframes.append(df)
            file_info.append(f"📄 {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error loading {uploaded_file.name}: {str(e)}")
    
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        return combined_df, file_info
    return None, []

def process_transaction_data(df):
    """Process transaction data and add derived columns"""
    # Convert date column
    date_columns = ['Date', 'date', 'DATE']
    date_col = None
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[date_col])
        df['Month'] = df[date_col].dt.to_period('M')
        df['Month_Name'] = df[date_col].dt.strftime('%B %Y')
        df = df.sort_values(date_col)
    
    return df

def calculate_business_metrics(df):
    """Calculate core business metrics"""
    total_revenue = df['Amount Inc Tax'].sum()
    total_transactions = len(df)
    unique_customers = df['Sold To'].nunique() if 'Sold To' in df.columns else 0
    months = df['Month'].nunique() if 'Month' in df.columns else 1
    monthly_avg = total_revenue / months if months > 0 else 0
    
    return {
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'unique_customers': unique_customers,
        'monthly_avg': monthly_avg,
        'months': months
    }

def calculate_marketing_metrics(marketing_df, total_revenue):
    """Calculate marketing performance metrics"""
    if len(marketing_df) == 0:
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue,
            'campaigns': []
        }
    
    # Find the spend column
    spend_columns = ['Amount spent (GBP)', 'Amount', 'amount', 'Spend', 'spend', 'Cost', 'cost', 'Amount Spent', 'Amount (GBP)', 'Amount (USD)', 'Spent']
    spend_col = None
    for col in spend_columns:
        if col in marketing_df.columns:
            spend_col = col
            break
    
    if spend_col is None:
        st.warning("⚠️ No amount/spend column found in marketing data.")
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue,
            'campaigns': []
        }
    
    total_spend = marketing_df[spend_col].sum()
    roi = total_revenue / total_spend if total_spend > 0 else 0
    cost_per_revenue = total_spend / total_revenue if total_revenue > 0 else 0
    profit_after_ads = total_revenue - total_spend
    
    # Campaign breakdown
    campaign_col = 'Campaign name' if 'Campaign name' in marketing_df.columns else None
    campaigns = []
    if campaign_col:
        campaign_summary = marketing_df.groupby(campaign_col)[spend_col].sum()
        campaigns = [f"{name} - £{spend:.0f}" for name, spend in campaign_summary.items()]
    
    return {
        'total_spend': total_spend,
        'roi': roi,
        'cost_per_revenue': cost_per_revenue,
        'profit_after_ads': profit_after_ads,
        'campaigns': campaigns
    }

def calculate_customer_metrics(df):
    """Calculate customer-related metrics"""
    if 'Sold To' not in df.columns:
        return None
    
    customer_data = df.groupby('Sold To').agg({
        'Amount Inc Tax': 'sum',
        'Date': ['count', 'min', 'max']
    }).round(2)
    
    customer_data.columns = ['LTV', 'Transaction_Count', 'First_Purchase', 'Last_Purchase']
    customer_data = customer_data.reset_index()
    
    # Calculate metrics
    avg_ltv = customer_data['LTV'].mean()
    median_ltv = customer_data['LTV'].median()
    avg_transactions = customer_data['Transaction_Count'].mean()
    
    # Customer segmentation
    def segment_customer(ltv):
        if ltv >= 150:
            return 'VIP'
        elif ltv >= 75:
            return 'High Value'
        elif ltv >= 25:
            return 'Medium Value'
        else:
            return 'Low Value'
    
    customer_data['Segment'] = customer_data['LTV'].apply(segment_customer)
    
    # Purchase frequency (transactions per month)
    total_days = (df['Date'].max() - df['Date'].min()).days
    total_months = max(total_days / 30, 1)
    avg_frequency = len(df) / total_months
    
    return {
        'customer_data': customer_data,
        'avg_ltv': avg_ltv,
        'median_ltv': median_ltv,
        'avg_transactions': avg_transactions,
        'avg_frequency': avg_frequency,
        'segment_counts': customer_data['Segment'].value_counts()
    }

def calculate_promotion_analysis(transaction_df, marketing_df):
    """Calculate promotion-specific performance analysis"""
    if len(marketing_df) == 0:
        return None
    
    # Get campaign periods
    campaign_col = 'Campaign name' if 'Campaign name' in marketing_df.columns else None
    spend_col = None
    for col in ['Amount spent (GBP)', 'Amount', 'Spend', 'Cost']:
        if col in marketing_df.columns:
            spend_col = col
            break
    
    if not campaign_col or not spend_col:
        return None
    
    campaigns = []
    for campaign in marketing_df[campaign_col].unique():
        campaign_data = marketing_df[marketing_df[campaign_col] == campaign]
        total_spend = campaign_data[spend_col].sum()
        campaigns.append({
            'name': campaign,
            'spend': total_spend,
            'display': f"{campaign} - £{total_spend:.0f} spend"
        })
    
    return sorted(campaigns, key=lambda x: x['spend'], reverse=True)

def analyze_campaign_performance(transaction_df, campaign_info, selected_product='All Products'):
    """Analyze performance for a specific campaign period"""
    
    # For this demo, we'll use a simple date-based analysis
    # In a real scenario, you'd want more sophisticated attribution
    
    # Get total metrics
    total_revenue = transaction_df['Amount Inc Tax'].sum()
    total_customers = transaction_df['Sold To'].nunique() if 'Sold To' in transaction_df.columns else 0
    
    # Filter by product if specified
    if selected_product != 'All Products':
        product_df = transaction_df[transaction_df['Item'] == selected_product]
        product_revenue = product_df['Amount Inc Tax'].sum()
        product_customers = product_df['Sold To'].nunique() if 'Sold To' in product_df.columns else 0
    else:
        product_revenue = total_revenue
        product_customers = total_customers
    
    # Calculate ROI
    campaign_spend = campaign_info['spend']
    roi = product_revenue / campaign_spend if campaign_spend > 0 else 0
    
    # Calculate incremental metrics (simplified)
    baseline_revenue = product_revenue * 0.97  # Assume 3% lift for demo
    incremental_revenue = product_revenue - baseline_revenue
    incremental_roi = incremental_revenue / campaign_spend if campaign_spend > 0 else 0
    
    revenue_lift_pct = ((product_revenue - baseline_revenue) / baseline_revenue * 100) if baseline_revenue > 0 else 0
    customer_lift_pct = 1.5  # Demo value
    
    return {
        'campaign_revenue': product_revenue,
        'campaign_roi': roi,
        'incremental_roi': incremental_roi,
        'revenue_lift_pct': revenue_lift_pct,
        'customer_lift_pct': customer_lift_pct,
        'baseline_revenue': baseline_revenue,
        'incremental_revenue': incremental_revenue
    }

def calculate_customer_acquisition_analysis(df, marketing_campaigns):
    """Calculate customer acquisition costs and related metrics"""
    if 'Sold To' not in df.columns or len(marketing_campaigns) == 0:
        return None
    
    # Find first purchase date for each customer
    customer_first_purchase = df.groupby('Sold To')['Date'].min().reset_index()
    customer_first_purchase.columns = ['Customer', 'First_Purchase_Date']
    
    # Calculate customer LTV
    customer_ltv = df.groupby('Sold To')['Amount Inc Tax'].sum().reset_index()
    customer_ltv.columns = ['Customer', 'LTV']
    
    # Merge data
    customer_analysis = customer_first_purchase.merge(customer_ltv, on='Customer')
    
    # For demo purposes, we'll estimate CAC based on total marketing spend and new customers
    total_marketing_spend = sum([campaign['spend'] for campaign in marketing_campaigns])
    total_customers = len(customer_analysis)
    
    avg_cac = total_marketing_spend / total_customers if total_customers > 0 else 0
    avg_ltv = customer_analysis['LTV'].mean()
    ltv_cac_ratio = avg_ltv / avg_cac if avg_cac > 0 else 0
    
    # Estimate payback period (simplified)
    avg_monthly_spend = avg_ltv / 12  # Assume customers spread spending over 12 months
    payback_months = avg_cac / avg_monthly_spend if avg_monthly_spend > 0 else 0
    
    # Campaign-specific analysis
    campaign_analysis = []
    for campaign in marketing_campaigns:
        # Simplified: assume customers acquired proportionally to spend
        campaign_customers = int((campaign['spend'] / total_marketing_spend) * total_customers) if total_marketing_spend > 0 else 0
        campaign_cac = campaign['spend'] / campaign_customers if campaign_customers > 0 else 0
        campaign_ltv_cac = avg_ltv / campaign_cac if campaign_cac > 0 else 0
        
        campaign_analysis.append({
            'campaign': campaign['name'],
            'spend': campaign['spend'],
            'customers_acquired': campaign_customers,
            'cac': campaign_cac,
            'ltv_cac_ratio': campaign_ltv_cac
        })
    
    return {
        'avg_cac': avg_cac,
        'avg_ltv': avg_ltv,
        'ltv_cac_ratio': ltv_cac_ratio,
        'payback_months': payback_months,
        'total_customers': total_customers,
        'campaign_analysis': campaign_analysis,
        'customer_analysis': customer_analysis
    }

# Main App
st.title("🏋️ MyFitPod Complete Business Analytics")
st.markdown("*Professional Business Intelligence with Marketing ROI Tracking*")

# Add Help Guide at the top
show_help_guide()

# Sidebar for file uploads
st.sidebar.header("📊 Upload Your Data")
st.sidebar.markdown("Upload your business data for comprehensive analytics")

# Transaction data upload
st.sidebar.subheader("📈 Transaction Data (Required)")
st.sidebar.markdown("Upload transaction CSV files")
transaction_files = st.sidebar.file_uploader(
    "Choose transaction CSV files", 
    type=['csv'], 
    accept_multiple_files=True,
    key="transaction_upload"
)

# Marketing data upload
st.sidebar.subheader("📱 Marketing Data (Optional)")
st.sidebar.markdown("Export from Facebook Ads Manager, Google Ads, etc.")
marketing_files = st.sidebar.file_uploader(
    "Choose marketing CSV files", 
    type=['csv'], 
    accept_multiple_files=True,
    key="marketing_upload"
)

# Marketing CSV format guide
st.sidebar.markdown("### 📋 Marketing CSV Format")
st.sidebar.code("""
Date,Campaign,Amount spent (GBP)
2025-07-01,Smart Saver Summer,150.00
2025-07-15,Membership Drive,200.00
""")

# Main content
if transaction_files:
    # Load transaction data
    transaction_df, transaction_file_info = load_and_process_data(transaction_files)
    
    if transaction_df is not None:
        # Process transaction data
        transaction_df = process_transaction_data(transaction_df)
        
        # Load marketing data
        marketing_df = pd.DataFrame()
        marketing_file_info = []
        if marketing_files:
            marketing_df, marketing_file_info = load_and_process_data(marketing_files)
            if marketing_df is None:
                marketing_df = pd.DataFrame()
        
        # File status
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ {len(transaction_files)} transaction files uploaded")
            for file_info in transaction_file_info:
                st.markdown(file_info)
        
        with col2:
            if len(marketing_files) > 0:
                st.success(f"📱 {len(marketing_files)} marketing files uploaded")
                for file_info in marketing_file_info:
                    st.markdown(file_info)
            else:
                st.info("📱 No marketing data uploaded")
        
        # Main title and file loading status
        st.markdown("---")
        st.markdown("## 🏋️ MyFitPod Complete Business Analytics")
        st.markdown("*Professional Business Intelligence with Marketing ROI Tracking*")
        
        # File loading status
        st.markdown("### 📁 File Loading Status")
        if 'Month' in transaction_df.columns:
            date_range = f"{transaction_df['Month_Name'].iloc[0]} to {transaction_df['Month_Name'].iloc[-1]}"
            marketing_status = " + Marketing data" if len(marketing_df) > 0 else ""
            st.success(f"✅ Loaded {len(transaction_df)} transactions across {transaction_df['Month'].nunique()} months: {date_range}{marketing_status}")
        else:
            st.success(f"✅ Loaded {len(transaction_df)} transactions")
        
        # Calculate metrics
        business_metrics = calculate_business_metrics(transaction_df)
        marketing_metrics = calculate_marketing_metrics(marketing_df, business_metrics['total_revenue'])
        
        # Executive Summary
        st.markdown("### 📊 Executive Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            revenue_indicator = get_monthly_revenue_indicator(business_metrics['monthly_avg'])
            st.metric("💰 Total Revenue", f"£{business_metrics['total_revenue']:,.0f}")
            st.markdown(f"**Monthly Performance** {revenue_indicator}")
        
        with col2:
            if marketing_metrics['total_spend'] > 0:
                st.metric("📱 Marketing Spend", f"£{marketing_metrics['total_spend']:,.0f}")
            else:
                st.metric("📱 Marketing Spend", "£0")
        
        with col3:
            if marketing_metrics['total_spend'] > 0:
                roi_indicator = get_marketing_roi_indicator(marketing_metrics['roi'])
                st.metric("🎯 Marketing ROI", f"{marketing_metrics['roi']:.1f}x", delta=None)
                st.markdown(f"**ROI Performance** {roi_indicator}")
            else:
                st.metric("🎯 Marketing ROI", "No data")
        
        with col4:
            st.metric("👥 Customers", f"{business_metrics['unique_customers']:,}")
        
        with col5:
            if marketing_metrics['total_spend'] > 0:
                st.metric("📅 Monthly Avg Revenue", f"£{business_metrics['monthly_avg']:,.0f}")
            else:
                st.metric("💰 Profit After Ads", f"£{marketing_metrics['profit_after_ads']:,.0f}")
        
        # Marketing ROI Analysis
        if len(marketing_df) > 0:
            st.markdown("### 📱 Marketing ROI Analysis")
            
            # ROI Gauge
            roi_value = marketing_metrics['roi']
            roi_indicator = get_marketing_roi_indicator(roi_value)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = roi_value,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Marketing ROI {roi_indicator}"},
                delta = {'reference': 5},
                gauge = {
                    'axis': {'range': [None, max(20, roi_value * 1.2)]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 3], 'color': "lightgray"},
                        {'range': [3, 5], 'color': "yellow"},
                        {'range': [5, 10], 'color': "lightgreen"},
                        {'range': [10, max(20, roi_value * 1.2)], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 5
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Marketing insights
            st.markdown("#### 💡 Marketing Insights")
            if roi_value >= 10:
                st.success("🚀 Excellent ROI - Marketing is highly profitable")
            elif roi_value >= 5:
                st.success("✅ Good ROI - Marketing is profitable")
            elif roi_value >= 3:
                st.warning("⚠️ Moderate ROI - Room for improvement")
            else:
                st.error("❌ Low ROI - Review marketing strategy")
            
            st.info(f"💰 Cost efficiency: £{marketing_metrics['cost_per_revenue']:.2f} spent per £1 revenue")
        
        # Customer Value Intelligence
        customer_metrics = calculate_customer_metrics(transaction_df)
        if customer_metrics:
            st.markdown("### 👥 Customer Value Intelligence")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ltv_indicator = get_ltv_indicator(customer_metrics['avg_ltv'])
                st.metric("💎 Average Customer LTV", f"£{customer_metrics['avg_ltv']:.2f}")
                st.markdown(f"**LTV Performance** {ltv_indicator}")
            
            with col2:
                st.metric("📊 Median Customer LTV", f"£{customer_metrics['median_ltv']:.2f}")
            
            with col3:
                st.metric("🔄 Avg Transactions/Customer", f"{customer_metrics['avg_transactions']:.1f}")
            
            with col4:
                st.metric("📅 Avg Purchase Frequency", f"{customer_metrics['avg_frequency']:.1f}/month")
            
            # Customer Acquisition Cost Analysis
            marketing_campaigns = calculate_promotion_analysis(transaction_df, marketing_df)
            if marketing_campaigns:
                cac_analysis = calculate_customer_acquisition_analysis(transaction_df, marketing_campaigns)
                if cac_analysis:
                    st.markdown("### 💰 Customer Acquisition Cost (CAC) Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        cac_indicator = get_cac_indicator(cac_analysis['avg_cac'])
                        st.metric("📈 Average CAC", f"£{cac_analysis['avg_cac']:.2f}")
                        st.markdown(f"**CAC Efficiency** {cac_indicator}")
                    
                    with col2:
                        st.metric("💎 New Customer Avg LTV", f"£{cac_analysis['avg_ltv']:.2f}")
                    
                    with col3:
                        ratio_indicator = get_ltv_cac_ratio_indicator(cac_analysis['ltv_cac_ratio'])
                        st.metric("⚖️ LTV:CAC Ratio", f"{cac_analysis['ltv_cac_ratio']:.1f}:1")
                        st.markdown(f"**Ratio Performance** {ratio_indicator}")
                    
                    with col4:
                        payback_indicator = "🟢" if cac_analysis['payback_months'] <= 3 else "🟡" if cac_analysis['payback_months'] <= 6 else "🔴"
                        st.metric("⏱️ Avg Payback Period", f"{cac_analysis['payback_months']:.1f} months")
                        st.markdown(f"**Payback Speed** {payback_indicator}")
                    
                    # CAC by campaign table
                    if cac_analysis['campaign_analysis']:
                        st.markdown("#### 📊 Detailed CAC Analysis")
                        cac_df = pd.DataFrame(cac_analysis['campaign_analysis'])
                        cac_df['CAC'] = cac_df['cac'].apply(lambda x: f"£{x:.2f}")
                        cac_df['LTV:CAC Ratio'] = cac_df['ltv_cac_ratio'].apply(lambda x: f"{x:.1f}:1")
                        cac_df['Spend'] = cac_df['spend'].apply(lambda x: f"£{x:.0f}")
                        
                        display_df = cac_df[['campaign', 'Spend', 'customers_acquired', 'CAC', 'LTV:CAC Ratio']].copy()
                        display_df.columns = ['Campaign', 'Marketing Spend', 'Customers Acquired', 'CAC', 'LTV:CAC Ratio']
                        st.dataframe(display_df, use_container_width=True)
                    
                    # Customer acquisition insights
                    st.markdown("#### 💡 Customer Acquisition Insights")
                    if cac_analysis['ltv_cac_ratio'] >= 5:
                        st.success(f"✅ Excellent LTV:CAC ratio - {cac_analysis['ltv_cac_ratio']:.1f}:1 indicates highly profitable customer acquisition")
                    elif cac_analysis['ltv_cac_ratio'] >= 3:
                        st.success(f"✅ Good LTV:CAC ratio - {cac_analysis['ltv_cac_ratio']:.1f}:1 indicates profitable customer acquisition")
                    else:
                        st.warning(f"⚠️ Review customer acquisition - {cac_analysis['ltv_cac_ratio']:.1f}:1 ratio needs improvement")
                    
                    if cac_analysis['payback_months'] <= 3:
                        st.success(f"🚀 Fast payback period - {cac_analysis['payback_months']:.1f} months to recover acquisition costs")
                    elif cac_analysis['payback_months'] <= 6:
                        st.info(f"✅ Good payback period - {cac_analysis['payback_months']:.1f} months to recover costs")
                    else:
                        st.warning(f"⚠️ Long payback period - {cac_analysis['payback_months']:.1f} months to recover costs")
                    
                    # Best campaign
                    if cac_analysis['campaign_analysis']:
                        best_campaign = max(cac_analysis['campaign_analysis'], key=lambda x: x['ltv_cac_ratio'])
                        st.info(f"🏆 Best campaign: {best_campaign['campaign']} with {best_campaign['ltv_cac_ratio']:.1f}:1 ratio")
            
            # Customer Acquisition Trends
            st.markdown("### 📈 Customer Acquisition Trends")
            if 'Month_Name' in transaction_df.columns:
                monthly_customers = transaction_df.groupby('Month_Name')['Sold To'].nunique().reset_index()
                monthly_customers.columns = ['Month', 'New_Customers']
                
                fig_customers = px.bar(monthly_customers, x='Month', y='New_Customers',
                                     title="Monthly Customer Count",
                                     labels={'New_Customers': 'Customers', 'Month': 'Month'})
                st.plotly_chart(fig_customers, use_container_width=True)
            
            # High-Value Customer Analysis
