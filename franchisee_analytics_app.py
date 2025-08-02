import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="MyFitPod Franchise Analytics",
    page_icon="🏋️",
    layout="wide"
)

st.title("🏋️ MyFitPod Franchise Analytics")
st.markdown("### Professional Business Intelligence for Pod Locations")
st.markdown("---")

# Sidebar for file upload
st.sidebar.title("📊 Upload Your Data")
st.sidebar.markdown("**Upload single month or multiple months for trend analysis**")
uploaded_file = st.sidebar.file_uploader(
    "Upload your CSV file(s)",
    type=['csv'],
    help="Upload your monthly transaction data"
)

def analyze_customer_behavior(df):
    """Analyze customer patterns"""
    if 'Sold To' in df.columns:
        customer_analysis = df.groupby('Sold To').agg({
            'Amount Inc Tax': ['sum', 'count', 'mean'],
            'Date': ['min', 'max']
        }).round(2)
        
        customer_analysis.columns = ['Total_Spent', 'Visit_Count', 'Avg_Spend', 'First_Visit', 'Last_Visit']
        customer_analysis = customer_analysis.reset_index()
        return customer_analysis
    return None

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

if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df['Month'] = df['Date'].dt.to_period('M')
    df['Month_Name'] = df['Date'].dt.strftime('%B %Y')
    
    # Determine if single or multi-month data
    unique_months = df['Month'].nunique()
    date_range = f"{df['Date'].min().strftime('%B %Y')} to {df['Date'].max().strftime('%B %Y')}" if unique_months > 1 else df['Date'].dt.strftime('%B %Y').iloc[0]
    
    st.success(f"✅ Loaded {len(df)} transactions from {date_range}")
    
    # Calculate overall metrics
    metrics = calculate_business_metrics(df)
    
    # Key metrics at the top
    st.markdown("## 📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Revenue", f"£{metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("📈 Transactions", f"{metrics['total_transactions']:,}")
    with col3:
        st.metric("👥 Unique Customers", f"{metrics['unique_customers']:,}")
    with col4:
        if unique_months > 1:
            monthly_avg = metrics['total_revenue'] / unique_months
            st.metric("📅 Monthly Average", f"£{monthly_avg:,.0f}")
        else:
            st.metric("💳 Avg Transaction", f"£{metrics['avg_transaction']:.2f}")
    
    st.markdown("---")
    
    # Multi-month trend analysis
    if unique_months > 1:
        st.markdown("## 📈 Monthly Trend Analysis")
        
        # Monthly revenue trends
        monthly_data = df.groupby('Month_Name').agg({
            'Amount Inc Tax': 'sum',
            'Sold To': 'nunique'
        }).reset_index()
        
        # Sort by actual date to ensure proper order
        month_order = df.groupby('Month_Name')['Date'].min().sort_values().index
        monthly_data = monthly_data.set_index('Month_Name').reindex(month_order).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue trend
            fig_revenue = px.line(monthly_data, x='Month_Name', y='Amount Inc Tax',
                                title="Monthly Revenue Trend",
                                labels={'Amount Inc Tax': 'Revenue (£)', 'Month_Name': 'Month'})
            fig_revenue.add_hline(y=6000, line_dash="dash", line_color="red", 
                                annotation_text="£6K Target")
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            # Customer growth
            fig_customers = px.line(monthly_data, x='Month_Name', y='Sold To',
                                  title="Monthly Customer Count",
                                  labels={'Sold To': 'Unique Customers', 'Month_Name': 'Month'})
            st.plotly_chart(fig_customers, use_container_width=True)
        
        # Target achievement analysis
        st.markdown("### 🎯 Monthly Target Performance")
        monthly_data['Target_Hit'] = monthly_data['Amount Inc Tax'] >= 6000
        months_above_target = monthly_data['Target_Hit'].sum()
        total_months = len(monthly_data)
        success_rate = (months_above_target / total_months) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Months Above £6K", f"{months_above_target}/{total_months}")
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            avg_monthly = monthly_data['Amount Inc Tax'].mean()
            st.metric("Average Monthly Revenue", f"£{avg_monthly:,.0f}")
        
        # Revenue model evolution
        st.markdown("### 💳 Business Model Evolution")
        
        monthly_breakdown = df.groupby(['Month_Name', 'Category'])['Amount Inc Tax'].sum().unstack(fill_value=0)
        if 'MEMBERSHIP' in monthly_breakdown.columns and 'CREDIT_PACK' in monthly_breakdown.columns:
            monthly_breakdown['Membership_Pct'] = (monthly_breakdown['MEMBERSHIP'] / 
                                                 (monthly_breakdown['MEMBERSHIP'] + monthly_breakdown['CREDIT_PACK'])) * 100
            
            # Reorder by date
            monthly_breakdown = monthly_breakdown.reindex(month_order)
            
            fig_evolution = px.line(monthly_breakdown.reset_index(), x='Month_Name', y='Membership_Pct',
                                  title="Membership Revenue % Over Time",
                                  labels={'Membership_Pct': 'Membership %', 'Month_Name': 'Month'})
            fig_evolution.update_yaxis(range=[0, 100])
            st.plotly_chart(fig_evolution, use_container_width=True)
    
    # Current/Overall Performance Analysis
    st.markdown("## 💰 Revenue Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Business model breakdown
        revenue_data = pd.DataFrame({
            'Type': ['Membership', 'Pay-as-you-go'],
            'Revenue': [metrics['membership_revenue'], metrics['payg_revenue']],
            'Percentage': [metrics['membership_pct'], metrics['payg_pct']]
        })
        
        fig_pie = px.pie(revenue_data, values='Revenue', names='Type',
                        title="Revenue by Business Model")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Business model metrics
        st.markdown("**Business Model Split:**")
        st.metric("Membership Revenue", f"£{metrics['membership_revenue']:,.0f} ({metrics['membership_pct']:.1f}%)")
        st.metric("Pay-as-you-go Revenue", f"£{metrics['payg_revenue']:,.0f} ({metrics['payg_pct']:.1f}%)")
    
    with col2:
        # Top products
        top_products = df.groupby('Item')['Amount Inc Tax'].sum().nlargest(8)
        fig_products = px.bar(x=top_products.values, y=top_products.index, 
                            orientation='h', title="Top Products by Revenue")
        st.plotly_chart(fig_products, use_container_width=True)
    
    # Customer Analysis
    if 'Sold To' in df.columns:
        st.markdown("## 👥 Customer Intelligence")
        
        customer_data = analyze_customer_behavior(df)
        
        if customer_data is not None:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_ltv = customer_data['Total_Spent'].mean()
                st.metric("Average Customer LTV", f"£{avg_ltv:.2f}")
            
            with col2:
                avg_visits = customer_data['Visit_Count'].mean()
                st.metric("Average Visits per Customer", f"{avg_visits:.1f}")
            
            with col3:
                st.metric("Revenue per Customer", f"£{metrics['revenue_per_customer']:.2f}")
            
            # Customer value distribution
            fig_ltv = px.histogram(customer_data, x='Total_Spent', nbins=20,
                                 title="Customer Lifetime Value Distribution")
            st.plotly_chart(fig_ltv, use_container_width=True)
    
    # Business Intelligence Insights
    st.markdown("## 💡 Business Intelligence Insights")
    
    insights = []
    
    # Revenue model insights
    if metrics['membership_pct'] > 60:
        insights.append("✅ **Strong subscription focus** - You have a solid recurring revenue base")
    elif metrics['membership_pct'] > 40:
        insights.append("⚖️ **Balanced revenue model** - Good mix of recurring and flexible revenue")
    else:
        insights.append("📈 **Growth opportunity** - Focus on converting PAYG customers to memberships")
    
    # Performance insights
    if unique_months > 1:
        monthly_avg = metrics['total_revenue'] / unique_months
        if monthly_avg >= 6000:
            insights.append("🎯 **Monthly target achieved** - Averaging above £6K per month")
        else:
            gap = 6000 - monthly_avg
            insights.append(f"🚀 **Growth needed** - Increase revenue by £{gap:,.0f}/month to hit £6K target")
        
        # Growth trend
        monthly_revenues = df.groupby('Month')['Amount Inc Tax'].sum().values
        if len(monthly_revenues) >= 3:
            recent_trend = np.mean(monthly_revenues[-3:]) - np.mean(monthly_revenues[-6:-3]) if len(monthly_revenues) >= 6 else monthly_revenues[-1] - monthly_revenues[0]
            if recent_trend > 0:
                insights.append(f"📈 **Positive growth trend** - Revenue increasing by £{recent_trend:,.0f} in recent months")
            else:
                insights.append("📊 **Stable performance** - Revenue showing consistency")
    else:
        current_revenue = metrics['total_revenue']
        if current_revenue >= 6000:
            insights.append(f"🎉 **Target achieved this month** - £{current_revenue:,.0f} vs £6K target")
        else:
            gap = 6000 - current_revenue
            insights.append(f"📈 **Growth opportunity** - £{gap:,.0f} away from £6K monthly target")
    
    # Customer insights
    if metrics['unique_customers'] > 0:
        if metrics['revenue_per_customer'] > 50:
            insights.append("💎 **High customer value** - Strong revenue per customer")
        else:
            insights.append("🎯 **Upsell opportunity** - Focus on increasing customer spend")
    
    for insight in insights:
        st.info(insight)

else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to MyFitPod Analytics
    
    ### Upload your CSV data to get comprehensive business intelligence:
    
    **📊 Single Month Analysis:**
    - Current month performance vs £6K target
    - Revenue model breakdown (Membership vs Pay-as-you-go)
    - Customer behavior analysis
    - Product performance insights
    
    **📈 Multi-Month Trend Analysis:**
    - Monthly revenue growth trends
    - Target achievement tracking
    - Business model evolution over time
    - Customer growth patterns
    - Seasonal performance insights
    
    **💡 Automated Business Intelligence:**
    - Growth recommendations
    - Revenue optimization opportunities
    - Customer value insights
    - Performance benchmarking
    
    **👈 Use the sidebar to upload your transaction CSV file and get started!**
    
    *Tip: Upload multiple months of data for comprehensive trend analysis*
    """)
