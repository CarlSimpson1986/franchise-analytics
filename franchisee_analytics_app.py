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
    """Calculate marketing ROI metrics"""
    if len(marketing_df) == 0 or 'Amount' not in marketing_df.columns:
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }
    
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
        return {
            'total_spend': 0,
            'roi': 0,
            'cost_per_revenue': 0,
            'profit_after_ads': total_revenue
        }

def calculate_promotion_analysis(transaction_df, marketing_df):
    """Calculate flexible promotion period analysis"""
    if len(transaction_df) == 0:
        return {
            'has_promotion_data': False,
            'promotion_periods': []
        }
    
    # Get unique months for promotion period selection
    transaction_df['Month_Period'] = transaction_df['Date'].dt.to_period('M')
    available_periods = sorted(transaction_df['Month_Period'].unique())
    
    # Identify potential promotion periods (months with marketing spend)
    promotion_periods = []
    if len(marketing_df) > 0 and 'Amount' in marketing_df.columns:
        # Try to extract dates from marketing data
        if 'Reporting starts' in marketing_df.columns and 'Reporting ends' in marketing_df.columns:
            for _, row in marketing_df.iterrows():
                try:
                    start_date = pd.to_datetime(row['Reporting starts'], errors='coerce')
                    end_date = pd.to_datetime(row['Reporting ends'], errors='coerce')
                    if pd.notna(start_date) and pd.notna(end_date):
                        campaign_name = row.get('Campaign name', row.get('Campaign', 'Promotion'))
                        promotion_periods.append({
                            'start_date': start_date,
                            'end_date': end_date,
                            'campaign_name': campaign_name,
                            'spend': row.get('Amount', 0)
                        })
                except:
                    continue
        
        # Fallback: use months with marketing data
        if not promotion_periods and 'Date' in marketing_df.columns:
            marketing_months = marketing_df['Date'].dt.to_period('M').unique()
            for month in marketing_months:
                month_spend = marketing_df[marketing_df['Date'].dt.to_period('M') == month]['Amount'].sum()
                promotion_periods.append({
                    'period': month,
                    'spend': month_spend,
                    'campaign_name': f"{month} Campaign"
                })
    
    return {
        'has_promotion_data': len(promotion_periods) > 0,
        'promotion_periods': promotion_periods
    }

