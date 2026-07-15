import pandas as pd
import streamlit as st
import plotly.express as px
from data.get_data import get_data
from modules.login import login
from style import load_css  


load_css()
st.set_page_config(page_title="Access Control Demo", layout="wide")

st.set_page_config(page_title="GenFinance Dashboard", page_icon="🌟", layout="wide")


col_logo, col_title = st.columns([1,4])
# with col_logo:
#     st.image("logo/logo.png", width=80)  # your logo file

# Define your pages. Use the path to your page files.
pages = [
    st.Page("pages/home.py", title="Home", icon="🏠"),
    st.Page("pages/reporting.py", title="Reporting", icon="📊"),
    st.Page("pages/credit_control.py", title="CreditControl", icon="💳"),
    st.Page("pages/treasury.py", title="Treasury", icon="💰"),
    st.Page("pages/reinsurance.py", title="REO", icon="⚖"),
    st.Page("pages/business_partnering.py", title="Finance Business Partnering", icon="🤝"),
]

# Create the navigation menu
selected_page = st.navigation(pages)

# Run the selected page
selected_page.run()