import pandas as pd
import streamlit as st
import plotly.express as px
from data.get_data import get_data
from data.get_remmitances import get_remmitances
from style import load_css
load_css()  # Using Method 2

# ================== HEADER ==================
col_logo, col_title = st.columns([1,4])


# ============ DATA ============

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Underwritting", "📊 Claims", "💲 BD", "📆 Others"])

with tab1:
    st.subheader("Underwritting")

    df = get_data()

    # KPIs
    total_sales = df["Amount"].sum()
    nairobi_sales = df[df["City"]=="Nairobi"]["Amount"].sum()
    mombasa_sales = df[df["City"]=="Mombasa"]["Amount"].sum()

    kpi1, kpi2, kpi3, kpi4,kpi5 = st.columns(5)
    kpi1.metric("Total Sales", f"{total_sales}")
    kpi2.metric("Nairobi Sales", f"{nairobi_sales}")
    kpi3.metric("Mombasa Sales", f"{mombasa_sales}")
    kpi4.metric("Top Fruit", df.groupby("Fruit")["Amount"].sum().idxmax())
    kpi5.metric("Lowest Fruit", df.groupby("Fruit")["Amount"].sum().idxmax())

    # Charts
    fig1 = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group", title="Sales by Fruit & City")
    fig2 = px.pie(df, values="Amount", names="Fruit", title="Fruit Sales Share")

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig1, config={"responsive": True}, use_container_width=True)
    col2.plotly_chart(fig2, config={"responsive": True}, use_container_width=True)

    # Table
    st.subheader("📊 Sales Data Table")
    col1, col2 = st.columns(2)
    col1.dataframe(df, width='stretch')
    col2.dataframe(df.groupby("Fruit").sum().reset_index(), width='stretch')


with tab2:
    cltab1, cltab2, cltab3 = st.tabs( ['Overview','Remmitances', 'TAT'])
    with cltab2:
        # ---- Inputs ----
        claim_no, payee = st.columns(2)
        claim_no_input = claim_no.text_input("Enter Claim No.")
        payee_input = payee.text_input("Enter Payee")

        # ---- Initialize session state ----
        if "remittances" not in st.session_state:
            st.session_state.remittances = pd.DataFrame()

        # ---- Button ----
        if st.button("Submit Input"):
            if not claim_no_input:
                st.info("Insert a valid claim number!")
            else:
                st.session_state.remittances = get_remmitances(
                    claim_no_input, payee_input
                )

        # ---- Display ----
        col1, col2 = st.columns(2)
        col1.dataframe(st.session_state.remittances, use_container_width=True)
        col2.dataframe(st.session_state.remittances, use_container_width=True)
        
