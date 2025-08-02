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
st.sidebar.markdown("**Upload multiple CSV files for comprehensive trend analysis**")

# Multiple file upload
uploaded_files = st.sidebar.file_uploader(
    "Upload your CSV files",
    type=['csv'],
    accept_multiple_files=True,
    help="Upload multiple monthly CSV files to see trends over time"
)

st.sidebar.markdown("---")
if uploaded_files:
    st.sidebar.success(f"✅ {len(uploaded_files)} files uploaded")
    for file in uploaded_files:
        st.sidebar.write(f"📄 {file.name}")

def load_and_combine_files(uploaded_files):
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
                'status': 'Success'
            })
        except Exception as e:
            file_info.append({
                'filename': file.name,
                'rows': 0,
                'status': f'Error: {str(e)}'
            })
    
    return combined_df, file_info

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

if uploaded_files:
    # Load and combine all files
    with st.spinner("Loading and processing files..."):
        df, file_info = load_and_combine_files(uploaded_files)
    
    # Show file loading status
    st.markdown("### 📁 File Loading Status")
    status_df = pd.DataFrame(file_info)
    st.dataframe(status_df, use_container_width=True)
    
    if len(df) > 0:
        # Process the combined data
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
        df['Month'] = df['Date'].dt.to_period('M')
        df['Month_Name'] = df['Date'].dt.strftime('%B %Y')
        
        # Determine if single or multi-month data
        unique_months = df['Month'].nunique()
        date_range = f"{df['Date'].min().strftime('%B %Y')} to {df['Date'].max().strftime('%B %Y')}" if unique_months > 1 else df['Date'].dt.strftime('%B %Y').iloc[0]
        
        st.success(f"✅ Combined {len(df)} transactions across {unique_months} months: {date_range}")
        
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
        
        # Multi-month trend analysis (if applicable)
        if unique_months > 1:
            st.markdown("## 📈 Multi-Month Trend Analysis")
            st.info(f"🎉 **Trend Analysis Activated!** Analyzing {unique_months} months of data")
            
            # Monthly revenue trends
            monthly_data = df.groupby(['Month', 'Month_Name']).agg({
                'Amount Inc Tax': 'sum',
                'Sold To': 'nunique'
            }).reset_index()
            
            # Sort by month period to ensure proper chronological order
            monthly_data = monthly_data.sort_values('Month').reset_index(drop=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Revenue trend
                fig_revenue = px.line(monthly_data, x='Month_Name', y='Amount Inc Tax',
                                    title="Monthly Revenue Trend",
                                    labels={'Amount Inc Tax': 'Revenue (£)', 'Month_Name': 'Month'},
                                    markers=True)
                fig_revenue.add_hline(y=6000, line_dash="dash", line_color="red", 
                                    annotation_text="£6K Target")
                st.plotly_chart(fig_revenue, use_container_width=True)
            
            with col2:
                # Customer growth
                fig_customers = px.line(monthly_data, x='Month_Name', y='Sold To',
                                      title="Monthly Customer Count",
                                      labels={'Sold To': 'Unique Customers', 'Month_Name': 'Month'},
                                      markers=True)
                st.plotly_chart(fig_customers, use_container_width=True)
            
            # Target achievement analysis
            st.markdown("### 🎯 Monthly Target Performance")
            monthly_data['Target_Hit'] = monthly_data['Amount Inc Tax'] >= 6000
            months_above_target = monthly_data['Target_Hit'].sum()
            total_months = len(monthly_data)
            success_rate = (months_above_target / total_months) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Months Above £6K", f"{months_above_target}/{total_months}")
            with col2:
                st.metric("Success Rate", f"{success_rate:.1f}%")
            with col3:
                avg_monthly = monthly_data['Amount Inc Tax'].mean()
                st.metric("Average Monthly Revenue", f"£{avg_monthly:,.0f}")
            with col4:
                # Calculate growth rate
                if len(monthly_data) >= 2:
                    recent_month = monthly_data['Amount Inc Tax'].iloc[-1]
                    previous_month = monthly_data['Amount Inc Tax'].iloc[-2]
                    growth_rate = ((recent_month - previous_month) / previous_month) * 100
                    st.metric("Latest Month Growth", f"{growth_rate:+.1f}%")
                else:
                    st.metric("Growth Rate", "N/A")
            
            # Monthly performance table
            st.markdown("### 📊 Monthly Performance Breakdown")
            display_data = monthly_data[['Month_Name', 'Amount Inc Tax', 'Sold To', 'Target_Hit']].copy()
            display_data['Amount Inc Tax'] = display_data['Amount Inc Tax'].apply(lambda x: f"£{x:,.0f}")
            display_data['Target_Hit'] = display_data['Target_Hit'].apply(lambda x: "✅ Yes" if x else "❌ No")
            display_data.columns = ['Month', 'Revenue', 'Customers', 'Hit £6K Target']
            st.dataframe(display_data, use_container_width=True)
            
            # Revenue model evolution
            st.markdown("### 💳 Business Model Evolution Over Time")
            
            monthly_breakdown = df.groupby(['Month_Name', 'Category'])['Amount Inc Tax'].sum().unstack(fill_value=0)
            if 'MEMBERSHIP' in monthly_breakdown.columns and 'CREDIT_PACK' in monthly_breakdown.columns:
                monthly_breakdown['Total'] = monthly_breakdown['MEMBERSHIP'] + monthly_breakdown['CREDIT_PACK']
                monthly_breakdown['Membership_Pct'] = (monthly_breakdown['MEMBERSHIP'] / monthly_breakdown['Total']) * 100
                
                # Sort by chronological order
                month_order = df.groupby('Month_Name')['Month'].min().sort_values().index
                monthly_breakdown = monthly_breakdown.reindex(month_order)
                
                fig_evolution = px.line(monthly_breakdown.reset_index(), x='Month_Name', y='Membership_Pct',
                                      title="Membership Revenue % Over Time",
                                      labels={'Membership_Pct': 'Membership %', 'Month_Name': 'Month'},
                                      markers=True)
                fig_evolution.update_layout(yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_evolution, use_container_width=True)
        
        else:
            st.markdown("## 📊 Single Month Analysis")
            st.info("💡 Upload multiple months of data to unlock trend analysis features!")
        
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
            
            # Growth trend analysis
            monthly_revenues = df.groupby('Month')['Amount Inc Tax'].sum().values
            if len(monthly_revenues) >= 3:
                if len(monthly_revenues) >= 6:
                    recent_avg = np.mean(monthly_revenues[-3:])
                    earlier_avg = np.mean(monthly_revenues[-6:-3])
                    trend_change = recent_avg - earlier_avg
                else:
                    trend_change = monthly_revenues[-1] - monthly_revenues[0]
                
                if trend_change > 500:
                    insights.append(f"📈 **Strong growth trend** - Revenue increasing by £{trend_change:,.0f} in recent period")
                elif trend_change > 0:
                    insights.append("📊 **Positive growth trend** - Revenue showing steady improvement")
                elif trend_change > -500:
                    insights.append("📊 **Stable performance** - Revenue showing consistency")
                else:
                    insights.append("⚠️ **Performance declining** - Focus on growth initiatives")
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
        st.error("❌ No valid data found in uploaded files. Please check your CSV format.")

else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to MyFitPod Analytics
    
    ### Upload your CSV files to get comprehensive business intelligence:
    
    **📁 Multiple File Upload:**
    - Upload multiple monthly CSV files at once
    - Automatic data combination and processing
    - Comprehensive trend analysis across all months
    
    **📊 Single Month Analysis:**
    - Current month performance vs £6K target
    - Revenue model breakdown (Membership vs Pay-as-you-go)
    - Customer behavior analysis
    - Product performance insights
    
    **📈 Multi-Month Trend Analysis:**
    - Monthly revenue growth trends
    - Target achievement tracking over time
    - Business model evolution
    - Customer growth patterns
    - Month-over-month performance comparison
    
    **💡 Automated Business Intelligence:**
    - Growth trend identification
    - Revenue optimization opportunities
    - Customer value insights
    - Performance benchmarking
    - Strategic recommendations
    
    **👈 Use the sidebar to upload your CSV files and get started!**
    
    *Tip: Upload multiple months of data to unlock comprehensive trend analysis features*
    """)
