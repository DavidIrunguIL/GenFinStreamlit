import pandas as pd
import numpy as np
import logging
import glob
import warnings
from datetime import datetime as dt, timedelta

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_claims_data(year, month):
    try:
            year_month = f"{year}{month:02d}"
            medical_claims_file = glob.glob(f"G:/Shared drives/FOOTPRINT EXTRACTS/Year {year}/Medical Claims  Paid/*{year_month}*.xlsx")
            medical_claims = pd.read_excel(medical_claims_file[0], sheet_name = 'All')
            medical_claims['Department'] = 'MEDICAL'
            medical_claims['reo_claims_paid'] = medical_claims['GrossPaid'] - medical_claims['NetPaid']
            grp_medical_df = medical_claims.groupby('Department').agg(
                        total_gross_paid = ('GrossPaid', 'sum'),
                        total_net_paid = ('NetPaid', 'sum'),
                        total_reo_paid = ('reo_claims_paid', 'sum'),
                    ).reset_index()
            file_list = glob.glob(f"G:/Shared drives/FOOTPRINT EXTRACTS/Year {year}/ClaimsPaid/*{year_month}*.xlsx")
            if file_list:
                claims_data = pd.read_excel(file_list[0])
            else:
                logger.warning(f"Error::No file found matching pattern")

            claims_data['FinanceCode'] = claims_data['FinanceCode'].astype(str)
            claims_data.loc[claims_data['FinanceCode'] == '122', 'Department'] = 'PERSONAL ACCIDENT'

            claims_data['pfx'] = claims_data['pfx'].astype(str)
            claims_data.loc[
                (claims_data['pfx'].isin(['120', '112'])) & 
                (claims_data['Department'].str.contains('MOTOR', na=False)),
                'Department'
            ] = 'MOTOR PRIVATE'

            claims_data.loc[claims_data['pfx'].isin(['119']) & 
                (claims_data['Department'].str.contains('MOTOR', na=False)), 'Department'] = 'MOTOR COMMERCIAL'


            claims_data['reo_claims_paid'] = claims_data['Grosspaid'] - claims_data['Netpaid']
            grp_claims_data = claims_data.groupby('Department').agg(
                total_gross_paid = ('Grosspaid', 'sum'),
                total_net_paid = ('Netpaid', 'sum'),
                total_reo_paid = ('reo_claims_paid', 'sum'),
            ).reset_index()

            grp_claims_data = pd.concat([grp_claims_data, grp_medical_df], axis=0)
            return grp_claims_data
    except Exception as e:
        logger.error(f"Error reading claims data: {e}")
        return pd.DataFrame()

