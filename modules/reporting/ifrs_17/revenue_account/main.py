from .input_data.get_input_data import read_google_sheet
from .src.adjusting_indurance_rev import adjusting_ins_revenue
from .insurance_service_expenses import IFRS17Processor

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
month = today.month - 1
year_month = f"{current_year}{month:02d}"
MONTH = (dt.today() - timedelta(days=30)).strftime('%b')
YEAR = dt.today().year
LAST_MONTH = (dt.today() - timedelta(days=60)).strftime('%b')
print(MONTH)
TAX_RATE = 0.325
# COMMON_FOLDER = 'G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/MANAGEMENT ACCOUNTS/2025/KENYA/MANAGEMENT ACCOUNTS/IFRS17/Quarter 2/June 2025'
# FILE_DIR = f'input_data/IFRS 17 JULY 2025 TEMPLATE Revenue account and Balance sheet- updated BELL & LC - 13.08.2025.xlsx'
PARENT_DIR = f'G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/{YEAR}'
def main():
    print(f"IFRS 17 Processor started for month: {MONTH}")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting IFRS 17 Processor...")    
    ##############################################################
        
    def get_bel(year,MONTH, LAST_MONTH):
        try:
            files = glob.glob(f"G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/{year}/BEL/{MONTH}*/*ICEA*.xlsx")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/{year}/BEL/{LAST_MONTH}*/*ICEA*.xlsx")
                if not files:
                    raise FileNotFoundError(f"No BEL file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]
            bel = pd.read_excel(file_path, header=0, usecols="B:H")
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
        except Exception as e:
            bel = pd.DataFrame()
            logger.error(f"Error getting BEL data: {e}")
            return bel
    # current_year_path = glob.glob(f"G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/{current_year}/BEL/{MONTH}*/*BEL*.xlsx")
    # prev_bel_path = f"G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/2024/BEL/DEC 2024/ICEA LION Kenya_2024_BE LIC Results_RA@99th_13022025 (1).xlsx"
    try:
        current_bel = get_bel(current_year,MONTH, LAST_MONTH)
        prev_bel = get_bel(prev_year,'Dec', LAST_MONTH)
    except Exception as e:
        current_bel = pd.DataFrame()
        prev_bel = pd.DataFrame()
        logger.error(f"Error reading BEL data: {e}")
    ######################################################################################
    def get_claims_incured(claims_data,prev_bel,current_bel):
        try:
            prev_lic = prev_bel[['DEPARTMENT', 'DISCOUNTED GROSS BEL LIC','DISCOUNTED REO BEL AIC']]
            curr_lic = current_bel[['DEPARTMENT', 'DISCOUNTED GROSS BEL LIC','DISCOUNTED REO BEL LIC']]
            claims_data['Department'] = claims_data['Department'].str.strip()
            prev_lic['DEPARTMENT'] = prev_lic['DEPARTMENT'].str.strip()
            curr_lic['DEPARTMENT'] = curr_lic['DEPARTMENT'].str.strip()
            claims_prev_lic1 = claims_data.merge(prev_lic, left_on='Department', right_on='DEPARTMENT', how='left')
            claims_prev_lic = claims_prev_lic1.merge(curr_lic, on='DEPARTMENT', how='left', suffixes=('_prev', '_curr'))
            claims_prev_lic['ReoIncurred'] = -claims_prev_lic['DISCOUNTED GROSS BEL LIC_prev'] +\
                                        claims_prev_lic['total_reo_paid'] +\
                                        claims_prev_lic['DISCOUNTED GROSS BEL LIC_curr']

            claims_prev_lic['ReoIncurred'] = -claims_prev_lic['DISCOUNTED REO BEL AIC'] +\
                                        claims_prev_lic['total_reo_paid'] +\
                                        claims_prev_lic['DISCOUNTED REO BEL LIC']

            claims_prev_lic['Gross Incurred'] = -claims_prev_lic['DISCOUNTED GROSS BEL LIC_prev'] +\
                                        claims_prev_lic['total_gross_paid'] +\
                                        claims_prev_lic['DISCOUNTED GROSS BEL LIC_curr']
            # claims_prev_lic.to_excel('IncuredClaims.xlsx', index = False)

            claims_incured = claims_prev_lic[['DEPARTMENT','ReoIncurred','Gross Incurred']]
            claims_incured["DEPARTMENT"] = claims_incured["DEPARTMENT"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            claims_incured.rename(columns={'DEPARTMENT':'Class of Insurance Business'}, inplace=True)

            return claims_incured
        except Exception as e:
            claims_incured = pd.DataFrame()
            logger.error(f"Error calculating claims incurred: {e}") 
            return claims_incured

    #########################################################################################
    try:
        
        def get_insurance_revenue(PARENT_DIR, MONTH, LAST_MONTH):
            # Try with MONTH
            files = glob.glob(f"{PARENT_DIR}/INSURANCE REVENUE/{MONTH}*/insurance_revenue*.xlsx")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"{PARENT_DIR}/INSURANCE REVENUE/{LAST_MONTH}*/insurance_revenue*.xlsx")
                if not files:
                    raise FileNotFoundError(f"No INSURANCE REVENUE file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]

            insurance_rev_output = pd.read_excel(file_path, sheet_name=None)
            logger.info(f"SUCCCESSFULLY EXTRACTED INSURANCE REVENUE")
            return insurance_rev_output['claims_data'], insurance_rev_output['insurance_revenue']
        
        # revenue_output = pd.read_excel("G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/2025/INSURANCE REVENUE/Sept 2025/insurance_revenue_amortize_aq_cost_202509.xlsx", sheet_name=None)

        revenue_data = get_insurance_revenue(PARENT_DIR, MONTH, LAST_MONTH)
        claims_data = revenue_data[0]
        revenue_data = adjusting_ins_revenue(revenue_data[1] , current_year,prev_year)
        # revenue_data.to_excel('output_data/adjusted_insurance_revenue_.xlsx', index=False)

        revenue_data['Department'] = revenue_data['Department'].str.strip()
        revenue_data["Department"] = revenue_data["Department"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
        incured_claim_data = get_claims_incured(claims_data, prev_bel, current_bel) 
        # incured_claim_data.to_excel('input_data/incured_claims.xlsx', index=False)


        realigned_bel = current_bel.copy()
        prev_realigned_bel = prev_bel.copy()
        
        logger.info("successfully read revenue BEL and incurred claims data.")

        def read_loss_component(PARENT_DIR, MONTH, LAST_MONTH):
            # Try with MONTH
            files = glob.glob(f"{PARENT_DIR}/LOSS COMPONENT/{MONTH}*/*Loss Comp*")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"{PARENT_DIR}/LOSS COMPONENT/{LAST_MONTH}*/*Loss Comp*")
                if not files:
                    raise FileNotFoundError(f"No Loss Component file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]

            current_loss_component = pd.read_excel(file_path, header=1)
            return current_loss_component
        
        current_loss_component = read_loss_component(PARENT_DIR, MONTH, LAST_MONTH)     
        logger.info("successfully read current loss component data.")

        prev_loss_component = pd.read_excel(f"G:/Shared drives/ACCOUNTS - GENERAL BUSINESS/REVENUE_DATASETS/2024/LOSS COMPONENT/DEC 2024/ICEA LION Kenya_2024_Loss Component_25022025  final.xlsx",header=1) 

        logger.info("successfully read previous loss component data.")



        def read_ifie(PARENT_DIR, MONTH, LAST_MONTH):
            # Try with MONTH
            files = glob.glob(f"{PARENT_DIR}/IFIE/{MONTH}*/*IFIE*")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"{PARENT_DIR}/IFIE/{LAST_MONTH}*/*IFIE*")
                if not files:
                    raise FileNotFoundError(f"No IFIE file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]

            IFIE_data = pd.read_excel(file_path, header=3,
                                    sheet_name='Results')
            return IFIE_data
        
        IFIE_data = read_ifie(PARENT_DIR, MONTH, LAST_MONTH)    
        logger.info("successfully read IFIE data.")

        IFIE_data.rename(columns={'PUBLIC LIABILITY':'LIABILITIES',
                                  'MISCELLANEOUS ACCIDENT':'MISCELLANEOUS'}, inplace=True)

        def read_expenses(PARENT_DIR, MONTH, LAST_MONTH):
            # Try with MONTH
            files = glob.glob(f"{PARENT_DIR}/EXPENSE PORTFOLIO/{MONTH}*/*Expense*")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"{PARENT_DIR}/EXPENSE PORTFOLIO/{LAST_MONTH}*/*Expense*")
                if not files:
                    raise FileNotFoundError(f"No EXPENSE file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]

            expenses_data = pd.read_excel(file_path, 
                                    sheet_name='PER PORTIFOLIO')
            return expenses_data
        
        expenses_data = read_expenses(PARENT_DIR, MONTH, LAST_MONTH)    
        logger.info(f"successfully read EXPENSE data.")              
        
            
        expenses_data.rename(columns={"Liability":"Liabilities",
                                      "Workmen's Compensation":"Workmens Compensation"
                                      }, inplace=True)
        logger.info("successfully read expenses data.")


    
        def read_P_and_L(PARENT_DIR, MONTH, LAST_MONTH):
            # Try with MONTH
            files = glob.glob(f"{PARENT_DIR}/PROFIT AND LOSS/{MONTH}*/*Profit*")
            if files:  # Found files
                file_path = files[0]
            else:  # Fallback to LAST_MONTH
                files = glob.glob(f"{PARENT_DIR}/PROFIT AND LOSS/{LAST_MONTH}*/*Profit*")
                if not files:
                    raise FileNotFoundError(f"No P&L file found for {MONTH} or {LAST_MONTH}")
                file_path = files[0]

            p_and_L = pd.read_excel(file_path,
                                    header=5)
            p_and_L.rename(columns={'Unnamed: 1':'variable',
                        2025:'Actual 2025',
                        2024:'Actual 2024'}, inplace=True)
            return p_and_L[['variable','Actual 2025','Actual 2024']]
        
        p_and_L = read_P_and_L(PARENT_DIR, MONTH, LAST_MONTH)    
        logger.info("successfully read P&L data.") 


        p_and_L.columns = p_and_L.columns.str.strip()
        # p_and_L.drop(columns=['Unnamed: 0'], inplace=True)
        # p_and_L.rename(columns={'Unnamed: 1':'variable'}, inplace=True)
        p_and_L['variable'] = p_and_L['variable'].str.rstrip()
        p_and_L.index = p_and_L['variable']

        # realised_LIC = prev_realigned_bel[['DEPARTMENT.1','DISCOUNTED PAA RISK ADJUSTMENT.1']]
        # realised_LIC.rename(columns={'DEPARTMENT.1':'Class of Insurance Business',
        #                              'DISCOUNTED PAA RISK ADJUSTMENT.1':'Release LIC Risk Adjustments Event'}, 
        #                              inplace=True)
        # realised_LIC = realised_LIC.reset_index(drop=True)
        

        processor = IFRS17Processor(revenue_data, incured_claim_data, expenses_data, realigned_bel,prev_realigned_bel, current_loss_component, prev_loss_component,IFIE_data)
        final_template = processor.update_revenue_account_template()
        final_template_with_REO = processor.update_reinsurance_section(final_template)
        YTD_Apr_2025 = final_template_with_REO.iloc[:13].sum()
        final_template_with_REO.loc[f'YTD_{MONTH}_2025'] = YTD_Apr_2025
        try:
            logger.info(f"Updating the P&L variables in the revenue accounts")
            final_template_with_REO.at[f'YTD_{MONTH}_2025', 'Investment income'] = p_and_L.at['Investment & other income','Actual 2025']
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Net Investment and Finance Income/Expenses'] =  final_template_with_REO.at[f'YTD_{MONTH}_2025','IFIE_PAA_TOTAL'] +\
                                                                                                            final_template_with_REO.at[f'YTD_{MONTH}_2025','IFIE_REO_TOTAL'] +\
                                                                                                            final_template_with_REO.at[f'YTD_{MONTH}_2025','Investment income'] 
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Non Attributable Expenses']  = p_and_L.at['Marketing, Communication, R &D& Customer Service Expenses','Actual 2025'] + \
                                                                                                            p_and_L.at['Investment Expenses','Actual 2025'] + \
                                                                                                            p_and_L.at['Other Costs','Actual 2025']
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Profit before income tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2025','Insurance service result'] +\
                                                                                                            final_template_with_REO.at[f'YTD_{MONTH}_2025','Net Investment and Finance Income/Expenses'] +\
                                                                                                            final_template_with_REO.at[f'YTD_{MONTH}_2025','Non Attributable Expenses']
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Income tax expense '] = -final_template_with_REO.at[f'YTD_{MONTH}_2025','Profit before income tax']*TAX_RATE
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Profit After Tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2025','Profit before income tax'] + \
                                                                                     final_template_with_REO.at[f'YTD_{MONTH}_2025','Income tax expense ']
            final_template_with_REO.at[f'YTD_{MONTH}_2025', 'Other comprehensive income'] = p_and_L.at['Other comprehensive income','Actual 2025']
            final_template_with_REO.at[f'YTD_{MONTH}_2025','Total Comprehensive Income After Tax'] =  final_template_with_REO.at[f'YTD_{MONTH}_2025','Profit After Tax'] + \
                                                                                     final_template_with_REO.at[f'YTD_{MONTH}_2025','Other comprehensive income']
        except Exception as e:
            logger.error(f'Error updating P&L variables::{e}')


            logger.info("IFRS 17 Revenue Account Template created successfully.")

        # final_template_with_REO['YTD_Apr_2025'] = final_template_with_REO.iloc[:13].sum(numeric_only=True)
        return final_template_with_REO.T
    except Exception as e:
        logger.error(f"Error in main function: {e}")

# if __name__ == "__main__":
#     main()


#     # https://drive.google.com/drive/folders/1Crd1P0PnpHoS2gajz6eK71wEmFa1XjII?usp=drive_link