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


@st.cache_data(ttl=600)
def get_broker_aging(date):
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
    # Query example (you can call your stored procedure here)
    try:
        with engine.connect() as connection:
            query = text(f'''
                SELECT
                [Broker No],
                Name,
                upper([Customer Posting Group]) as [Customer Posting Group] ,
                upper(C.[Responsibility Center]) as [Responsibility Center],
                SUM([Original Amount]) AS [Original Amount],
                SUM([Allocated Debits PR Amount]) AS PreviousYrAllocations,
                SUM([Allocated Debits CR Amount]) AS CurrentYrAllocations,
                SUM([Unallocated Amount]) AS [Unallocated Amount],
                isnull((
                    SELECT
                    SUM([Unallocated Amount]) AS EXPR1
                    FROM
                    [ICEA-LION GROUP$Receipt Analysis Yr 2015] AS Amount
                    WHERE
                    [Broker No] =C.No_
                    AND ([Receipt Date] BETWEEN DATEADD(day,
                        -30,
                        CAST('{date}' AS date))
                        AND CAST('{date}' AS date))),
                    0) AS [0-30 Un Allocated],
                isnull((
                    SELECT
                    SUM([Unallocated Amount]) AS EXPR1
                    FROM
                    [ICEA-LION GROUP$Receipt Analysis Yr 2015] AS Amount
                    WHERE
                    [Broker No] =C.No_
                    AND ([Receipt Date] BETWEEN DATEADD(day,
                        -60,
                        CAST('{date}' AS date))
                        AND DATEADD(day,
                        -31,
                        CAST('{date}' AS date)))),
                    0) AS [31-60 Un Allocated],
                isnull((
                    SELECT
                    SUM([Unallocated Amount]) AS EXPR1
                    FROM
                    [ICEA-LION GROUP$Receipt Analysis Yr 2015] AS Amount
                    WHERE
                    [Broker No] =C.No_
                    AND ([Receipt Date] BETWEEN DATEADD(day,
                        -90,
                        CAST('{date}' AS date))
                        AND DATEADD(day,
                        -61,
                        CAST('{date}' AS date)))),
                    0) AS [61-90 Un Allocated],
                isnull((
                    SELECT
                    SUM([Unallocated Amount]) AS EXPR1
                    FROM
                    [ICEA-LION GROUP$Receipt Analysis Yr 2015] AS Amount
                    WHERE
                    [Broker No] =C.No_
                    AND ([Receipt Date] BETWEEN DATEADD(day,
                        -120,
                        CAST('{date}' AS date))
                        AND DATEADD(day,
                        -91,
                        CAST('{date}' AS date)))),
                    0) AS [91-120 Un Allocated],
                isnull((
                    SELECT
                    SUM([Unallocated Amount]) AS EXPR1
                    FROM
                    [ICEA-LION GROUP$Receipt Analysis Yr 2015] AS Amount
                    WHERE
                    [Broker No] =C.No_
                    AND [Receipt Date] < DATEADD(day,
                        -120,
                        CAST('{date}' AS date) )),
                    0) AS [OVER 120 Un Allocated]
                FROM
                [ICEA-LION GROUP$Receipt Analysis Yr 2015] R  
                INNER JOIN
                [ICEA-LION GROUP$Customer] C
                ON
                C.No_=[Broker No]
                WHERE
                [Customer Posting Group] IN ('BROKER',
                    'AGENT',
                    'TLAS',
                    'DIRECT',
                    'TGA',
                    'BANCASSURA',
                    'TRAVEL'
                    )
                AND upper(C.[Responsibility Center]) NOT IN ('MNGAVALA','LAWYERS')
                AND ([Allocated Debits PR Amount] +[Allocated Debits CR Amount]+[Unallocated Amount])=[Original Amount]
                --  AND [Broker No] in ('020-10017')
                GROUP BY
                [Broker No],
                Name,
                C.No_,
                C.[Responsibility Center],
                C.[Customer Posting Group] 

            ''')
            df = pd.read_sql_query(
                query,
                connection,
                params={
                    'date': date,
                }
            )
            logger.info('successfully fetched data::')
            # df.to_excel('output_data/unallocated_receipts.xlsx')
            return df
    except Exception as e:
        logger.error(f'Error fetching the data::{e}')
    



