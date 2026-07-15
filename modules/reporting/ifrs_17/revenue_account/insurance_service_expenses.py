import pandas as pd
import numpy as np
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import logging
import warnings
from datetime import datetime as dt, timedelta

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


MONTH = (dt.today() - timedelta(days=30)).strftime('%b')
class IFRS17Processor:
    def __init__(self, revenue_data, incured_claim_data, expenses_data, realigned_bel,prev_realigned_bel,
                 current_loss_component=None, prev_loss_component=None, IFIE_data=None):
        self.revenue_data = revenue_data
        self.incured_claim_data = incured_claim_data
        self.expenses_data = expenses_data
        self.realigned_bel = realigned_bel
        self.current_loss_component = current_loss_component
        self.prev_loss_component = prev_loss_component
        # self.realised_LIC = realised_LIC
        self.IFIE_data = IFIE_data
        self.prev_realigned_bel = prev_realigned_bel

    def get_IFRS17_template(self):
        try:
            df = pd.read_excel("C:/Users/dkirungu/Documents/finance/streamlit/modules/reporting/ifrs_17/revenue_account/input_data/IFRS 17 APRIL 2025 TEMPLATE Revenue account and Balance sheet. - After April 2025 LC.xlsx", sheet_name='template')
            df.columns = df.columns.map(str)
            df = df.loc[:, ~df.columns.str.startswith('Unnamed')].dropna(how='all')
            df.drop(columns=['1000'], inplace=True)

            df_transposed = df.T
            df_transposed.columns = df_transposed.iloc[0]
            df_transposed = df_transposed.drop(df_transposed.index[0])
            df_transposed.index.name = 'Class of Insurance Business'
            # final_template_with_REO.loc['YTD_May_2025'] = YTD_Apr_2025

            result = df_transposed.reset_index().rename(columns={'index': 'Class of Insurance Business'})
            result.set_index('Class of Insurance Business', inplace=True)
            # result.rename(columns={'YTD_Apr_2025': 'YTD_May_2025'}, inplace=True)
            result.rename(index={f'YTD_Apr_2025': f'YTD_{MONTH}_2025'}, inplace=True)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_IFRS17_template: {e}")
            return pd.DataFrame()

    def get_insurance_revenue(self):
        current_year = dt.now().year
        prev_year = current_year - 1
        current_date = (dt.now().replace(day=1) - relativedelta(days=1)).strftime('%d/%m/%Y')
        try:
            df = self.revenue_data.copy()
            # df.rename(columns={'Unnamed: 0': 'Class of Insurance Business'}, inplace=True)
            df.dropna(subset=['Department'], inplace=True)
            df.set_index('Department', inplace=True)
            df['Insurance acquisition cash flows amortasation'] = df['Amortize Acq Cost'].fillna(0).astype(float)*-1
            ###PAA
            df['Gross Written Premium'] = df[f'basicprem_{current_year}'].fillna(0).astype(float)
            df[f'UPR  as at 01/01/{current_year}'] = df[f'GrossUPR_{prev_year}'].fillna(0).astype(float)
            df[f'UPR  as at {current_date}'] = df[f'GrossUPR_{current_year}'].fillna(0).astype(float)
            ###REO
            df['Reinsurance Premium Ceded'] = df[f'Reins Prem_{current_year}'].fillna(0).astype(float)
            df[f'REO UPR  as at 01/01/{current_year}'] = df[f'Reins UPR_{prev_year}'].fillna(0).astype(float)
            df[f'REO UPR  as at {current_date}'] = df[f'Reins UPR_{current_year}'].fillna(0).astype(float)
            return df
        except Exception as e:
            logger.error(f"Error in get_insurance_revenue: {e}")
            return pd.DataFrame()

    def get_incured_claims(self):
        try:
            df = self.incured_claim_data.copy()
            df.rename(columns={'DEPARTMENT':'Class of Insurance Business'}, inplace = True)
            df.dropna(subset=['Class of Insurance Business'], inplace=True)
            df.set_index('Class of Insurance Business', inplace=True)
            df['Incurred Claims'] = df['Gross Incurred'] * -1
            return df
        except Exception as e:
            logger.error(f"Error in get_incured_claims: {e}")
            return pd.DataFrame()

    def get_bel(self):
        try:
            df_bel = self.realigned_bel.copy()
            df_bel["DEPARTMENT"] = df_bel["DEPARTMENT"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            df_bel.rename(columns={
                'DEPARTMENT': 'Class of Insurance Business',
                'DISCOUNTED PAA RISK ADJUSTMENT': 'LIC Risk Adjustments Event',
                'DISCOUNTED NON-PERFORMANCE AMOUNTS': 'NON-PERFORMANCE AMOUNTS'
            }, inplace=True)

            df_bel['LIC Risk Adjustments Event'] *= -1
            df_bel.dropna(subset=['Class of Insurance Business'], inplace=True)
            df_bel['Class of Insurance Business'] = df_bel['Class of Insurance Business'].str.upper()
            df_bel.set_index('Class of Insurance Business', inplace=True)
            # df_realise.set_index('Class of Insurance Business', inplace=True)
            return df_bel #, df_realise
        except Exception as e:
            logger.error(f"Error in get_bel: {e}")
            return pd.DataFrame(), pd.DataFrame()
    def get_prev_bel(self):
        try:
            prev_realigned_bel = self.prev_realigned_bel
            prev_realigned_bel["DEPARTMENT"] = prev_realigned_bel["DEPARTMENT"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")

            prev_realigned_bel.rename(columns={
                'DEPARTMENT': 'Class of Insurance Business',
                # 'DISCOUNTED PAA RISK ADJUSTMENT': 'LIC Risk Adjustments Event',
                'DISCOUNTED PAA RISK ADJUSTMENT': 'Release LIC Risk Adjustments Event',
                'DISCOUNTED REO RISK ADJUSTEMENT': 'DISCOUNTED REO RISK ADJUSTEMENT',
                'NON-PERFORMANCE AMOUNTS': 'NON-PERFORMANCE AMOUNTS',
            }, inplace=True)

            prev_realigned_bel['LIC Risk Adjustments Event'] = prev_realigned_bel['Release LIC Risk Adjustments Event']*-1

            prev_realigned_bel.dropna(subset=['Class of Insurance Business'], inplace=True)
            prev_realigned_bel['Class of Insurance Business'] = prev_realigned_bel['Class of Insurance Business'].str.upper()
            prev_realigned_bel.set_index('Class of Insurance Business', inplace=True)
            
            return prev_realigned_bel
        except Exception as e:
            logger.error(f"Error in get_prev_bel: {e}")
            return pd.DataFrame()

    def get_IFIE(self):
        def rename_duplicates(series):
            seen = {}
            new_vals = []
            for val in series:
                if val not in seen:
                    new_vals.append(f"{val}_PAA")
                    seen[val] = 1
                else:
                    new_vals.append(f"{val}_REO")
            return new_vals

        try:
            df = self.IFIE_data.copy()
            df.drop(columns=['Unnamed: 0', 'DETAILS'], inplace=True)
            df["INCOME STATEMENT DISCLOSURE"] = rename_duplicates(df["INCOME STATEMENT DISCLOSURE"])

            df.set_index('INCOME STATEMENT DISCLOSURE', inplace=True)
            df = df.T.rename(columns={
                'Interest accreted_PAA': 'LIC Interest accreted',
                'Effect of changes in interest rates and other financial assumptions_PAA': 'LIC Effect of changes in interest rates'
            })
            
            df['LIC EFFECT OF CHANGES IN INTEREST RATES'] = df['LIC Effect of changes in interest rates']
            df['LIC INTEREST ACCRETED'] = df['LIC Interest accreted']
            df['LIC Interest accreted'] *= -1
            df['LIC Effect of changes in interest rates'] *= -1
            df['IFIE_PAA_TOTAL'] =  df['LIC INTEREST ACCRETED'] + df['LIC EFFECT OF CHANGES IN INTEREST RATES']
            
            return df
        except Exception as e:
            logger.error(f"Error in get_IFIE: {e}")
            return pd.DataFrame()

    def get_expenses(self, revenue_template):
        try:
            df = self.expenses_data
            df.set_index('Unnamed: 0', inplace=True)
            df = df.T
            df.index = df.index.str.upper()
            revenue_template['PAA'] = np.nan
            revenue_template['REO'] = np.nan
            df = df.loc[:, ~df.columns.duplicated()]
            revenue_template.update(df)
            revenue_template['Directly attributable Expenses_PAA'] = revenue_template['PAA'].fillna(0).astype(float) * -1
            revenue_template['Directly attributable Expenses_REO'] = revenue_template['REO'].fillna(0).astype(float) * -1
            revenue_template.drop(columns=['PAA','REO'], inplace=True)
            self.expenses_data = df
            return revenue_template
        except Exception as e:
            logger.error(f"Error in get_expenses: {e}")
            return revenue_template

    def get_loss_components(self):
        try:
            current = self.current_loss_component.copy()
            prev = self.prev_loss_component.copy()
            current['Class of business'] = current['Class of business'].str.strip()
            prev['Class of business'] = prev['Class of business'].str.strip()
            current["Class of business"] = current["Class of business"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            prev["Class of business"] = prev["Class of business"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")

            for df in [current, prev]:
                df.dropna(subset=['Class of business'], inplace=True)
                df.set_index('Class of business', inplace=True)
                df.drop(columns=['Unnamed: 0'], inplace=True)
                df.index = df.index.str.upper()

            current['Losses on onerous contracts and reversal of those losses'] = current['Gross loss component'].fillna(0).astype(float) * -1
            prev['Release Recoveries of loss on recognition of underlying onerous contracts'] = prev['Gross loss component'].fillna(0).astype(float) * -1
            prev['Ifrs 17 Release Loss Component'] = prev['Gross loss component']

            return current, prev
        except Exception as e:
            logger.error(f"Error in get_loss_components: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def update_revenue_account_template(self):
        try:
            rev_template = self.get_IFRS17_template()
            rev_template.update(self.get_insurance_revenue())
            rev_template.update(self.get_incured_claims())

            bel = self.get_bel()
            rev_template.update(bel)
            
            realise_lic = self.prev_realigned_bel[['DEPARTMENT','DISCOUNTED PAA RISK ADJUSTMENT']].copy()
            realise_lic["DEPARTMENT"] = realise_lic["DEPARTMENT"].replace("MISCELLANEOUS ACCIDENT", "MISCELLANEOUS")
            realise_lic.columns = ['Class of Insurance Business', 'Release LIC Risk Adjustments Event']
            realise_lic = realise_lic.set_index("Class of Insurance Business")
            rev_template.update(realise_lic)
            # print(rev_template['Release LIC Risk Adjustments Event'])
            rev_template.update(self.get_IFIE())
            rev_template = self.get_expenses(rev_template)

            curr_loss, prev_loss = self.get_loss_components()
            rev_template.update(curr_loss)
            rev_template.update(prev_loss)

            # Derived fields
            rev_template['Changes that related to Loss component'] = rev_template[
                'Losses on onerous contracts and reversal of those losses'].fillna(0) + \
                rev_template['Ifrs 17 Release Loss Component'].fillna(0)

            rev_template['Changes that related to past service-Adjustments to the LIC'] = rev_template[
                'Release LIC Risk Adjustments Event'].fillna(0) + rev_template[
                'LIC Risk Adjustments Event'].fillna(0)

            rev_template['Changes in Losses on Onerous cntracts'] = rev_template[
                'Losses on onerous contracts and reversal of those losses'].fillna(0).astype(float) + rev_template[
                'Release Recoveries of loss on recognition of underlying onerous contracts'].fillna(0).astype(float)
            
            dupes = rev_template.columns[rev_template.columns.duplicated()]
            rev_template = rev_template.loc[:, ~rev_template.columns.duplicated()]


            # Calculate total insurance service expenses
            rev_template['Changes that related to Loss component'] = (
                pd.to_numeric(rev_template['Losses on onerous contracts and reversal of those losses'], errors='coerce').fillna(0) +
                pd.to_numeric(rev_template['Ifrs 17 Release Loss Component'], errors='coerce').fillna(0)
            )

            rev_template['Changes that related to past service-Adjustments to the LIC'] = (
                pd.to_numeric(rev_template['Release LIC Risk Adjustments Event'], errors='coerce').fillna(0) +
                pd.to_numeric(rev_template['LIC Risk Adjustments Event'], errors='coerce').fillna(0)
            )

            rev_template['Changes in Losses on Onerous cntracts'] = (
                pd.to_numeric(rev_template['Losses on onerous contracts and reversal of those losses'], errors='coerce').fillna(0) +
                pd.to_numeric(rev_template['Release Recoveries of loss on recognition of underlying onerous contracts'], errors='coerce').fillna(0)
            )

            rev_template['Total Insurance Service expenses'] = rev_template[['Incurred Claims',
                                                                             'Changes that related to past service-Adjustments to the LIC',
                                                                             'LIC Interest accreted',
                                                                             'LIC Effect of changes in interest rates',
                                                                             'Directly attributable Expenses_PAA',
                                                                             'Changes that related to Loss component',
                                                                             'Insurance acquisition cash flows amortasation']].sum(axis=1)      
            return rev_template
        except Exception as e:
            logger.error(f"Error in update_revenue_account_template: {e}")
            return pd.DataFrame()
        
    def update_reinsurance_section(self, revenue_account_template):
            try:
                insur_revenue = self.get_insurance_revenue()
                incured_claim = self.get_incured_claims()
                realigned_bel = self.get_bel()
                prev_realigned_bel = self.get_prev_bel()
                IFIE_numbers_tr = self.get_IFIE()
                current_loss_component, prev_loss_component = self.get_loss_components()
                expenses_trns = self.expenses_data.copy()

                logger.info("Updating Reinsurance Section of Revenue Account Template")

                incured_claim['Incurred LIC Event'] = incured_claim['ReoIncurred'].fillna(0).astype(float)

                revenue_account_template['Net expenses from reinsurance contracts held'] = np.nan.__float__()
                insur_revenue['Reinsurance Premium Earned'] = insur_revenue['Insurance Revenue'] - insur_revenue['Net Insurance Revenue']
                revenue_account_template['Reinsurance Premium Paid'] = insur_revenue['Reinsurance Premium Earned'].fillna(0).astype(float) * -1
                revenue_account_template['Reinsurance Amortize Acq Cost'] = insur_revenue['Reinsurance Amortize Acq Cost'].fillna(0).astype(float)
                logger.info("Done with reinsurance cost and paid prem revenue")
                revenue_account_template = revenue_account_template.apply(pd.to_numeric, errors='ignore')
                revenue_account_template['Reinsurance expenses-Contracts measured under PAA'] = revenue_account_template['Reinsurance Premium Paid'] + revenue_account_template['Reinsurance Amortize Acq Cost']
                revenue_account_template['Claims recovered'] = np.nan.__float__()
                revenue_account_template['Incurred LIC Event'] = incured_claim['ReoIncurred'].fillna(0).astype(float)
                logger.info("Done with incured claims and recoveries")
                # print(realigned_bel.columns)
                # print(realigned_bel['DISCOUNTED REO RISK ADJUSTEMENT'])
                revenue_account_template['REO LIC Risk Adjustments Event'] = realigned_bel['DISCOUNTED REO RISK ADJUSTEMENT'].fillna(0).astype(float)
                # print('DISC_RISK_ADJ',prev_realigned_bel['DISCOUNTED REO RISK ADJUSTEMENT'].fillna(0).astype(float)*-1)
                # print(prev_realigned_bel.columns)
                revenue_account_template['REO Release LIC Risk Adjustments Event'] = prev_realigned_bel['DISCOUNTED REO RISK ADJUSTEMENT'].fillna(0).astype(float)*-1

                logger.info("Done with discounted REO risk adjustments")

                revenue_account_template['Changes in the risk  adjustment recognized for the risk expired'] = revenue_account_template['REO LIC Risk Adjustments Event'] + revenue_account_template['REO Release LIC Risk Adjustments Event']
                revenue_account_template['Changes in the risk  adjustment recognized for the risk expired']
                revenue_account_template['REO Interest accreted'] = IFIE_numbers_tr['Interest accreted_REO'].fillna(0).astype(float) * -1
                revenue_account_template['REO INTEREST ACCRETED'] = IFIE_numbers_tr['Interest accreted_REO'].fillna(0).astype(float)
                revenue_account_template['REO Effect of changes in interest rates'] = IFIE_numbers_tr['Effect of changes in interest rates and other financial assumptions_REO'].fillna(0).astype(float) * -1
                revenue_account_template['REO EFFECT OF CHANGES IN INTEREST RATES'] = revenue_account_template['REO Effect of changes in interest rates']*-1
                revenue_account_template['IFIE_REO_TOTAL'] = revenue_account_template['REO INTEREST ACCRETED'] + revenue_account_template['REO EFFECT OF CHANGES IN INTEREST RATES']
                revenue_account_template['Directly attributable Expenses_REO'] = expenses_trns['REO'].fillna(0).astype(float)*-1
                revenue_account_template['Non Performance Risk'] = realigned_bel['NON-PERFORMANCE AMOUNTS'].fillna(0).astype(float)
                revenue_account_template['ReleaseNon performance LIC event'] = prev_realigned_bel['NON-PERFORMANCE AMOUNTS'].fillna(0).astype(float)*-1
                # revenue_account_template['Release LIC Risk Adjustments Event'] = prev_realigned_bel['Release LIC Risk Adjustments Event'].fillna(0).astype(float)
                revenue_account_template['Effect of changes in the risk of reinsurers non performance'] = revenue_account_template['Non Performance Risk'] + revenue_account_template['ReleaseNon performance LIC event']
                revenue_account_template['Recoveries of loss on recognition of underlying onerous contracts'] = current_loss_component['Loss Recovery Component'].fillna(0).astype(float)
                revenue_account_template['Release Recoveries of loss on recognition of underlying onerous contracts'] = prev_loss_component['Loss Recovery Component'].fillna(0).astype(float)*-1
                revenue_account_template['Changes in Losses on Onerous cntracts'] = revenue_account_template['Recoveries of loss on recognition of underlying onerous contracts'] + revenue_account_template['Release Recoveries of loss on recognition of underlying onerous contracts']
                revenue_account_template['Changes in Losses on Onerous cntracts']

                revenue_account_template['Total net expenses from reinsurance contracts held'] = revenue_account_template['Reinsurance expenses-Contracts measured under PAA'] + \
                    revenue_account_template['Incurred LIC Event'] + \
                    revenue_account_template['Changes in the risk  adjustment recognized for the risk expired'] + \
                                revenue_account_template['REO Interest accreted'] + \
                    revenue_account_template['REO Effect of changes in interest rates']+\
                    revenue_account_template['Directly attributable Expenses_REO'] -\
                    revenue_account_template['Effect of changes in the risk of reinsurers non performance'] + \
                    revenue_account_template['Changes in Losses on Onerous cntracts']
            
                revenue_account_template['Insurance service result'] = revenue_account_template['Total net expenses from reinsurance contracts held'] + \
                    revenue_account_template['Insurance Revenue'] + \
                    revenue_account_template['Total Insurance Service expenses']
                revenue_account_template['Insurance service result']

                return revenue_account_template
            except Exception as e:
                logger.error(f"Error in update_reinsurance_section: {e}")
                return revenue_account_template

        
