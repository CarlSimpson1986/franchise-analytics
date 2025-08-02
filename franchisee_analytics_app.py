import streamlit as st
import pandas as pd

st.title("🔥 WORKING TEST")
st.write("If you can see this, the app is working!")

st.write("---")
st.write("Testing file upload:")

uploaded_file = st.file_uploader("Upload CSV", type=['csv'])

if uploaded_file is not None:
    st.success("✅ FILE UPLOADED SUCCESSFULLY!")
    df = pd.read_csv(uploaded_file)
    st.write(f"Rows: {len(df)}")
    st.write(f"Columns: {df.columns.tolist()}")
    st.write("First 5 rows:")
    st.dataframe(df.head())
else:
    st.info("👆 Upload a CSV file to test")

st.write("---")
st.write("🎯 If you see this, we can build the full analytics!")
