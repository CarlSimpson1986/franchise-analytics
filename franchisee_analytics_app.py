import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="MyFitPod Franchise Analytics",
    page_icon="🏋️",
    layout="wide"
)

st.title("🏋️ MyFitPod Franchise Analytics")
st.markdown("### Professional Business Intelligence for Franchise Locations")
st.markdown("---")

# Sidebar for file upload
st.sidebar.title("📊 Upload Your Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload your monthly CSV file",
    type=['csv'],
    help="Upload your gym transaction data"
)

if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    
    st.success(f"✅ Loaded {len(df)} transactions successfully!")
    
    # Key metrics at the top
    st.markdown("## 📊 Key Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = df['Amount Inc Tax'].sum()
    total_transactions = len(df)
    avg_transaction = df['Amount Inc Tax'].mean()
    
    with col1:
        st.metric("💰 Total Revenue", f"£{total_revenue:,.0f}")
    with col2:
        st.metric("📈 Transactions", f"{total_transactions:,}")
    with col3:
        st.metric("💳 Avg Transaction", f"£{avg_transaction:.2f}")
    with col4:
        months = df['Date'].dt.to_period('M').nunique()
        monthly_avg = total_revenue / max(1, months)
        st.metric("📅 Monthly Average", f"£{monthly_avg:,.0f}")
    
    st.markdown("---")
    
    # £6K Target Progress
    st.markdown("## 🎯 Progress Toward £6K Monthly Target")
    
    target = 6000
    progress = min((monthly_avg / target) * 100, 100)
    
    # Progress bar
    st.progress(progress / 100)
    
    col1, col2 = st.columns(2)
    with col1:
        if monthly_avg >= target:
            st.success(f"🎉 **TARGET ACHIEVED!** You're making £{monthly_avg:,.0f}/month!")
        else:
            gap = target - monthly_avg
            st.warning(f"📈 **GROWTH NEEDED:** £{gap:,.0f} more to reach £6K target ({progress:.1f}% complete)")
    
    with col2:
        # Simple gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = monthly_avg,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Monthly Revenue vs £6K Target"},
            gauge = {
                'axis': {'range': [None, 8000]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 4000], 'color': "lightgray"},
                    {'range': [4000, 6000], 'color': "yellow"},
                    {'range': [6000, 8000], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 6000
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Revenue breakdown
    st.markdown("## 💰 Revenue Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category breakdown
        category_revenue = df.groupby('Category')['Amount Inc Tax'].sum()
        fig = px.pie(values=category_revenue.values, names=category_revenue.index,
                    title="Revenue by Category")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top products
        top_products = df.groupby('Item')['Amount Inc Tax'].sum().nlargest(8)
        fig = px.bar(x=top_products.values, y=top_products.index, 
                    orientation='h', title="Top Products by Revenue")
        st.plotly_chart(fig, use_container_width=True)
    
    # Business insights
    st.markdown("## 💡 Business Intelligence")
    
    subscription_revenue = df[df['Category'] == 'MEMBERSHIP']['Amount Inc Tax'].sum()
    payg_revenue = df[df['Category'] == 'CREDIT_PACK']['Amount Inc Tax'].sum()
    subscription_pct = (subscription_revenue / total_revenue) * 100 if total_revenue > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💳 Subscription Revenue", f"£{subscription_revenue:,.0f}")
    with col2:
        st.metric("💰 Pay-as-you-go Revenue", f"£{payg_revenue:,.0f}")
    with col3:
        st.metric("📊 Subscription %", f"{subscription_pct:.1f}%")
    
    # Key insights
    st.markdown("### 🔍 Key Insights:")
    
    insights = []
    if subscription_pct > 50:
        insights.append("✅ **Strong subscription focus** - You have a solid recurring revenue base")
    else:
        insights.append("📈 **Growth opportunity** - Focus on converting more customers to subscriptions")
    
    if monthly_avg >= target:
        insights.append("🎯 **Monthly target achieved** - Focus on maintaining consistency")
    else:
        insights.append(f"🚀 **Growth needed** - Increase revenue by £{target - monthly_avg:,.0f}/month to hit £6K target")
    
    for insight in insights:
        st.info(insight)

else:
    # Welcome screen
    st.markdown("""
    ## 🎯 Welcome to Your Franchise Analytics Platform
    
    ### Upload your CSV to get instant insights:
    - 📊 **Revenue tracking** vs £6K monthly target
    - 💰 **Business model analysis** (subscriptions vs pay-as-you-go)
    - 🏆 **Product performance** rankings
    - 📈 **Growth recommendations**
    
    **👈 Use the sidebar to upload your monthly CSV file and get started!**
    """)
