import streamlit as st
import pandas as pd
from modules.payables.bank_rec import BankReconciliation


# Page configuration
st.set_page_config(
    page_title="Credit Control",
    page_icon="🔍",
    layout="wide"
)

tab1, tab2, tab3, tab4 = st.tabs(["🔭 Bank Reconciliation","📈 Cashier Conf", "📊 Claims Control", "ℹ️ Unclearing Receipts"])

with tab1:
    # --- Initialize empty dataframes ---
    cashbook_df = pd.DataFrame()
    bank_statement_df = pd.DataFrame()

    # --- Upload section ---
    col1, col2 = st.columns(2)
    cashbook_data = col1.file_uploader("Upload cashbook", type=["xlsx", "xls", "csv"])
    bank_statement = col2.file_uploader("Upload bank statement", type=["xlsx", "xls", "csv"])

    info1, info2 = st.columns(2)
    # --- Load bank statement ---
    if bank_statement:
        bank_statement_df = pd.read_csv(bank_statement) if bank_statement.name.endswith(".csv") else pd.read_excel(bank_statement, header=7)
        info2.info(f"Bank statement uploaded successfully. Records: {len(bank_statement_df)}")
        info2.dataframe(bank_statement_df.head(3))

    # --- Load cashbook ---
    if cashbook_data:
        cashbook_sheets = pd.read_excel(cashbook_data, header=10, sheet_name=None)

        cashbook_ = pd.DataFrame()
        for sheet_name, df in cashbook_sheets.items():
            df['Sheet Name'] = sheet_name
            cashbook_ = pd.concat([cashbook_, df], ignore_index=True)

        info1.info(f"Cashbook uploaded successfully. Records: {len(cashbook_)}")
        info1.dataframe(cashbook_.head(3))

    # 1. Initialize session state keys so they persist across reruns
    if "recon_results" not in st.session_state:
        st.session_state.recon_results = None

    if st.button("Perform Bank Reconciliation"):
        if bank_statement_df.empty or cashbook_.empty:
            st.warning("Please upload both bank statement and cashbook to perform reconciliation.")
        else:
            recon = BankReconciliation(bank_statement_df, cashbook_)
            # Store results directly into session state
            st.session_state.recon_results = recon.bank_reconciliation()
            st.success("Bank reconciliation completed. Here are the results:")

    # 2. Only render the results and action buttons if the reconciliation has been run
    if st.session_state.recon_results is not None:
        results = st.session_state.recon_results

        ### Display summaries of the results 
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Matching Items:", len(results["matching_items"]))
        col2.metric("Unclearing Items:", len(results["unclearing_items"]))
        col3.metric("Unreceipted Items:", len(results["unreceipted_items"]))
        col4.metric("Manual Intervention:", len(results["manual_intervention"]))
        col5.metric("Bounced Cheques:", len(results["bounced_cheques"]))

        output1, output2, output3, output4, output5 = st.tabs([
            "Matching Items", "Unclearing Items", "Unreceipted Items", "Manual Intervention", "Bounced Cheques"
        ])
        
        output1.dataframe(results["matching_items"])
        output2.dataframe(results["unclearing_items"])
        output3.dataframe(results["unreceipted_items"])
        output4.dataframe(results["manual_intervention"])
        output5.dataframe(results["bounced_cheques"])

        #--------
        ### Actions Section
        
        next_step1, next_step2, next_step3, next_step4 = st.columns(4)
        
        # Pro Tip: Using hardcoded local C:/ paths will break if you host this app on a server.
        # Consider using st.download_button for CSV exports in the future!
        next_step1_but = next_step1.button("Export Matching Items")
        if next_step1_but:
            results["matching_items"].to_csv("C:/Users/dkirungu.ICEALIONGROUP/Downloads/matching_items.csv", index=False)
            st.success("Matching items exported successfully as matching_items.csv") 

        next_step2_but = next_step2.button("Export Unclearing Items")
        if next_step2_but:
            results["unclearing_items"].to_csv("C:/Users/dkirungu.ICEALIONGROUP/Downloads/unclearing_items.csv", index=False)
            st.success("Unclearing items exported successfully as unclearing_items.csv")

        next_step3_but = next_step3.button("Share Unreceipted Items to Credit Control")
                # Ensure we have a place to store the edited unreceipted items in session state
        if "edited_unreceipted_df" not in st.session_state:
            st.session_state.edited_unreceipted_df = None

        # Track if the user has clicked the "Share/Prepare" button
        if "show_credit_control_editor" not in st.session_state:
            st.session_state.show_credit_control_editor = False

        # --- Inside your if st.session_state.recon_results is not None: block ---
        results = st.session_state.recon_results

        # ... (your tabs and other buttons remain the same) ...

        next_step3_but = next_step3.button("Prepare Unreceipted Items for Credit Control")
        if next_step3_but:
            # 1. Pull the fresh unreceipted items
            base_df = results["unreceipted_items"].copy()
            
            # 2. Add the columns if they don't already exist
            if "Policy Number" not in base_df.columns:
                base_df["Policy Number"] = ""
            if "Claim Number" not in base_df.columns:
                base_df["Claim Number"] = ""
                
            # 3. Store in session state and open the editor view
            st.session_state.edited_unreceipted_df = base_df
            st.session_state.show_credit_control_editor = True

        # 4. Render the editor OUTSIDE the button conditional so it survives reruns
        if st.session_state.show_credit_control_editor and st.session_state.edited_unreceipted_df is not None:
            st.write("### Edit Unreceipted Items")
            st.caption("Please insert the Policy Number or Claim Number below before exporting.")
            
            # The data editor updates st.session_state directly on every keystroke/change
            st.session_state.edited_unreceipted_df = st.data_editor(
                st.session_state.edited_unreceipted_df,
                key="unreceipted_editor"
            )
            
            # Separate actionable button to export the data
            if st.button("Save & Export to Credit Control"):
                st.session_state.edited_unreceipted_df.to_csv(
                    "C:/Users/dkirungu.ICEALIONGROUP/Downloads/unreceipted_items.csv", 
                    index=False
                )
                st.success("Unreceipted items updated and exported successfully to Downloads!")
                
                # Optional: Reset the view state after a successful save
                st.session_state.show_credit_control_editor = False
                st.rerun()

        next_step4_but = next_step4.button("Review Manual Intervention")
        if next_step4_but:
            # We use a data_editor here; changes will be saved to session state if needed later
            edited_df = st.data_editor(results["manual_intervention"])
            st.success("Manual intervention reviewed.")
                    

                    # ['Claim No_', 'Description', 'Document No_', 'Policy No_', 'Posting Date']