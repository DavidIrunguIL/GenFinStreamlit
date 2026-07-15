import pandas as pd
import numpy as np
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class BankReconciliation:
    def __init__(self, bank_statement, cashbook):
        self.bank_statement = bank_statement
        self.cashbook = cashbook

    def get_cashbook_data(self):
        cashbook_output = self.cashbook
        return cashbook_output


    def clean_bankstatement(self):
        current_bank_df = self.bank_statement.copy()
        df2 = current_bank_df[['Transaction Details','Posting Date', 'Value Date','Bank Reference', 'Debit Amount','Credit Amount']]
        extracted_chq = df2["Transaction Details"].str.extract(r"CHQ-?(\d+)\b")[0]
        conditions = [
        df2["Transaction Details"].str.contains("CHQ", na=False)
        & extracted_chq.notna()
        ]
        choices = [extracted_chq]
        df2["Clean_Cheque_No"] = np.select(conditions, choices, default=df2["Bank Reference"])
        df2['Clean_Cheque_No'] = df2['Clean_Cheque_No'].fillna('No Cheque No')

        return df2
    
    def bank_reconciliation(self):
        clean_bank_df = self.clean_bankstatement()
        cashbook = self.get_cashbook_data()
        logger.info(f"CLEAN BANK DF::::{cashbook}")
        grouped_bank = clean_bank_df.groupby(['Clean_Cheque_No','Transaction Details','Posting Date','Value Date','Bank Reference']).agg(
        Debit_Amount =('Debit Amount','sum'),
        Credit_Amount = ('Credit Amount','sum')
        ).reset_index()

        grouped_cashbook = cashbook.groupby(['Payment Reference', 'Balance Account', 'Source No_',
            'Balance account Name']).agg(
                Amount = ('Amount','sum'),
                Description = ('Description','first'),
                Posting_Date = ('Posting Date','first'),
                Claim_No_ = ('Claim No_','first'),
                Document_No_ = ('Voucher', lambda x: ', '.join(x.dropna().astype(str))),
                    Policy_No_ = ('Policy No_', lambda x: ', '.join(x.dropna().astype(str)))
        ).reset_index()


        merged_df = pd.merge(grouped_cashbook, grouped_bank, 
                            left_on='Payment Reference', 
                            right_on='Clean_Cheque_No',
                            how='outer', 
                            indicator=True,
                            suffixes=('_cashbook', '_bank')) 
        merged_df['Bank_Amount'] = merged_df['Credit_Amount'].fillna(0) - merged_df['Debit_Amount'].fillna(0)
        merged_df['Amount_Difference'] = merged_df['Amount'].fillna(0) - merged_df['Bank_Amount'].fillna(0)


        matching_items = merged_df[merged_df['_merge'] == 'both']
        unclearing_items = merged_df[merged_df['_merge'] == 'left_only']
        unreceipted_items = merged_df[merged_df['_merge'] == 'right_only']

        to_manually_resolve = matching_items[matching_items['Amount_Difference'] != 0]['Clean_Cheque_No'].tolist()
        manual_interv_df = matching_items[matching_items['Clean_Cheque_No'].isin(to_manually_resolve)]
        matching_items = matching_items[~matching_items['Clean_Cheque_No'].isin(to_manually_resolve)]

        grouped_bank = clean_bank_df.groupby('Clean_Cheque_No').agg(
            Total_Debit = ('Debit Amount', 'sum'),  
            Total_Credit = ('Credit Amount', 'sum')
        ).reset_index()

        bounced_cheques = grouped_bank[(grouped_bank['Total_Debit'] > 0) & (grouped_bank['Total_Credit'] > 0)]
        bounced_cheques_data = merged_df[merged_df['Clean_Cheque_No'].isin(bounced_cheques['Clean_Cheque_No'])]
        # bounced_cheques_data.to_excel("C:/Users/dkirungu.ICEALIONGROUP/Downloads/bounced_cheques.xlsx", index=False)

        

        with pd.ExcelWriter("C:/Users/dkirungu.ICEALIONGROUP/Downloads/BANKRECON.xlsx") as writer:
            matching_items.to_excel(writer, sheet_name='Matching Items', index=False)
            unclearing_items.to_excel(writer, sheet_name='Unclearing Items', index=False)
            unreceipted_items.to_excel(writer, sheet_name='Unreceipted Items', index=False)
            manual_interv_df.to_excel(writer, sheet_name='Manual Intervention', index=False)
            bounced_cheques_data.to_excel(writer, sheet_name='Bounced Cheques', index=False)
            
        return {
            "matching_items": matching_items,
            "unclearing_items": unclearing_items,
            "unreceipted_items": unreceipted_items,
            "manual_intervention": manual_interv_df,
            "bounced_cheques": bounced_cheques_data
        }
    