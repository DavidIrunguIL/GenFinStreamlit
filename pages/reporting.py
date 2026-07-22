import pandas as pd
import streamlit as st
import plotly.express as px
from data.get_data import get_data as GT

from modules.reporting.insurance_revenue.src.insurance_revenue_class import InsuranceRevenueGenerator
from modules.reporting.insurance_revenue.src.claims import get_claims_data
from modules.reporting.insurance_revenue.input_data import  get_data
from modules.reporting.ifrs_17.revenue_account import main as ifrs_17_main
from modules.reporting.revenue_account.main import consolidate_revenue_account
from style import load_css
# from modules.reporting.ifrs_17.revenue_account import main as ifrs_17_main
import pandas as pd
import numpy as np
from datetime import datetime as dt
import warnings
import logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

####### APP STYLE #########
# Load CSS function
# def local_css(file_name):
#     with open(file_name) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Sales Dashboard", layout="wide")
load_css()    # 🎨 load custom styles

# ================== HEADER ==================
col_logo, col_title = st.columns([1,4])


# ============ DATA ============

st.sidebar.header("Filter Data Here:")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📆 IRA","💲 Insurance Revenue", "📊 Revenue Account"])

with tab1:
    try:
        st.subheader("IRA")
    except Exception as e:
        st.warning(f"Error filling IRA data: {e}")


with tab2:
    st.subheader("Insurance Revenue")
    col1,col2,col3 = st.columns(3)
    with col1:
        try:
            months = list(range(1, 13))
            default_index = (dt.now().month - 2) % 12

            month = st.selectbox(
                "Select Month",
                options=months,
                index=default_index
            )
        except Exception as e:
            st.warning(f"Error selecting month: {e}")

    with col2:
        try:
            year = st.selectbox("Select Year", options=list(range(2020,dt.now().year +1)), index=dt.now().year -2020)
        except Exception as e:
            st.warning(f"Error selecting year: {e}")

    with col3:
        try:
            report_type = st.selectbox("Select Report Type", options=["Both","Insurance_revenue","Claims"], index=0)
            generate_button = st.button("Generate Report")
        except Exception as e:
            st.warning(f"Error selecting report type: {e}")

## Revenue Account Tab
with tab3:
    st.subheader("Revenue Account")
    insu_rev, cur_bel, cur_loss, ifie,expenses  = st.columns(5)

    # --- Data Uploads (Saving raw file objects for the backend) ---
    with insu_rev:
        try:
            insurance_revenue_file = st.file_uploader("Upload Insurance Revenue Output", type=["xlsx", "xls", "csv"])
            if insurance_revenue_file:
                st.info("Insurance Revenue file uploaded successfully.")
                st.session_state['insurance_revenue_output'] = insurance_revenue_file
        except Exception as e:
            st.warning(f"Error uploading insurance_revenue_output: {e}")
            
    with cur_bel:
        try:
            BEL = st.file_uploader("Upload Current BEL", type=["xlsx", "xls", "csv"])
            if BEL:
                st.info("BEL uploaded successfully.")
                st.session_state['bel_data'] = BEL
        except Exception as e:
            st.warning(f"Error uploading BEL: {e}")

    with cur_loss:
        try:
            CurrentLossComponent = st.file_uploader("Upload Current Loss Component", type=["xlsx", "xls", "csv"])
            if CurrentLossComponent:
                st.info("Current Loss Component uploaded successfully.")
                st.session_state['current_loss_data'] = CurrentLossComponent
        except Exception as e:
            st.warning(f"Error uploading Current Loss Component: {e}")
        

    with ifie:
        try:
            IFIE = st.file_uploader("Upload IFIE", type=["xlsx", "xls", "csv"])
            if IFIE:
                st.info("IFIE uploaded successfully.")
                st.session_state['ifie_data'] = IFIE
        except Exception as e:
            st.warning(f"Error uploading IFIE: {e}")

    # FIXED: Brought expenses out of ifie's indentation block
    with expenses:
        try:
            expenses = st.file_uploader("Upload Expenses", type=["xlsx", "xls", "csv"])
            if expenses:
                st.info("Expenses uploaded successfully.")
                st.session_state['EXPENSE_data'] = expenses
        except Exception as e:
            st.warning(f"Error uploading Expenses: {e}")

    prev_loss, prev_bel, _,_,_  = st.columns(5)
    with prev_bel:
        try:
            prev_BEL = st.file_uploader("Upload Previous BEL", type=["xlsx", "xls", "csv"])
            if prev_BEL:
                st.info("Previous BEL uploaded successfully.")
                st.session_state['prev_bel_data'] = prev_BEL
        except Exception as e:
            st.warning(f"Error uploading Previous BEL: {e}")
    with prev_loss:
        try:
            PreviousLossComponent = st.file_uploader("Upload Previous Loss Component", type=["xlsx", "xls", "csv"])
            if PreviousLossComponent:
                st.info("Previous Loss Component uploaded successfully.")
                st.session_state['previous_loss_data'] = PreviousLossComponent
        except Exception as e:
            st.warning(f"Error uploading Previous Loss Component: {e}")


    # --- Execution Section ---
    st.markdown("---")
    run_rev,run_IRA , _ = st.columns(3)
    run_rev_button = run_rev.button("Run Revenue Account", use_container_width=True)
    
    if run_rev_button:
        try:
            # Fetch raw file objects from session state
            ins_rev_out = st.session_state.get('insurance_revenue_output')
            current_bel = st.session_state.get('bel_data')
            prev_bel = st.session_state.get('prev_bel_data')
            current_loss = st.session_state.get('current_loss_data')
            prev_loss = st.session_state.get('previous_loss_data')
            ifie_data = st.session_state.get('ifie_data')
            expenses_data = st.session_state.get('EXPENSE_data')
            # Note: expenses_data is fetched inside your main via hardcoded path, 
            # but we pass the placeholder fields your main signature requires

            # Check if files are missing
            required_files = [ins_rev_out, current_bel, prev_bel, current_loss, prev_loss, ifie_data]
            if any(file is None for file in required_files):
                st.warning("Please upload all required files before running the Revenue Account.")
            else:
                st.info("Running Revenue Account...")
                consolidate_revenue_account(
                    ins_rev_out,     # passes as claims_data placeholder since main parses it
                    prev_bel, 
                    current_bel, 
                    ins_rev_out,     # insurance_revenue_output
                    current_loss, 
                    prev_loss,
                    expenses_data,
                    ifie_data
                )
                st.success("Revenue Account generated successfully!")
        except Exception as e:
            st.error(f"Error running Revenue Account: {e}")
            logger.error(f"Error running Revenue Account: {e}")


    run_IRA_button = run_IRA.button("Run IRA IFRS17 Forms", use_container_width=True)
    
