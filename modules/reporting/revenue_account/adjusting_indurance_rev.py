import pandas as pd
import numpy as np
import re
import glob
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from datetime import datetime as dt, timedelta



def adjusting_ins_revenue(insurance_rev_df, current_year,prev_year ):
    try:
        insurance_rev = insurance_rev_df.copy()
        insurance_rev.fillna(value=0, inplace=True)
        insurance_rev[f'NetComm_{current_year}'] += insurance_rev[f'ADJ_Net_Comm']

        insurance_rev[f'brkcomm_{current_year}'] = insurance_rev[f'brkcomm_{current_year}']  - \
                                        insurance_rev[f'ADJ_brkcomm_2026_{current_year}'] 

        insurance_rev[f'Reins Prem_{current_year}'] = insurance_rev[f'Reins Prem_{current_year}'] + \
                                            insurance_rev[f'ADJ_Reins Prem_{current_year}']
        
        insurance_rev[f'Reins Comm_{current_year}'] = insurance_rev[f'brkcomm_{current_year}'] - insurance_rev[f'NetComm_{current_year}']
    except Exception as e:
        logger.error(f"Error applying the immediate adjustments")
    
    try:
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
    except Exception as e:
        logger.error(f"Error in the other calculations:: {e}")

    return insurance_rev


# insurance_revenue_output = pd.read_excel("input_data/InsuranceRevenueAmortizedAqCost_June.xlsx")
##ADJUSTING THE INSURANCE_REVEMUE_OUTPUT
# insurance_revenue_output['Reins Comm_2025'] = insurance_revenue_output['brkcomm_2025'] - \
#                                                  insurance_revenue_output['NetComm_2025'] + \
#                                                  insurance_revenue_output['ADJ_Reins Comm_2025']
# insurance_revenue_output['Reins Prem_2025'] = insurance_revenue_output['Reins Prem_2025'] +\
#                                              insurance_revenue_output['ADJ_Reins Prem_2025']

# today = dt.now()
# current_year = today.year
# prev_year = current_year -1 
# month = today.month - 1
# year_month = f"{current_year}{month:02d}"
# ins_rev_with_adj = pd.read_excel(f"C:/Users/dkirungu/Documents/finance/reporting/IRA_IFRS17/input_data/insurance_revenue_amortize_aq_cost_202508.xlsx")
# adjusted_ins_rev = adjusting_ins_revenue(ins_rev_with_adj, current_year,prev_year )
# adjusted_ins_rev.to_excel(f"input_data/adjusted_insurance_revenue_{year_month}.xlsx", index=False)
# adjusted_ins_rev.shape




