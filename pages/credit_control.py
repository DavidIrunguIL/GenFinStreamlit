import streamlit as st
import pandas as pd
import plotly.express as px
from modules.credit_control.reconciliation import broker_reconciliation_v1


# Page configuration
st.set_page_config(
    page_title="Credit Control",
    page_icon="🔍",
    layout="wide"
)

tab1, tab2, tab3, tab4 = st.tabs(["🔭 Reconcile","📈 Aging Reports", "📊 Broker Profile & Debtors Listing", "ℹ️ Allocation Report"])

with tab1:
    # --- Initialize empty dataframes ---
    df_broker = pd.DataFrame()
    df_icea = pd.DataFrame()

    # --- Upload section ---
    col1, col2 = st.columns(2)
    broker_schedule = col1.file_uploader("Upload Broker Schedule", type=["xlsx", "xls", "csv"])
    icea_statement = col2.file_uploader("Upload ICEALION Statement", type=["xlsx", "xls", "csv"])

    info1, info2 = st.columns(2)

    # --- Load ICEA ---
    if icea_statement:
        df_icea = pd.read_csv(icea_statement) if icea_statement.name.endswith(".csv") else pd.read_excel(icea_statement)
        info2.info(f"ICEA file uploaded successfully. Records: {len(df_icea)}")
        info2.dataframe(df_icea.head(3))

    # --- Load Broker ---
    if broker_schedule:
        df_broker = pd.read_csv(broker_schedule) if broker_schedule.name.endswith(".csv") else pd.read_excel(broker_schedule)
        info1.info(f"Broker file uploaded successfully. Records: {len(df_broker)}")
        info1.dataframe(df_broker.head(3))

    required_cols = ['risk_note', 'net_amount', 'gross_amount', 'Insured_name']
    optional_cols = ['start_date', 'end_date']
    all_cols = required_cols + optional_cols

    st.write("### 🧩 Column Mapping")

    broker_col, icea_col = st.columns(2)

    # ======================  BROKER MAPPING  ======================
    with broker_col:
        st.subheader("Broker Mapping")

        broker_mapping = {
            req: st.selectbox(
                f"Map **{req}** {'(optional)' if req in optional_cols else ''}",
                options=[None] + list(df_broker.columns) if not df_broker.empty else [None],
                key=f"broker_{req}"
            )
            for req in all_cols
        }

        if st.button("Apply Broker Mapping"):
            missing_required = [col for col in required_cols if broker_mapping[col] is None]

            if missing_required:
                st.error(f"Please map these required fields: {missing_required}")
            else:
                rename_dict = {v: k for k, v in broker_mapping.items() if v is not None}
                st.session_state["brk_mapped_df"] = df_broker.rename(columns=rename_dict).copy()
                st.success("Broker mapping applied!")
                # st.dataframe(st.session_state["brk_mapped_df"].head())

    # ======================  ICEA MAPPING  ======================
    with icea_col:
        st.subheader("ICEA Mapping")

        icea_mapping = {
            req: st.selectbox(
                f"Map **{req}** {'(optional)' if req in optional_cols else ''}",
                options=[None] + list(df_icea.columns) if not df_icea.empty else [None],
                key=f"icea_{req}"
            )
            for req in all_cols
        }

        if st.button("Apply ICEA Mapping"):
            missing_required = [col for col in required_cols if icea_mapping[col] is None]

            if missing_required:
                st.error(f"Please map these required fields: {missing_required}")
            else:
                rename_dict = {v: k for k, v in icea_mapping.items() if v is not None}
                st.session_state["icea_mapped_df"] = df_icea.rename(columns=rename_dict).copy()
                st.success("ICEA mapping applied!")
                # st.dataframe(st.session_state["icea_mapped_df"].head())

    # ======================  RECONCILIATION  ======================
    reconcile, allocate = st.tabs(['Reconcile', 'Allocate'])

    with reconcile:
        st.write("### 🔄 Reconciliation Options")
        
        colA, colB = st.columns(2)
        recon_butt = colA.button("Reconcile on Net Amount", key="on_net", use_container_width=True)
        gross_butt = colB.button("Reconcile on Gross Amount", key="on_gross", use_container_width=True)

        if recon_butt or gross_butt:
            # Validate session state
            if "brk_mapped_df" not in st.session_state or "icea_mapped_df" not in st.session_state:
                st.error("Please complete BOTH mappings before reconciliation.")
            else:
                # Show loading spinner
                with st.spinner("Reconciling records... This may take a few moments."):
                    # Perform reconciliation
                    use_gross = gross_butt  # True if gross button was clicked
                    st.session_state["recon_result"] = broker_reconciliation_v1(
                        st.session_state["brk_mapped_df"],
                        st.session_state["icea_mapped_df"],
                        use_gross=use_gross
                    )
                
                st.success("Reconciliation completed!")

        # Display results if available
        if "recon_result" in st.session_state:
            recon_df, unrecon_df = st.session_state["recon_result"]
            
            # Calculate metrics
            total_records = len(st.session_state["brk_mapped_df"])
            reconciled_count = len(recon_df)
            unreconciled_count = len(unrecon_df)
            reconciliation_rate = (reconciled_count / total_records) * 100 if total_records > 0 else 0

            # Display metrics
            st.write("### 📊 Reconciliation Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Records", total_records)
            col2.metric("Reconciled", f"{reconciled_count} ({reconciliation_rate:.1f}%)")
            col3.metric("Unreconciled", unreconciled_count)

            # Display results in tabs
            result_tab1, result_tab2 = st.tabs(["✅ Reconciled Items", "❌ Unreconciled Items"])
            
            with result_tab1:
                st.write(f"**Reconciled Records ({len(recon_df)})**")
                if not recon_df.empty:
                    # Show important columns
                    display_cols = ['risk_note', 'Insured_name', 'amount_broker', 'amount_icea', 
                                  'amount_diff', 'merged_on', 'fuzzy_score_rn', 'fuzzy_score_name']
                    available_cols = [col for col in display_cols if col in recon_df.columns]

                    st.dataframe(recon_df)
                    
                    # Download button for reconciled data
                    csv = recon_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Reconciled Data",
                        data=csv,
                        file_name="reconciled_records.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No reconciled records found.")
            
            with result_tab2:
                st.write(f"**Unreconciled Records ({len(unrecon_df)})**")
                if not unrecon_df.empty:
                    st.dataframe(unrecon_df)
                    
                    # Download button for unreconciled data
                    csv = unrecon_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Unreconciled Data",
                        data=csv,
                        file_name="unreconciled_records.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("All records were reconciled! 🎉")

    with allocate:
        st.write("### 💰 Allocation")
        st.info("Allocation features will be implemented here.")
        # Add allocation logic here when needed

