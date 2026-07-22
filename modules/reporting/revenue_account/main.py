from modules.reporting.revenue_account.insurance_service_expenses import IFRS17Processor
# from input_data.get_input_data import read_google_sheet
from modules.reporting.revenue_account.adjusting_indurance_rev import adjusting_ins_revenue

import pandas as pd
import glob
import numpy as np
import logging
import warnings


warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

from datetime import datetime as dt, timedelta
today = dt.now()
current_year = today.year
prev_year = current_year -1
month = today.month - 2
year_month = f"{current_year}{month:02d}"
MONTH = (dt.today() - timedelta(days=30)).strftime('%b')
YEAR = dt.today().year
LAST_MONTH = (dt.today() - timedelta(days=60)).strftime('%b')
print(MONTH)
TAX_RATE = 0.325
PARENT_DIR = f'G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/{YEAR}'


def consolidate_revenue_account(claims_data,prev_bel,current_bel,insurance_revenue_output,
         current_loss_component,prev_loss_component, expenses_data,IFIE_data):
    try:
        print(f"IFRS 17 Processor started for month: {MONTH}")
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger.info("Starting IFRS 17 Processor...")    
        ##############################################################
        def get_bel(bel_path):
            bel = pd.read_excel(bel_path, header=0, usecols="B:H")
            bel["is_dept"] = bel["Unnamed: 1"].str.contains("DEPARTMENT", case=False, na=False)
            bel["group_id"] = bel["is_dept"].cumsum()

            # Split into DataFrames
            dfs = [g.drop(columns=["is_dept","group_id"]).reset_index(drop=True)
                for _, g in bel.groupby("group_id")]

            labels = ['PAA_LIC','REO_AIC','PAA_RISK_ADJUSTMENT','REO_RISK_ADJUSTMENT']

            # Store in dictionary
            named_dfs = {}
            realigned_bel = pd.DataFrame()

            for i, label in enumerate(labels):
                if i < len(dfs):  # safeguard in case labels > dfs
                    df_temp = dfs[i].copy()
                    df_temp.columns = df_temp.iloc[0]                  # set first row as header
                    df_temp = df_temp.drop(df_temp.index[0]).reset_index(drop=True)
                    df_temp = df_temp.dropna(subset=['DEPARTMENT'])    # drop rows missing DEPARTMENT
                    df_temp = df_temp.dropna(axis=1, how='all')        # drop empty columns
                    named_dfs[label] = df_temp
                    df_temp['DEPARTMENT'] = df_temp['DEPARTMENT'].str.upper()
                    df_temp['DEPARTMENT'] = df_temp['DEPARTMENT'].replace({
                                'MISCELLANEOUS': 'MISCELLANEOUS ACCIDENT',
                            })

                    if realigned_bel.empty:
                        realigned_bel = df_temp.copy()
                    else:
                        realigned_bel = realigned_bel.merge(df_temp, on='DEPARTMENT', how='outer')
            return realigned_bel
        
        prev_bel_df = get_bel(prev_bel)
        current_bel_df = get_bel(current_bel)
        def get_claims_incured(claims_data,prev_bel_df,current_bel_df):
            prev_lic = prev_bel_df[['DEPARTMENT', 'DISCOUNTED GROSS BEL LIC','DISCOUNTED REO BEL LIC']]
            curr_lic = current_bel_df[['DEPARTMENT', 'DISCOUNTED GROSS BEL LIC','DISCOUNTED REO BEL LIC']]
            claims_data['Department'] = claims_data['Department'].str.strip()
            prev_lic['DEPARTMENT'] = prev_lic['DEPARTMENT'].str.strip()
            curr_lic['DEPARTMENT'] = curr_lic['DEPARTMENT'].str.strip()
            claims_prev_lic1 = claims_data.merge(prev_lic, left_on='Department', right_on='DEPARTMENT', how='left')
            claims_prev_lic = claims_prev_lic1.merge(curr_lic, on='DEPARTMENT', how='left', suffixes=('_prev', '_curr'))
            claims_prev_lic['ReoIncurred'] = -claims_prev_lic['DISCOUNTED GROSS BEL LIC_prev'] +\
                                        claims_prev_lic['total_reo_paid'] +\
                                        claims_prev_lic['DISCOUNTED GROSS BEL LIC_curr']

            claims_prev_lic['ReoIncurred'] = -claims_prev_lic['DISCOUNTED REO BEL LIC_prev'] +\
                                        claims_prev_lic['total_reo_paid'] +\
                                        claims_prev_lic['DISCOUNTED REO BEL LIC_curr']

            claims_prev_lic['Gross Incurred'] = -claims_prev_lic['DISCOUNTED GROSS BEL LIC_prev'] +\
                                        claims_prev_lic['total_gross_paid'] +\
                                        claims_prev_lic['DISCOUNTED GROSS BEL LIC_curr']
            # claims_prev_lic.to_excel('C:/Users/dkirungu.ICEALIONGROUP/Downloads/IncuredClaims.xlsx', index = False)

            claims_incured = claims_prev_lic[['DEPARTMENT','ReoIncurred','Gross Incurred']]
            claims_incured["DEPARTMENT"] = claims_incured["DEPARTMENT"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            claims_incured.rename(columns={'DEPARTMENT':'Class of Insurance Business'}, inplace=True)

            return claims_incured

        #########################################################################################
        try:
            
            def get_insurance_revenue(insurance_revenue_output):
                insurance_rev_output = pd.read_excel(insurance_revenue_output, sheet_name=None)
                return insurance_rev_output['claims_data'], insurance_rev_output['insurance_revenue']
        
            revenue_data = get_insurance_revenue(insurance_revenue_output)
            ###############################################################################
            claims_data = revenue_data[0]
            revenue_data = adjusting_ins_revenue(revenue_data[1] , current_year,prev_year)
            revenue_data.to_excel('G:/Shared drives/ACCOUNT_GENERAL/FINANCE_WEBAPP_OUTPUT/reporting/adjusted_insurance_revenue_.xlsx', index=False)
            revenue_data['Department'] = revenue_data['Department'].str.strip()
            revenue_data["Department"] = revenue_data["Department"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            ##claims
            incured_claim_data = get_claims_incured(claims_data, prev_bel_df, current_bel_df)
            # incured_claim_data.to_excel('C:/Users/dkirungu.ICEALIONGROUP/Downloads/incured_claims.xlsx', index=False)


            realigned_bel = current_bel_df.copy()
            prev_realigned_bel = prev_bel_df.copy()
        
            #################################################################################
            def read_loss_component(loss_component_dir):
                current_loss_component = pd.read_excel(loss_component_dir, header=1)
                return current_loss_component
            
            
            current_loss_component = read_loss_component(current_loss_component)     
            prev_loss_component = read_loss_component(prev_loss_component)


            #############################################################################
            def read_ifie(ifie_data):
                IFIE_data = pd.read_excel(ifie_data, header=3,
                                        sheet_name='Results')
                return IFIE_data
            
            IFIE_data = read_ifie(IFIE_data)    
            IFIE_data.rename(columns={'PUBLIC LIABILITY':'LIABILITIES',
                                    'MISCELLANEOUS ACCIDENT':'MISCELLANEOUS'}, inplace=True)
            ######################################################################################
            def read_expenses(expenses_data):
                # Try with MONTH
                # files = glob.glob(f"{PARENT_DIR}/EXPENSE PORTFOLIO/{MONTH}*/*Expense*")
                # if files:  # Found files
                #     file_path = files[0]
                # else:  # Fallback to LAST_MONTH
                #     files = glob.glob(f"{PARENT_DIR}/EXPENSE PORTFOLIO/{LAST_MONTH}*/*Expense*")
                #     if not files:
                #         raise FileNotFoundError(f"No EXPENSE file found for {MONTH} or {LAST_MONTH}")
                #     file_path = files[0]

                expenses_data = pd.read_excel(expenses_data, 
                                        sheet_name='PER PORTIFOLIO')
                logger.info(f"SUCCCESSFULLY EXTRACTED EXPENSE PORTFOLIO")
                return expenses_data
            
            expenses_data = read_expenses(expenses_data)    
            logger.info(f"successfully read EXPENSE data.")              
            
                
            expenses_data.rename(columns={"Liability":"Liabilities",
                                        "Workmen's Compensation":"Workmens Compensation"
                                        }, inplace=True)
            logger.info("successfully read expenses data.")


            ###########################################################################################
            def read_P_and_L(PARENT_DIR, MONTH, LAST_MONTH):
                # Try with MONTH
                files = glob.glob(f"{PARENT_DIR}/PROFIT AND LOSS/{MONTH}*/*")
                if files:  # Found files
                    file_path = files[0]
                else:  # Fallback to LAST_MONTH
                    files = glob.glob(f"{PARENT_DIR}/PROFIT AND LOSS/{LAST_MONTH}*/*")
                    if not files:
                        raise FileNotFoundError(f"No P&L file found for {MONTH} or {LAST_MONTH}")
                    file_path = files[0]

                p_and_L = pd.read_excel(file_path,
                                        header=5)
                p_and_L.rename(columns={'Unnamed: 1':'variable',
                            2026:'Actual 2026',
                            2025:'Actual 2025'}, inplace=True)
                return p_and_L[['variable','Actual 2026','Actual 2025']]
            
            p_and_L = read_P_and_L(PARENT_DIR, MONTH, LAST_MONTH)    
            logger.info("successfully read P&L data.") 


            p_and_L.columns = p_and_L.columns.str.strip()
            # p_and_L.drop(columns=['Unnamed: 0'], inplace=True)
            # p_and_L.rename(columns={'Unnamed: 1':'variable'}, inplace=True)
            p_and_L['variable'] = p_and_L['variable'].str.rstrip()
            p_and_L.index = p_and_L['variable']
            

            processor = IFRS17Processor(revenue_data, incured_claim_data, realigned_bel,prev_realigned_bel, current_loss_component, prev_loss_component,expenses_data,IFIE_data)
            final_template = processor.update_revenue_account_template()
            final_template_with_REO = processor.update_reinsurance_section(final_template)
            YTD_Apr_2025 = final_template_with_REO.iloc[:13].sum()
            final_template_with_REO.loc[f'YTD_{MONTH}_2026'] = YTD_Apr_2025
            try:
                logger.info(f"Updating the P&L variables in the revenue accounts")
                final_template_with_REO.at[f'YTD_{MONTH}_2026', 'Investment income'] = p_and_L.at['Investment & other income','Actual 2026']
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Net Investment and Finance Income/Expenses'] =  final_template_with_REO.at[f'YTD_{MONTH}_2026','IFIE_PAA_TOTAL'] +\
                                                                                                                final_template_with_REO.at[f'YTD_{MONTH}_2026','IFIE_REO_TOTAL'] +\
                                                                                                                final_template_with_REO.at[f'YTD_{MONTH}_2026','Investment income'] 
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Non Attributable Expenses']  = p_and_L.at['Marketing, Communication, R &D& Customer Service Expenses','Actual 2026'] + \
                                                                                                                p_and_L.at['Investment Expenses','Actual 2026'] + \
                                                                                                                p_and_L.at['Other Costs','Actual 2026']
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Profit before income tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2026','Insurance service result'] +\
                                                                                                                final_template_with_REO.at[f'YTD_{MONTH}_2026','Net Investment and Finance Income/Expenses'] +\
                                                                                                                final_template_with_REO.at[f'YTD_{MONTH}_2026','Non Attributable Expenses']
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Income tax expense '] = -final_template_with_REO.at[f'YTD_{MONTH}_2026','Profit before income tax']*TAX_RATE
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Profit After Tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2026','Profit before income tax'] + \
                                                                                        final_template_with_REO.at[f'YTD_{MONTH}_2026','Income tax expense ']
                final_template_with_REO.at[f'YTD_{MONTH}_2026', 'Other comprehensive income'] = p_and_L.at['Other comprehensive income','Actual 2026']
                final_template_with_REO.at[f'YTD_{MONTH}_2026','Total Comprehensive Income After Tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2026','Profit After Tax'] + \
                                                                                        final_template_with_REO.at[f'YTD_{MONTH}_2026','Other comprehensive income']
            except Exception as e:
                logger.error(f'Error updating P&L variables::{e}')

            # final_template_with_REO['YTD_Apr_2025'] = final_template_with_REO.iloc[:13].sum(numeric_only=True)
            final_template_with_REO.T.to_excel(f"G:/Shared drives/ACCOUNT_GENERAL/FINANCE_WEBAPP_OUTPUT/reporting/IFRS17_Automated_Output.xlsx", index=True)
            logger.info("IFRS 17 Revenue Account Template created successfully.")
        except Exception as e:
            logger.error(f"Error in main function: {e}")

    except Exception as e:
        logger.error(f"Error in Generating Revenue Account:: {e}")
