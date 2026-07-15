import pandas as pd
import numpy as np
import logging
import warnings
from datetime import datetime as dt, timedelta

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsuranceRevenueGenerator:
    def __init__(self):
        pass

    @staticmethod
    def get_prem_rev_calculation(prem_data, prem_register_list):
        all_departments = prem_data['Department'].unique()
        pivot_table = prem_data.groupby('Department').agg(
            **{col: pd.NamedAgg(column=col, aggfunc='sum') for col in prem_register_list}
        ).reset_index()

        pivot_table = pivot_table.set_index('Department').reindex(all_departments, fill_value=0).reset_index()
        pivot_table = pivot_table.sort_values(by='Department')

        # Adding total row
        total_row = pivot_table.sum(numeric_only=True)
        total_row['Department'] = 'Total'
        pivot_table = pd.concat([pivot_table, total_row.to_frame().T], ignore_index=True)
        return pivot_table

    @staticmethod
    def get_upr_rev_calculation(upr_data, upr_list, grp_col):
        all_departments = upr_data[grp_col].unique()
        pivot_table = upr_data.groupby(grp_col).agg(
            **{col: pd.NamedAgg(column=col, aggfunc='sum') for col in upr_list}
        ).reset_index()

        pivot_table = pivot_table.set_index(grp_col).reindex(all_departments, fill_value=0).reset_index()
        pivot_table = pivot_table.sort_values(by=grp_col)

        # Adding total row
        total_row = pivot_table.sum(numeric_only=True)
        total_row[grp_col] = 'Total'
        pivot_table = pd.concat([pivot_table, total_row.to_frame().T], ignore_index=True)
        return pivot_table

    @staticmethod
    def get_insurance_revenue(current_upr_pivot_table, current_prem_piv_table,
                               prev_upr_pivot_table, prev_prem_piv_table,
                               current_year, prev_year):
        
        # Current year premium data
        prem_current = current_prem_piv_table[['Department', 'basicprem', 'NetAfterXOL', 'brkcomm', 'NetComm']].copy()
        prem_current['Reins Prem'] = prem_current['basicprem'] - prem_current['NetAfterXOL']
        prem_current[f'ADJ_Reins Prem'] = 0 ##to allow manual adjustements for Rein Prem
        prem_current['Reins Comm'] = prem_current['brkcomm'] - prem_current['NetComm']
        prem_current[f'ADJ_brkcomm_{current_year}'] = 0 ##to allow manual adjustements for brkcomm
        prem_current = prem_current.add_suffix(f'_{current_year}')
        prem_current = prem_current.rename(columns={f'Department_{current_year}': 'Department'})

        ##Adding columns that will need manual adjustemnts       
        prem_current[f'ADJ_Net_Comm'] = 0
        ###


        # Current year UPR data
        upr_current = current_upr_pivot_table[['departmentname', 'GrossUPR', 'NetUPR', 'BrokerDAC', 'NETDAC']].copy()
        upr_current['Reins UPR'] = upr_current['GrossUPR'] - upr_current['NetUPR']
        upr_current['Reins DAC'] = upr_current['BrokerDAC'] - upr_current['NETDAC']
        upr_current = upr_current.add_suffix(f'_{current_year}')
        upr_current = upr_current.rename(columns={f'departmentname_{current_year}': 'Department'})

        # Previous year premium data
        prem_prev = prev_prem_piv_table[['Department', 'basicprem', 'NetAfterXOL', 'brkcomm', 'NetComm']].copy()
        prem_prev['Reins Prem'] = prem_prev['basicprem'] - prem_prev['NetAfterXOL']
        prem_prev['Reins Comm'] = prem_prev['brkcomm'] - prem_prev['NetComm']
        prem_prev = prem_prev.add_suffix(f'_{prev_year}')
        prem_prev = prem_prev.rename(columns={f'Department_{prev_year}': 'Department'})

        # Previous year UPR data
        upr_prev = prev_upr_pivot_table[['departmentname', 'GrossUPR', 'NetUPR', 'BrokerDAC', 'NETDAC']].copy()
        upr_prev['Reins UPR'] = upr_prev['GrossUPR'] - upr_prev['NetUPR']
        upr_prev['Reins DAC'] = upr_prev['BrokerDAC'] - upr_prev['NETDAC']
        upr_prev = upr_prev.add_suffix(f'_{prev_year}')
        upr_prev = upr_prev.rename(columns={f'departmentname_{prev_year}': 'Department'})

        # Merging all
        current_year_df = prem_current.merge(upr_current, how='left', on='Department')
        prev_year_df = prem_prev.merge(upr_prev, how='left', on='Department')
        insurance_rev = current_year_df.merge(prev_year_df, how='left', on='Department')

        # Calculations
        insurance_rev['Insurance Revenue'] = (
            insurance_rev[f'basicprem_{current_year}'] +
            insurance_rev[f'GrossUPR_{prev_year}'] -
            insurance_rev[f'GrossUPR_{current_year}']
        )
        insurance_rev['Net Insurance Revenue'] = (
            insurance_rev[f'NetAfterXOL_{current_year}'] +
            insurance_rev[f'NetUPR_{prev_year}'] -
            insurance_rev[f'NetUPR_{current_year}']
        )
        insurance_rev['Reinsurance Prem Paid'] = insurance_rev['Insurance Revenue'] - insurance_rev['Net Insurance Revenue']

        insurance_rev['Amortize Acq Cost'] = (
            insurance_rev[f'brkcomm_{current_year}'] +
            insurance_rev[f'BrokerDAC_{prev_year}'] -
            insurance_rev[f'BrokerDAC_{current_year}']
        )
        insurance_rev['Net Amortize Acq Cost'] = (
            insurance_rev[f'NetComm_{current_year}'] +
            insurance_rev[f'NETDAC_{prev_year}'] -
            insurance_rev[f'NETDAC_{current_year}']
        )
        insurance_rev['Reinsurance Amortize Acq Cost'] = insurance_rev['Amortize Acq Cost'] - insurance_rev['Net Amortize Acq Cost']
        insurance_rev['Reinsurance Cost'] = insurance_rev['Reinsurance Prem Paid'] - insurance_rev['Reinsurance Amortize Acq Cost']

        insurance_rev['Gross Prem Reserve Mov'] = insurance_rev[f'GrossUPR_{prev_year}'] - insurance_rev[f'GrossUPR_{current_year}']
        insurance_rev['Net Prem Reserve Mov'] = insurance_rev[f'NetUPR_{prev_year}'] - insurance_rev[f'NetUPR_{current_year}']
        insurance_rev['Reinsurance Prem Reserve movement'] = insurance_rev[f'Reins UPR_{prev_year}'] - insurance_rev[f'Reins UPR_{current_year}']
        insurance_rev['Gross Comm Reserve Mov'] = insurance_rev[f'BrokerDAC_{prev_year}'] - insurance_rev[f'BrokerDAC_{current_year}']
        insurance_rev['Reinsurance Comm Reserve movement'] = insurance_rev[f'Reins DAC_{prev_year}'] - insurance_rev[f'Reins DAC_{current_year}']

        # Changes
        insurance_rev['Reins Prem Previous'] = insurance_rev[f'basicprem_{prev_year}'] - insurance_rev[f'NetAfterXOL_{prev_year}']
        insurance_rev['basicprem Change'] = insurance_rev[f'basicprem_{current_year}'] - insurance_rev[f'basicprem_{prev_year}']
        insurance_rev['NetAfterXOL Change'] = insurance_rev[f'NetAfterXOL_{current_year}'] - insurance_rev[f'NetAfterXOL_{prev_year}']
        insurance_rev['Reins Prem Change'] = insurance_rev[f'Reins Prem_{current_year}'] - insurance_rev['Reins Prem Previous']
        insurance_rev['brkcomm Change'] = insurance_rev[f'brkcomm_{current_year}'] - insurance_rev[f'brkcomm_{prev_year}']
        insurance_rev['NetComm Change'] = insurance_rev[f'NetComm_{current_year}'] - insurance_rev[f'NetComm_{prev_year}']
        insurance_rev['Reins Comm Change'] = insurance_rev[f'Reins Comm_{current_year}'] - insurance_rev[f'Reins Comm_{prev_year}']

        # Ratios
        insurance_rev['Reinsurance Ratio Current'] = insurance_rev[f'Reins Prem_{current_year}'] / insurance_rev[f'basicprem_{current_year}']
        insurance_rev['Reinsurance Ratio Previous'] = insurance_rev['Reins Prem Previous'] / insurance_rev[f'basicprem_{prev_year}']
        insurance_rev['Change in REO'] = insurance_rev['Reinsurance Ratio Current'] - insurance_rev['Reinsurance Ratio Previous']

        insurance_rev['Gross Commission Rate Current'] = insurance_rev[f'brkcomm_{current_year}'] / insurance_rev[f'basicprem_{current_year}']
        insurance_rev['Gross Commission Rate Previous'] = insurance_rev[f'brkcomm_{prev_year}'] / insurance_rev[f'basicprem_{prev_year}']
        insurance_rev['Gross Commission Rate Variance'] = insurance_rev['Gross Commission Rate Current'] - insurance_rev['Gross Commission Rate Previous']

        insurance_rev['Reins Commission Rate Current'] = insurance_rev[f'Reins Comm_{current_year}'] / insurance_rev[f'Reins Prem_{current_year}']
        insurance_rev['Reins Commission Rate Previous'] = insurance_rev[f'Reins Comm_{prev_year}'] / insurance_rev['Reins Prem Previous']
        insurance_rev['Reins Commission Rate Variance'] = insurance_rev['Reins Commission Rate Current'] - insurance_rev['Reins Commission Rate Previous']

        ##additional columns
        insurance_rev["Opening insurance contract liabilities"] = insurance_rev["GrossUPR_2024"] - insurance_rev["BrokerDAC_2024"]

        return insurance_rev
