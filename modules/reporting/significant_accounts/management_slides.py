import pandas as pd
from datetime import datetime as dt
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
import requests
from io import BytesIO




def get_significant_accounts_management_slides():
    """
    Fetch significant accounts management slides from Google Drive.
    
    Returns:
        pd.DataFrame: DataFrame containing the management slides data.
    """
    try:
        file_name = 'PremiumRegister202509'
        file_path = f"G:/Shared drives/FOOTPRINT EXTRACTS/Year 2025/PremiumRegister/{file_name}.xlsx"

        prem_reg_current = pd.read_excel(file_path)
        prem_reg_current.loc[
            prem_reg_current['cltname'] == 'NATIONAL POLICE SERVICE AND KENYA PRISONS SERVICE', 
            'ClientPinNumber'
        ] = 'NPS'


        prem_reg_prev = pd.read_excel("G:/Shared drives/FOOTPRINT EXTRACTS/Year 2024/PremiumRegister/PremiumRegister202409.xlsx")
        prem_reg_prev.loc[
            prem_reg_prev['cltname'] == 'NATIONAL POLICE SERVICE AND KENYA PRISONS SERVICE', 
            'ClientPinNumber'
        ] = 'NPS'


        from datetime import datetime as dt
        import pandas as pd

        def get_top_accounts_per_class(prem_reg_current, prem_reg_prev):
            today = dt.now()
            current_year = today.year
            prev_year = current_year - 1

            departments = prem_reg_prev['Department'].unique()
            final_output_data = pd.DataFrame()

            for department in departments:
                # Filter by department
                if department in ('MEDICAL', 'MEDICAL    '):
                    cltname = 'SchemeName'
                else:
                    cltname = 'cltname'
                top_5_gross_curr = prem_reg_current[prem_reg_current['Department'] == department].groupby(['ClientPinNumber']).agg(
                    cltname=pd.NamedAgg(column= cltname, aggfunc='max'),
                    GROSS_PREMIUM=pd.NamedAgg(column='basicprem', aggfunc='sum'),
                    NET_PREMIUM=pd.NamedAgg(column='netamount', aggfunc='sum')
                ).rename_axis('INSURED_PIN').reset_index()
                top_5_gross_curr = top_5_gross_curr.add_suffix(f"_{current_year}")

                top_5_gross_prev = prem_reg_prev[prem_reg_prev['Department'] == department].groupby(['ClientPinNumber']).agg(
                    cltname=pd.NamedAgg(column=cltname, aggfunc='max'),
                    GROSS_PREMIUM=pd.NamedAgg(column='basicprem', aggfunc='sum'),
                    NET_PREMIUM=pd.NamedAgg(column='netamount', aggfunc='sum')
                ).rename_axis('INSURED_PIN').reset_index()
                top_5_gross_prev = top_5_gross_prev.add_suffix(f"_{prev_year}")

                # Merge current and previous year data
                top_5_gross_curr_renamed = top_5_gross_curr.rename(columns={f'INSURED_PIN_{current_year}': 'INSURED_PIN'})
                top_5_gross_prev_renamed = top_5_gross_prev.rename(columns={f'INSURED_PIN_{prev_year}': 'INSURED_PIN'})
                top_5_gross = pd.merge(top_5_gross_curr_renamed, top_5_gross_prev_renamed, on='INSURED_PIN', how='outer')

                # GROSS
                top5_current_by_gross = top_5_gross.sort_values(by=f'GROSS_PREMIUM_{current_year}', ascending=False).head(5)
                top5_prev_by_gross = top_5_gross.sort_values(by=f'GROSS_PREMIUM_{prev_year}', ascending=False).head(5)
                gross_curr_ids = set(top5_current_by_gross["INSURED_PIN"])
                prev_only_gross = top5_prev_by_gross[~top5_prev_by_gross["INSURED_PIN"].isin(gross_curr_ids)]
                final_top_5_by_gross = pd.concat([top5_current_by_gross, prev_only_gross], ignore_index=True)
                final_top_5_by_gross["amount_type"] = "gross"
                final_top_5_by_gross["Department"] = department

                # NET
                top5_current_by_net = top_5_gross.sort_values(by=f'NET_PREMIUM_{current_year}', ascending=False).head(5)
                top5_prev_by_net = top_5_gross.sort_values(by=f'NET_PREMIUM_{prev_year}', ascending=False).head(5)
                net_curr_ids = set(top5_current_by_net["INSURED_PIN"])
                prev_only_net = top5_prev_by_net[~top5_prev_by_net["INSURED_PIN"].isin(net_curr_ids)]
                final_top_5_by_net = pd.concat([top5_current_by_net, prev_only_net], ignore_index=True)
                final_top_5_by_net["amount_type"] = "net"
                final_top_5_by_net["Department"] = department

                # Combine and append to final
                final_top_5 = pd.concat([final_top_5_by_gross, final_top_5_by_net])
                final_output_data = pd.concat([final_output_data, final_top_5], ignore_index=True)

            # Save to Excel
            final_output_data.to_excel('final_output_data.xlsx', index=False)


            def get_top_accounts_with_witho_aviation(prem_reg_current, prem_reg_prev):
                today = dt.now()
                current_year = today.year
                prev_year = current_year - 1
                final_output_data = pd.DataFrame()


                # Filter by department
                top_5_gross_curr = prem_reg_current.groupby(['ClientPinNumber']).agg(
                    cltname=pd.NamedAgg(column='cltname', aggfunc='max'),
                    SchemeName=pd.NamedAgg(column='SchemeName', aggfunc='max'),
                    GROSS_PREMIUM=pd.NamedAgg(column='basicprem', aggfunc='sum'),
                    NET_PREMIUM=pd.NamedAgg(column='netamount', aggfunc='sum')
                ).rename_axis('INSURED_PIN').reset_index()
                top_5_gross_curr = top_5_gross_curr.add_suffix(f"_{current_year}")

                top_5_gross_prev = prem_reg_prev.groupby(['ClientPinNumber']).agg(
                    cltname=pd.NamedAgg(column='cltname', aggfunc='max'),
                    SchemeName=pd.NamedAgg(column='SchemeName', aggfunc='max'),
                    GROSS_PREMIUM=pd.NamedAgg(column='basicprem', aggfunc='sum'),
                    NET_PREMIUM=pd.NamedAgg(column='netamount', aggfunc='sum')
                ).rename_axis('INSURED_PIN').reset_index()
                top_5_gross_prev = top_5_gross_prev.add_suffix(f"_{prev_year}")

                # Merge current and previous year data
                top_5_gross_curr_renamed = top_5_gross_curr.rename(columns={f'INSURED_PIN_{current_year}': 'INSURED_PIN'})
                top_5_gross_prev_renamed = top_5_gross_prev.rename(columns={f'INSURED_PIN_{prev_year}': 'INSURED_PIN'})
                top_5_gross = pd.merge(top_5_gross_curr_renamed, top_5_gross_prev_renamed, on='INSURED_PIN', how='outer')

                # GROSS
                top5_current_by_gross = top_5_gross.sort_values(by=f'GROSS_PREMIUM_{current_year}', ascending=False).head(10)
                top5_prev_by_gross = top_5_gross.sort_values(by=f'GROSS_PREMIUM_{prev_year}', ascending=False).head(10)
                gross_curr_ids = set(top5_current_by_gross["INSURED_PIN"])
                prev_only_gross = top5_prev_by_gross[~top5_prev_by_gross["INSURED_PIN"].isin(gross_curr_ids)]
                final_top_5_by_gross = pd.concat([top5_current_by_gross, prev_only_gross], ignore_index=True)
                final_top_5_by_gross["amount_type"] = "gross"
                # NET
                top5_current_by_net = top_5_gross.sort_values(by=f'NET_PREMIUM_{current_year}', ascending=False).head(10)
                top5_prev_by_net = top_5_gross.sort_values(by=f'NET_PREMIUM_{prev_year}', ascending=False).head(10)
                net_curr_ids = set(top5_current_by_net["INSURED_PIN"])
                prev_only_net = top5_prev_by_net[~top5_prev_by_net["INSURED_PIN"].isin(net_curr_ids)]
                final_top_5_by_net = pd.concat([top5_current_by_net, prev_only_net], ignore_index=True)
                final_top_5_by_net["amount_type"] = "net"

                # Combine and append to final
                final_top_5 = pd.concat([final_top_5_by_gross, final_top_5_by_net])
                final_output_data = pd.concat([final_output_data, final_top_5], ignore_index=True)

                # Save to Excel
                final_output_data.to_excel('TOP_10_WITH_AVIATION_NEW.xlsx', index=False)

            prem_reg_current_ = prem_reg_current
            prem_reg_prev_ = prem_reg_prev
            get_top_accounts_with_witho_aviation(prem_reg_current_,prem_reg_prev_)


    except Exception as e:
        logger.error(f"Error fetching management slides data: {e}")
        return pd.DataFrame()