# For the other tabs, you can add content later
with tab2:
    st.write("## Aging Reports")
    st.info("Aging reports will be displayed here.")
    

with tab3:
    st.write("### 📊 Broker Health & Debtors Listing")
    
    # 1. Check if data is already available via the reconciliation engine or read globally
    # For standalone test stability, we gracefully read 'icea_mapped_df' or fall back to your source file
    if "icea_mapped_df" in st.session_state:
        score_df = st.session_state["icea_mapped_df"]
    else:
        # Mocking or loading a default dataset if nothing has been uploaded yet in Tab 1
        try:
            score_df = pd.read_excel("C:/Users/dkirungu.ICEALIONGROUP/Documents/finance/credit_control/CustomerMapping/data/post_modeling_data.xlsx")
        except:
            st.warning("⚠️ Please upload and map your ICEA Statement in the 'Reconcile' tab to see live calculations, or ensure 'your_data.csv' is in your workspace.")
            st.stop()

    # Clean missing financial values safely
    financial_cols = ['basicprem', 'claims_incured', 'debt_amount']
    for col in financial_cols:
        if col in score_df.columns:
            score_df[col] = score_df[col].fillna(0)

    # 2. SIDEBAR FILTER OVERLAY (Scoped elegantly just for this tab layout context)
    st.markdown("---")
    
    # Customer/Client Filter
    if "brkaccount" in score_df.columns:
        client_options = ["📊 All Portfolio Profiles"] + sorted(list(score_df["brkaccount"].dropna().unique()))
        cust_d1, cust_d2 = st.columns(2)
        selected_client = cust_d1.selectbox("🎯 Select Customer Number", options=client_options)
        select_name = cust_d2.selectbox("🔍 Search by Customer Name", options=["All"] + sorted(list(score_df["brkname"].dropna().unique())) if "brkname" in score_df.columns else ["All"])
    else:
        st.error("The column 'brkaccount' was not found in the dataset.")
        st.stop()

    st.markdown("---")

    # ==================== VIEW A: ALL PORTFOLIO PORTFOLIO / SUMMARIES ====================
    if selected_client == "📊 All Portfolio Profiles":
        st.write("📋 Macro Portfolio & Risk Profile Summaries")

        # Top-level KPI Aggregations
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Clients", f"{score_df['brkaccount'].nunique():,}")
        if 'basicprem' in score_df.columns: m2.metric("Total Premiums", f"Kes: {score_df['basicprem'].sum():,.0f}")
        if 'claims_incured' in score_df.columns: m3.metric("Total Incurred Claims", f"Kes: {score_df['claims_incured'].sum():,.0f}")
        if 'debt_amount' in score_df.columns: m4.metric("Total Outstanding Debt", f"Kes: {score_df['debt_amount'].sum():,.0f}")

        st.markdown("### 🔍 Typical Profile Segmentation")
        
        # Build Profile Cards Aggregated Dynamic Matrix by Segment Column
        if 'segment' in score_df.columns:
            profile_summary = score_df.groupby("segment").agg(
                avg_overall=("overall_score", "mean") if "overall_score" in score_df.columns else ("brkaccount", "count"),
                avg_debt_score=("debt_score", "mean") if "debt_score" in score_df.columns else ("brkaccount", "count"),
                avg_claims_score=("claims_score", "mean") if "claims_score" in score_df.columns else ("brkaccount", "count"),
                total_debt=("debt_amount", "sum"),
                client_count=("brkaccount", "nunique")
            ).reset_index()

            # Dynamic Horizontal Columns layout generation matching your unique data clusters
            seg_cols = st.columns(len(profile_summary))
            for idx, row in profile_summary.iterrows():
                with seg_cols[idx]:
                    st.info(f"🧬 **Profile: {row['segment']}**")
                    st.write(f"• **Clients:** {int(row['client_count']):,}")
                    if "overall_score" in score_df.columns: st.write(f"• **Avg Score:** `{row['avg_overall']:.1f}`")
                    if "debt_score" in score_df.columns: st.write(f"• **Debt Score:** `{row['avg_debt_score']:.1f}`")
                    if "claims_score" in score_df.columns: st.write(f"• **Claims Score:** `{row['avg_claims_score']:.1f}`")
                    st.write(f"• **Debt Exposure:** Kes: {row['total_debt']:,.2f}")
        else:
            st.warning("The field 'segment' column is missing from the data layout structure.")

        # Analytical Matrix Plots
        st.markdown("### 📈 Portfolio Risk Distributions")
        g1, g2, g3 = st.columns(3)
        
        with g1:
            if "overall_score" in score_df.columns and "segment" in score_df.columns:
                fig_box = px.box(
                    score_df, 
                    x="segment", 
                    y="overall_score", 
                    color="segment",
                    title="Overall Risk Score Variance Across Profiles", 
                    points="all",
                    # Force explicit high-contrast mapping
                    color_discrete_map={
                        "High Risk": "#D32F2F",    # Deep Crimson Red
                        "Medium Risk": "#FBC02D",  # Vivid Amber Yellow
                        "Low Risk": "#388E3C"      # Rich Emerald Green
                    }
                )
                
                # Optional styling polish: make the box outlines crisper
                fig_box.update_traces(marker=dict(line=dict(width=1, color='Black')))
                
                st.plotly_chart(fig_box, use_container_width=True)
        with g2:
            if "basicprem" in score_df.columns and "claims_incured" in score_df.columns:
                fig_scat = px.scatter(score_df, x="basicprem", y="claims_incured", color="segment" if "segment" in score_df.columns else None,
                                      size="debt_amount" if "debt_amount" in score_df.columns else None,
                                      hover_data=["brkaccount", "Name"] if "Name" in score_df.columns else ["brkaccount"],
                                      title="Revenue vs Loss Position Profile Scatter")
                st.plotly_chart(fig_scat, use_container_width=True)
        
        with g3:
            current_score = float(score_df['overall_score'].iloc[0]) if 'overall_score' in score_df.columns else 0.0
            # Build the dynamic colorful Plotly Gauge
            fig_gauge = px.indicators.go.Figure(px.indicators.go.Indicator(
                mode = "gauge+number",
                value = current_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Overall Risk Score Index", 'font': {'size': 18}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"}, # Adjust range (e.g. 0-100 or 300-850) based on your model scale
                    'bar': {'color': "#3A3B3C"}, # Gauge needle pointer line color
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 40], 'color': '#EF553B'},    # Red - High Risk zone
                        {'range': [40, 70], 'color': '#FECB52'},   # Yellow - Medium Risk zone
                        {'range': [70, 100], 'color': '#00CC96'}   # Green - Low Risk zone
                    ],
                }
            ))
            
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

    # ==================== VIEW B: DETAILED CUSTOMER DRILLDOWN ====================
    else:
        client_records = score_df[score_df["brkaccount"] == selected_client]
        
        # Sort values securely on historical timeline anchors
        time_col = "UwYear" if "UwYear" in client_records.columns else ("DebtYear" if "DebtYear" in client_records.columns else "ClaimYear")
        if time_col in client_records.columns:
            client_records = client_records.sort_values(time_col)
            
        latest_record = client_records.iloc[-1]

        cust_title = latest_record['Name'] if "Name" in latest_record else f"Client {selected_client}"
        st.write(f"👤 Risk Profile Analysis: {cust_title}")
        
        # Grid Matrix Scores Layout
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Overall Score Index", f"{latest_record.get('overall_score', 0.0):.1f}")
        s2.metric("Premium Score Status", f"{latest_record.get('premium_score', 0.0):.1f}")
        s3.metric("Claims Friction Score", f"{latest_record.get('claims_score', 0.0):.1f}")
        s4.metric("Debt Collection Score", f"{latest_record.get('debt_score', 0.0):.1f}")

        st.markdown("---")
        st.write("📊 Trends & Context Comparisons")
        c1, c2 = st.columns(2)

        with c1:
            # Generate trend tracking graph lines across available underwriting/accounting intervals
            if time_col in client_records.columns:
                trend_metrics = [m for m in ['basicprem', 'claims_incured', 'debt_amount'] if m in client_records.columns]
                yearly_data = client_records.groupby(time_col)[trend_metrics].sum().reset_index()
                
                fig_line = px.line(yearly_data, x=time_col, y=trend_metrics, markers=True,
                                   title=f"Financial Exposure Curve Over Years ({time_col})")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No time-series attributes found (UwYear/DebtYear) to generate trend lines.")

        with c2:
            # Context Comparison Component Matrix: Customer Scores versus Segment baseline averages
            if "segment" in latest_record and "overall_score" in score_df.columns:
                seg_avg = score_df[score_df["segment"] == latest_record["segment"]][["overall_score", "premium_score", "claims_score", "debt_score"]].mean()
                
                compare_df = pd.DataFrame({
                    "Dimension": ["Overall", "Premium", "Claims", "Debt"],
                    "Selected Client": [latest_record.get("overall_score", 0), latest_record.get("premium_score", 0), latest_record.get("claims_score", 0), latest_record.get("debt_score", 0)],
                    "Segment Benchmark": [seg_avg.get("overall_score", 0), seg_avg.get("premium_score", 0), seg_avg.get("claims_score", 0), seg_avg.get("debt_score", 0)]
                })
                
                fig_bar = px.bar(
                    compare_df, 
                    x="Dimension", 
                    y=["Selected Client", "Segment Benchmark"], 
                    barmode="group",
                    title=f"Client Vector Evaluation vs. {latest_record['segment']} Baseline Cluster",
                    # Force precise color contrast on the legend dimensions
                    color_discrete_map={
                        "Selected Client": "#B4581F",     # Sharp, bright electric blue
                        "Segment Benchmark": "#2828DE"   # High-contrast light silver/grey
                    }
                )
                
                # Optional styling polish to make the edges of the bars clean and distinct
                fig_bar.update_traces(marker=dict(line=dict(width=1, color='black')))
                
                st.plotly_chart(fig_bar, use_container_width=True)

        # Expandable Detailed Data Frame Ledger View
        with st.expander("📄 View Customer Accounting Ledger Sub-Records"):
            st.dataframe(client_records)

with tab4:
    st.write("## Allocation Report")
    st.info("Allocation reports will be displayed here.")