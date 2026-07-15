from src.insurance_revenue_class import InsuranceRevenueGenerator
from src.claims import get_claims_data
from input_data import  get_data
import pandas as pd
import numpy as np
from datetime import datetime as dt
import warnings
import logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


current_year = dt.now().year
month = dt.now().month - 1
prev_year = current_year - 1

# if 
start_period = f"{prev_year}01"
end_period = dt.now().strftime("%Y%m")  # current year and month

#the *last completed* month instead:
today = dt.now()
last_month = today.replace(day=1) - pd.DateOffset(days=1)
end_period = last_month.strftime("%Y%m")


GetData = get_data.GetData
current_prem_reg = GetData.get_prem_reg(current_year, month)
prev_prem_reg = GetData.get_prem_reg(prev_year, 12)
claims_data = get_claims_data(current_year, month)

prem_reg = pd.concat([current_prem_reg,prev_prem_reg], axis=0)

# prem_reg.to_excel(f"output_data/prem_reg.xlsx", index=False)
current_upr_reg = GetData.get_upr_reg(current_year, month)
prev_upr_reg = GetData.get_upr_reg(prev_year, 12)

## adjustoments to the prem_regester where needed
prem_reg['FinanceCode'] = prem_reg['FinanceCode'].astype(str)
current_upr_reg['FinanceCode'] = current_upr_reg['FinanceCode'].astype(str)
prev_upr_reg['FinanceCode'] = prev_upr_reg['FinanceCode'].astype(str)



prem_reg.loc[prem_reg['FinanceCode'] == '122', 'Department'] = 'PERSONAL ACCIDENT'
current_upr_reg.loc[current_upr_reg['FinanceCode'] == '122', 'departmentname'] = 'PERSONAL ACCIDENT'
prev_upr_reg.loc[prev_upr_reg['FinanceCode'] == '122', 'departmentname'] = 'PERSONAL ACCIDENT'



prem_register_list = [
    "basicprem",  "brkcomm", "tlevy", "pcf", "duty", "wtax", "eareamt", "surp1amt", "surp2amt", 
    "Loggross","Facprop", "QsAmt","NetAfterXOL", "netamount", "Xol1", "Xol2", 
    "Xol3", "Xol4", "Xol5", "XolTotal",  "NetComm", "QsComm", "facpropcomm", "surpcomm", 
    "surp2comm", "fobcomm", "NewBusiness", "RenewalPremium", "OtherPremium"
] #missing: ["netamountAfterNonProportionalTreaty", "NetAfterXOL"]


upr_list = [
    'Basic Premium', 'FacPremium', 'Surp1Prem', 'Surp2Prem', 'QSPrem', 'FOBPrem', 'Net Premium',
    'GrossCommission', 'FACComm', 'Surp1Comm', 'Surp2Comm', 'QSComm', 'FOBComm', 'NetComm',
    'GrossUPR', 'EareUPR', 'FacPropUPR', 'QSUPR', 'Surp1UPR', 'Surp2UPR', 'NetUPR',
    'BrokerDAC', 'FACDAC', 'FOBDAC', 'Surp1DAC', 'Surp2DAC', 'QuotaDAC', 'NETDAC'
]


prem_reg['period'] = pd.to_numeric(prem_reg['period'])
current_period = dt.now().strftime('%Y%m')
current_start_period = int(dt(dt.now().year, 1, 1).strftime('%Y%m'))

prev_year_prem_ = prem_reg[prem_reg['period'] < current_start_period]
current_year_prem_ = prem_reg[prem_reg['period'] >= current_start_period]

current_prem_piv_table = InsuranceRevenueGenerator.get_prem_rev_calculation(current_year_prem_,prem_register_list)
prev_prem_piv_table = InsuranceRevenueGenerator.get_prem_rev_calculation(prev_year_prem_,prem_register_list)

current_prem_piv_table.to_excel(f"output_data/current_prem_piv_table.xlsx", index=False)
prev_prem_piv_table.to_excel(f"output_data/prev_prem_piv_table.xlsx", index=False)

grp_col = 'departmentname'
current_upr_pivot_table = InsuranceRevenueGenerator.get_upr_rev_calculation(current_upr_reg,upr_list,grp_col)
prev_upr_pivot_table = InsuranceRevenueGenerator.get_upr_rev_calculation(prev_upr_reg,upr_list,grp_col)




insurance_rev = InsuranceRevenueGenerator.get_insurance_revenue(current_upr_pivot_table, current_prem_piv_table,
                               prev_upr_pivot_table, prev_prem_piv_table,
                               current_year, prev_year)

numeric_cols = insurance_rev.columns.difference(['Department'])
insurance_rev[numeric_cols] = insurance_rev[numeric_cols].apply(pd.to_numeric, errors='coerce')
# insurance_rev = insurance_rev[insurance_rev['Department'] != 'Total'] #remove total when not needed 
year_month = f"{current_year}{month:02d}"
# insurance_rev.to_excel(f"output_data/insurance_revenue_amortize_aq_cost_{year_month}.xlsx", index=False)


# Write both DataFrames into separate sheets
with pd.ExcelWriter(f"output_data/insurance_revenue_amortize_aq_cost_{year_month}.xlsx", engine="xlsxwriter") as writer:
    insurance_rev.to_excel(writer, sheet_name="insurance_revenue", index=False)
    claims_data.to_excel(writer, sheet_name="claims_data", index=False)