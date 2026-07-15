import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup credentials and client


def read_google_sheet(file_name, sheet_name):
  try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("C:/Users/dkirungu/Documents/saved_queries/dbt-demos-392016-eb143eaf19f5.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(file_name)
    worksheet = sheet.worksheet(sheet_name)  

    # Convert to pandas DataFrame
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    logger.info(f'SUCCESSFULLY READING GOOGLESHEET')
  except Exception as e:
    logger.error(f"Error getting google sheet:: {e}") 

