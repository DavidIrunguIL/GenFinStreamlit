import pandas as pd
import numpy as np
import glob
import logging
import warnings
from datetime import datetime as dt, timedelta

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class GetData:
    def __init__(self):
        pass

    def get_prem_reg(year,month):
        try:
            year_month = f"{year}{month:02d}"
            file_list = glob.glob(f"G:/Shared drives/FOOTPRINT EXTRACTS/Year {year}/PremiumRegister/*{year_month}*.xlsx")
            if file_list:
                df = pd.read_excel(file_list[0])
            else:
                df = pd.DataFrame()
                logger.warning(f"Error::No file found matching pattern")
        except Exception as e:
            df = pd.DataFrame()
            logger.error(f"Error getting prem_register::{e}")
        return df
    
    def get_upr_reg(year, month):
        logger.info('EXTRACTING UPR DATA')
        try:
            year_month = f"{year}{month:02d}"
            file_list = glob.glob(f"G:/Shared drives/FOOTPRINT EXTRACTS/Year {year}/UPR/*{year_month}*.xlsx")
            if file_list:
                df = pd.read_excel(file_list[0])
                logger.info("SUCCESSFULLY EXTRACTED UPR_DAC DATA")
            else:
                logger.warning(f"Error::No file found matching pattern")
        except Exception as e:
            logger.error(f"Error getting prem_register::{e}")
        return df