def analyze_promotion_performance(transaction_df, promotion_start, promotion_end, marketing_spend=0):
    """Analyze performance during a specific promotion period"""
    
    # Filter data for promotion period
    promotion_data = transaction_df[
        (transaction_df['Date'] >= promotion_start) & 
        (transaction_df['Date'] <= promotion_end)
    ]
    
    if len(promotion_data) == 0:
        return {}
    
    # Calculate promotion metrics
    promotion_revenue = promotion_data['Amount Inc Tax'].sum()
    promotion_transactions = len(promotion_data)
    promotion_customers = promotion_data['Sold To'].nunique() if 'Sold To' in promotion_data.columns else 0
    
    # Product performance during promotion
    if 'Quantity Sold' in promotion_data.columns:
        product_performance = promotion_data.groupby('Item').agg({
            'Amount Inc Tax': 'sum',
            'Quantity Sold': 'sum',
            'Sold To': 'nunique' if 'Sold To' in promotion_data.columns else 'count'
        }).round(2)
        product_performance.columns = ['Revenue', 'Units_Sold', 'Customers']
        product_performance['Avg_Price'] = product_performance['Revenue'] / product_performance['Units_Sold'].replace(0, 1)
        product_performance = product_performance.reset_index().sort_values('Revenue', ascending=False)
    else:
        product_performance = promotion_data.groupby('Item').agg({
            'Amount Inc Tax': 'sum'
        }).round(2)
        product_performance.columns = ['Revenue']
        product_performance['Units_Sold'] = 1  # Default if no quantity data
        product_performance['Customers'] = 1
        product_performance['Avg_Price'] = product_performance['Revenue']
        product_performance = product_performance.reset_index().sort_values('Revenue', ascending=False)
    
    # Calculate comparison period (same period previous month if available)
    period_duration = (promotion_end - promotion_start).days
    comparison_start = promotion_start - pd.Timedelta(days=30)
    comparison_end = comparison_start + pd.Timedelta(days=period_duration)
    
    comparison_data = transaction_df[
        (transaction_df['Date'] >= comparison_start) & 
        (transaction_df['Date'] <= comparison_end)
    ]
    
    # Comparison metrics
    comparison_revenue = comparison_data['Amount Inc Tax'].sum() if len(comparison_data) > 0 else 0
    comparison_transactions = len(comparison_data)
    comparison_customers = comparison_data['Sold To'].nunique() if len(comparison_data) > 0 and 'Sold To' in comparison_data.columns else 0
    
    # Calculate lifts
    revenue_lift = ((promotion_revenue - comparison_revenue) / comparison_revenue * 100) if comparison_revenue > 0 else 0
    transaction_lift = ((promotion_transactions - comparison_transactions) / comparison_transactions * 100) if comparison_transactions > 0 else 0
    customer_lift = ((promotion_customers - comparison_customers) / comparison_customers * 100) if comparison_customers > 0 else 0
    
    # ROI calculation
    roi = (promotion_revenue / marketing_spend) if marketing_spend > 0 else 0
    incremental_revenue = promotion_revenue - comparison_revenue
    incremental_roi = (incremental_revenue / marketing_spend) if marketing_spend > 0 else 0
    
    return {
        'promotion_revenue': promotion_revenue,
        'promotion_transactions': promotion_transactions,
        'promotion_customers': promotion_customers,
        'comparison_revenue': comparison_revenue,
        'comparison_transactions': comparison_transactions,
        'comparison_customers': comparison_customers,
        'revenue_lift': revenue_lift,
        'transaction_lift': transaction_lift,
        'customer_lift': customer_lift,
        'roi': roi,
        'incremental_revenue': incremental_revenue,
        'incremental_roi': incremental_roi,
        'product_performance': product_performance,
        'marketing_spend': marketing_spend
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
        
        # Product Performance Analysis
        st.markdown("## 💰 Product Performance Analysis")
        
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
            # Top products by revenue
            top_products_revenue = transaction_df.groupby('Item')['Amount Inc Tax'].sum().nlargest(8)
            fig_products_revenue = px.bar(x=top_products_revenue.values, y=top_products_revenue.index, 
                                        orientation='h', title="Top Products by Revenue")
            st.plotly_chart(fig_products_revenue, use_container_width=True)
        
        # Enhanced Product Analysis with Quantities
        if 'Quantity Sold' in transaction_df.columns:
            st.markdown("### 📊 Product Quantity & Performance Analysis")
            
            # Product performance table with quantities
            product_details = transaction_df.groupby('Item').agg({
                'Amount Inc Tax': 'sum',
                'Quantity Sold': 'sum',
                'Sold To': 'nunique' if 'Sold To' in transaction_df.columns else 'count'
            }).round(2)
            product_details.columns = ['Total_Revenue', 'Units_Sold', 'Customers']
            product_details['Avg_Price'] = (product_details['Total_Revenue'] / product_details['Units_Sold'].replace(0, 1)).round(2)
            product_details['Revenue_Per_Customer'] = (product_details['Total_Revenue'] / product_details['Customers'].replace(0, 1)).round(2)
            product_details = product_details.reset_index().sort_values('Total_Revenue', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top products by quantity
                top_products_qty = product_details.nlargest(8, 'Units_Sold')
                fig_qty = px.bar(top_products_qty, x='Units_Sold', y='Item', 
                               orientation='h', title="Top Products by Units Sold")
                st.plotly_chart(fig_qty, use_container_width=True)
            
            with col2:
                # Product performance table
                st.markdown("**Product Performance Summary:**")
                display_products = product_details.copy()
                display_products['Total_Revenue'] = display_products['Total_Revenue'].apply(lambda x: f"£{x:,.0f}")
                display_products['Avg_Price'] = display_products['Avg_Price'].apply(lambda x: f"£{x:.2f}")
                display_products['Revenue_Per_Customer'] = display_products['Revenue_Per_Customer'].apply(lambda x: f"£{x:.2f}")
                display_products.columns = ['Product', 'Revenue', 'Units', 'Customers', 'Avg Price', 'Rev/Customer']
                st.dataframe(display_products, use_container_width=True, hide_index=True)
        
        # Promotion Analysis Section
        if promotion_analysis['has_promotion_data'] and len(marketing_df) > 0:
            st.markdown("## 🎯 Promotion Period Analysis")
            st.info("📈 **Intelligent promotion tracking** - Analyze any campaign period performance vs baseline")
            
            # Let user select promotion period to analyze
            if promotion_analysis['promotion_periods']:
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_promotion = st.selectbox(
                        "1️⃣ Select Campaign Period:",
                        range(len(promotion_analysis['promotion_periods'])),
                        format_func=lambda x: f"{promotion_analysis['promotion_periods'][x].get('campaign_name', 'Campaign')} - £{promotion_analysis['promotion_periods'][x].get('spend', 0):.0f} spend"
                    )
                
                with col2:
                    # Get unique products from transaction data
                    unique_products = sorted(transaction_df['Item'].unique())
                    product_options = ['All Products'] + unique_products
                    
                    selected_product = st.selectbox(
                        "2️⃣ Select Product Focus:",
                        product_options,
                        help="Choose 'All Products' for overall campaign performance, or select a specific product to analyze"
                    )
                
                promo_period = promotion_analysis['promotion_periods'][selected_promotion]
                
                # Analyze selected promotion
                if 'start_date' in promo_period and 'end_date' in promo_period:
                    # Filter transaction data by selected product if not "All Products"
                    analysis_df = transaction_df.copy()
                    if selected_product != 'All Products':
                        analysis_df = transaction_df[transaction_df['Item'] == selected_product]
                        st.info(f"🎯 **Analyzing {selected_product}** performance during {promo_period.get('campaign_name', 'campaign')}")
                    else:
                        st.info(f"📊 **Analyzing all products** performance during {promo_period.get('campaign_name', 'campaign')}")
                    
                    promo_results = analyze_promotion_performance(
                        analysis_df, 
                        promo_period['start_date'], 
                        promo_period['end_date'],
                        promo_period.get('spend', 0)
                    )
                    
                    if promo_results:
                        # Promotion performance metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            revenue_label = f"{selected_product} Revenue" if selected_product != 'All Products' else "Campaign Revenue"
                            st.metric(
                                revenue_label, 
                                f"£{promo_results['promotion_revenue']:,.0f}",
                                delta=f"{promo_results['revenue_lift']:+.1f}% vs baseline"
                            )
                        
                        with col2:
                            roi_label = f"{selected_product} ROI" if selected_product != 'All Products' else "Campaign ROI"
                            st.metric(
                                roi_label, 
                                f"{promo_results['roi']:.1f}x",
                                help="Revenue ÷ marketing spend"
                            )
                        
                        with col3:
                            st.metric(
                                "Incremental ROI", 
                                f"{promo_results['incremental_roi']:.1f}x",
                                help="Additional revenue ÷ marketing spend"
                            )
                        
                        with col4:
                            st.metric(
                                "Customer Lift", 
                                f"{promo_results['customer_lift']:+.1f}%",
                                help="Customer increase vs comparison period"
                            )
                        
                        # Product performance during promotion
                        if len(promo_results['product_performance']) > 0:
                            if selected_product == 'All Products':
                                st.markdown("### 🏆 All Products Performance During Campaign")
                            else:
                                st.markdown(f"### 🏆 {selected_product} Performance During Campaign")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Product revenue during promotion
                                fig_promo_revenue = px.bar(
                                    promo_results['product_performance'].head(8), 
                                    x='Revenue', y='Item', 
                                    orientation='h', 
                                    title="Revenue by Product (Campaign Period)"
                                )
                                st.plotly_chart(fig_promo_revenue, use_container_width=True)
                            
                            with col2:
                                # Product quantities during promotion
                                fig_promo_qty = px.bar(
                                    promo_results['product_performance'].head(8), 
                                    x='Units_Sold', y='Item', 
                                    orientation='h', 
                                    title="Units Sold by Product (Campaign Period)"
                                )
                                st.plotly_chart(fig_promo_qty, use_container_width=True)
                            
                            # Detailed product performance table
                            if selected_product != 'All Products':
                                st.markdown(f"### 📊 {selected_product} Detailed Performance")
                                
                                # Filter for selected product only
                                selected_product_data = promo_results['product_performance'][
                                    promo_results['product_performance']['Item'] == selected_product
                                ]
                                
                                if len(selected_product_data) > 0:
                                    product_row = selected_product_data.iloc[0]
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Product Revenue", f"£{product_row['Revenue']:,.2f}")
                                    with col2:
                                        st.metric("Units Sold", f"{product_row['Units_Sold']:,.0f}")
                                    with col3:
                                        st.metric("Average Price", f"£{product_row['Avg_Price']:,.2f}")
                                    with col4:
                                        st.metric("Customers", f"{product_row['Customers']:,.0f}")
                                else:
                                    st.warning(f"⚠️ No {selected_product} sales during this campaign period")
                        
                        # Campaign attribution insights
                        st.markdown("### 💡 Campaign Attribution Insights")
                        
                        if selected_product != 'All Products':
                            # Product-specific insights
                            total_campaign_revenue = promo_results['promotion_revenue']
                            product_attribution = (total_campaign_revenue / promo_period.get('spend', 1)) if promo_period.get('spend', 0) > 0 else 0
                            
                            attribution_insights = []
                            
                            if product_attribution > 3:
                                attribution_insights.append(f"✅ **{selected_product} campaign profitable** - {product_attribution:.1f}x ROI")
                            elif product_attribution > 1:
                                attribution_insights.append(f"⚠️ **{selected_product} campaign break-even** - {product_attribution:.1f}x ROI")
                            else:
                                attribution_insights.append(f"❌ **{selected_product} campaign unprofitable** - {product_attribution:.1f}x ROI")
                            
                            if promo_results['revenue_lift'] > 20:
                                attribution_insights.append(f"📈 **Strong {selected_product} lift** - {promo_results['revenue_lift']:.1f}% increase vs baseline")
                            elif promo_results['revenue_lift'] > 0:
                                attribution_insights.append(f"📊 **Moderate {selected_product} lift** - {promo_results['revenue_lift']:.1f}% increase")
                            else:
                                attribution_insights.append(f"⚠️ **{selected_product} performance declined** during campaign")
                        
                        else:
                            # Overall campaign insights
                            attribution_insights = []
                            
                            if promo_results['incremental_roi'] > 5:
                                attribution_insights.append("🚀 **Excellent campaign ROI** - Scale up similar campaigns")
                            elif promo_results['incremental_roi'] > 2:
                                attribution_insights.append("✅ **Profitable campaign** - Good incremental return")
                            elif promo_results['incremental_roi'] > 0:
                                attribution_insights.append("⚠️ **Marginal campaign** - Consider optimization")
                            else:
                                attribution_insights.append("❌ **Unprofitable campaign** - Review strategy")
                            
                            if promo_results['revenue_lift'] > 20:
                                attribution_insights.append(f"📈 **Strong overall lift** - {promo_results['revenue_lift']:.1f}% increase vs baseline")
                            elif promo_results['revenue_lift'] > 10:
                                attribution_insights.append(f"📊 **Moderate overall lift** - {promo_results['revenue_lift']:.1f}% increase")
                            
                            if promo_results['customer_lift'] > 15:
                                attribution_insights.append("👥 **Great customer acquisition** - Attracting new customers")
                        
                        for insight in attribution_insights:
                            st.info(insight)
                
                # Campaign comparison section
                st.markdown("### 🔄 Quick Campaign Comparison")
                st.info("""
                **💡 Pro Tip:** Try analyzing different products with the same campaign to see:
                - Which products benefited most from the campaign
                - Overall campaign effectiveness vs product-specific impact
                - Cross-selling opportunities (Smart Saver ad → Membership sales)
                """)
        
        
        elif len(marketing_df) > 0:
            st.markdown("## 🎯 Promotion Analysis")
            st.info("""
            **💡 Enhanced promotion tracking available!**
            
            Your marketing CSV contains campaign data. For detailed promotion analysis:
            1. Ensure date ranges are included in marketing data
            2. Run campaigns for specific products or periods
            3. Get detailed before/during/after performance comparison
            
            **Track any promotion:**
            - Smart Saver campaigns
            - Membership drives  
            - Credit pack specials
            - Any product focus
            """)
        
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
    - Product quantity and performance tracking
    
    **📱 Marketing ROI Tracking:**
    - Marketing spend analysis
    - Return on investment calculation
    - Campaign performance comparison
    - Flexible promotion period analysis
    
    **🎯 Promotion Analysis:**
    - Before/during/after campaign comparison
    - Product performance during promotions
    - Revenue lift calculation
    - Incremental ROI tracking
    
    **💡 Intelligent Insights:**
    - Automated business recommendations
    - Growth opportunity identification
    - Performance optimization suggestions
    - Strategic planning support
    
    **📊 Key Features:**
    - **Multi-file upload** - Combine multiple months of data
    - **Marketing integration** - Upload ad spend from any platform
    - **Flexible promotion tracking** - Analyze any campaign period
    - **Quantity analysis** - Track units sold vs revenue
    - **Professional dashboards** - Executive-ready reports
    
    **👈 Use the sidebar to upload your CSV files and get started!**
    
    ### 📋 Quick Start Guide:
    
    **Step 1:** Upload your transaction CSV files (from your pod system)
    **Step 2:** Optionally upload marketing spend CSV files (from Facebook Ads, Google Ads, etc.)
    **Step 3:** Get comprehensive business intelligence with flexible promotion analysis!
    
    *Transform your raw data into actionable business insights in minutes!*
    """)
