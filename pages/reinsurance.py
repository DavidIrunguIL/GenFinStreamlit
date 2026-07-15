import streamlit as st
from style import load_css

load_css()  # Using Method 2
st.title("Reinsurance")
st.write("View and generate reports here.")

# Add your report-related content here
st.line_chart([10, 20, 15, 30])