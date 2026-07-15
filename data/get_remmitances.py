import pandas as pd
from dotenv import load_dotenv
import os
import re
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime as dt
import streamlit as st
# from data.sql_queries import test
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


def get_remmitances(claim_no, payee = None):
    try:
        db_host = os.getenv("DB_HOST_PROD")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        driver = os.getenv("DRIVER")
        trusted_conn = os.getenv("TRUSTED_CONN")
        server = os.getenv("SERVER")

        connection_string = (
            f"mssql+pyodbc://{db_host},{db_port}/{db_name}?driver={driver}&trusted_connection={trusted_conn}"
        )

        #SQLAlchemy engine
        engine = create_engine(connection_string)
        logger.info(f'successfully connected to the DB::')
    except Exception as e:
        logger.error(f'Error connecting to the DB:: {e}')
    try:
        with engine.connect() as connection:
            if claim_no:
                query = text(f'''                  
                        SELECT top 5 
                        [Line No_],	BATCH_ID,
                        PV_NO,	CLAIM_NO,	AMOUNT	, 
                        TOTAL_AMOUNT, 
                        PAYEE, ACCOUNT_NO, 
                        SORT_CODE, 
                        STATUS, 
                        TYPE_BATCH, 
                        [Reference Number], 
                        [Report Ref No], 
                        Payee, 
                        Amount, 
                        [GL Account], 
                        [GL Description], 
                        [Bank Account], 
                        [Claim No], 
                        [Policy Number], 
                        [Beneficiary Account], 
                        [Swift Code], 
                        [Payment Description], 
                        [Payment Status], 
                        InvoiceNo, 
                        [Contact Email], 
                        [FP Claim No]
                        FROM ICEALION.dbo.[ICEA-LION GROUP$IL PAYMENT DETAIL2] dt
                        left join ICEALION.dbo.[ICEA-LION GROUP$General Business Payments new] pyn
                        ON dt.CLAIM_NO = pyn.[Claim No] 
                        where pyn.[Claim No] in ('{claim_no}')
                        order by [Pay Date] DESC;
                ''')
                df = pd.read_sql_query(
                    query,
                    connection,
                    params={
                        'claim_no': claim_no,
                    }
                )
                logger.info('Successfully fetched data by claim_no')
            elif payee:
                payee_clean = payee.replace("'", "''").lower()
                query = text(f'''                  
                        SELECT top 5 
                        [Line No_],	BATCH_ID,
                        PV_NO,	CLAIM_NO,	AMOUNT	, 
                        TOTAL_AMOUNT, 
                        PAYEE, ACCOUNT_NO, 
                        SORT_CODE, 
                        STATUS, 
                        TYPE_BATCH, 
                        [Reference Number], 
                        [Report Ref No], 
                        Payee, 
                        Amount, 
                        [GL Account], 
                        [GL Description], 
                        [Bank Account], 
                        [Claim No], 
                        [Policy Number], 
                        [Beneficiary Account], 
                        [Swift Code], 
                        [Payment Description], 
                        [Payment Status], 
                        InvoiceNo, 
                        [Contact Email], 
                        [FP Claim No]
                        FROM ICEALION.dbo.[ICEA-LION GROUP$IL PAYMENT DETAIL2] dt
                        left join ICEALION.dbo.[ICEA-LION GROUP$General Business Payments new] pyn
                        ON dt.CLAIM_NO = pyn.[Claim No] 
                        where  lower(pyn.PAYEE) LIKE ({payee})
                        order by [Pay Date] DESC;
                    ''')
        
                df = pd.read_sql_query(
                        query,
                        connection,
                        params={'payee': f"%{payee_clean.lower()}%"}
                    )
                logger.info('Successfully fetched data by payee')

            else:
                df = pd.DataFrame()
                logger.warning('No valid claim_no or payee provided.')
            return df
    except Exception as e:
        logger.error(f'Error fetching the data::{e}')
    




