import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process
import re
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import fuzz
import numpy as np
from itertools import product
from datetime import datetime as dt
import pandas as pd
import numpy as np
import re
from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rfuzz  # Much faster than fuzzywuzzy
from rapidfuzz import process
from datetime import datetime
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

import pandas as pd
import re
from datetime import datetime as dt
from fuzzywuzzy import fuzz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def broker_reconciliation_v1(broker_statement, icea_statement, use_gross=False):
    """
    Reconcile broker statements with ICEA statements using multiple matching strategies.
    
    Args:
        broker_statement: DataFrame from broker
        icea_statement: DataFrame from ICEA
        use_gross: Boolean, if True use gross_amount, else net_amount
    
    Returns:
        tuple: (reconciled_df, unreconciled_df)
    """
    
    icea_statement = icea_statement.copy()
    broker_statement = broker_statement.copy()

    def clean_text(text):
        """Clean text for matching by removing special chars and normalizing."""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def preprocess_df(df, name_cols, rn_col, df_type):
        """Preprocess dataframe for matching."""
        df = df.copy()
        pattern = r'\b(limited|ltd|agencies|brokers|company|co|kltd)\b'

        # Handle multiple or single name columns
        if isinstance(name_cols, list):
            name_raw = df[name_cols].astype(str).agg(" ".join, axis=1)
        else:
            name_raw = df[name_cols].astype(str)

        df[f"name_clean_{df_type}"] = (
            name_raw.apply(clean_text)
                    .str.replace(pattern, "", regex=True)
                    .str.replace(" ", "", regex=False)
                    .str.strip()
        )

        df[f"rn_clean_{df_type}"] = (
            df[rn_col].astype(str).apply(clean_text)
                     .str.replace(pattern, "", regex=True)
                     .str.replace(" ", "", regex=False)
                     .str.strip()
        )
        
        # Use gross or net amount based on parameter
        amount_col = "gross_amount" if use_gross else "net_amount"
        if amount_col in df.columns:
            df[f"amount_{df_type}"] = df[amount_col]
        else:
            # Fallback to first available amount column
            amount_cols = [col for col in df.columns if 'premium' in col.lower() or 'amount' in col.lower() or 'gross' in col.lower() or 'net' in col.lower()]
            if amount_cols:
                df[f"amount_{df_type}"] = df[amount_cols[0]]
            else:
                df[f"amount_{df_type}"] = 0
        
        return df

    # Apply cleaning
    icea = preprocess_df(icea_statement, "Insured_name", "risk_note", "icea")
    broker = preprocess_df(broker_statement, "Insured_name", "risk_note", "broker")

    # Convert year & amounts
    try:
        icea["year"] = pd.to_datetime(icea["start_date"]).dt.year
        broker["year"] = pd.to_datetime(broker["start_date"]).dt.year
    except Exception as e:
        logger.warning(f"Date conversion failed: {e}, using current year")
        icea["year"] = dt.now().year
        broker["year"] = dt.now().year

    # 1. Exact match (risk note key cleaned)
    logger.info(f"Starting reconciliation: {len(broker)} broker records, {len(icea)} ICEA records")
    
    exact_rn_match = broker.merge(
        icea,
        left_on="rn_clean_broker",
        right_on="rn_clean_icea",
        how="inner",
        suffixes=("_brk", "_icea")
    )
    exact_rn_match["merged_on"] = "risk_note_exact"
    
    logger.info(f"Exact RN matches found: {len(exact_rn_match)}")

    # Remove matched rows for next layer
    matched_rn = exact_rn_match["rn_clean_broker"].unique()
    remaining_broker = broker[~broker["rn_clean_broker"].isin(matched_rn)]

    # 2. Fuzzy risk note matching
    fuzzy_rows = []
    for idx_b, row_b in remaining_broker.iterrows():
        # Filter icea candidates by year to reduce comparisons
        candidates = icea[
            icea["year"].between(row_b["year"] - 1, row_b["year"] + 1)
        ]

        for idx_i, row_i in candidates.iterrows():
            score = fuzz.token_set_ratio(row_b["rn_clean_broker"], row_i["rn_clean_icea"])
            if score >= 95:  # strong fuzzy threshold
                fuzzy_rows.append({
                    "rn_clean_broker": row_b["rn_clean_broker"],
                    "rn_clean_icea": row_i["rn_clean_icea"],
                    "risk_note_brk": row_b["risk_note"],
                    "risk_note_icea": row_i["risk_note"],
                    "amount_icea": row_i["amount_icea"],
                    "amount_broker": row_b["amount_broker"],
                    "insured_name_icea": row_i["Insured_name"],
                    "insured_name_brk": row_b["Insured_name"],
                    "merged_on": "risk_note_fuzzy",
                    "fuzzy_score_rn": score,
                    "amount_diff": row_i["amount_icea"] - row_b["amount_broker"]
                })
    
    fuzzy_rn_match = pd.DataFrame(fuzzy_rows)

    # Remove fuzzy matched rows
    matched_fuzzy = fuzzy_rn_match["rn_clean_broker"].unique() if not fuzzy_rn_match.empty else []
    remaining_broker2 = remaining_broker[
        ~remaining_broker["rn_clean_broker"].isin(matched_fuzzy)
    ]

    # 3. Name + Amount matching
    name_amount_rows = []
    for idx_b, row_b in remaining_broker2.iterrows():
        # Filter candidates by amount similarity
        candidates = icea[
            abs(icea["amount_icea"].astype(float) - float(row_b["amount_broker"])) <= 10
        ]

        for idx_i, row_i in candidates.iterrows():
            score = fuzz.token_set_ratio(row_b["name_clean_broker"], row_i["name_clean_icea"])
            if score >= 80:
                name_amount_rows.append({
                    "rn_clean_broker": row_b["rn_clean_broker"],
                    "rn_clean_icea": row_i["rn_clean_icea"],
                    "risk_note_brk": row_b["risk_note"],
                    "risk_note_icea": row_i["risk_note"],
                    "amount_icea": row_i["amount_icea"],
                    "amount_broker": row_b["amount_broker"],
                    "insured_name_icea": row_i["Insured_name"],
                    "insured_name_brk": row_b["Insured_name"],
                    "merged_on": "name_amount",
                    "fuzzy_score_name": score,
                    "amount_diff": row_i["amount_icea"] - row_b["amount_broker"]
                })

    name_amount_match = pd.DataFrame(name_amount_rows)
    if not name_amount_match.empty:
        name_amount_match = name_amount_match.drop_duplicates("rn_clean_broker")

    # Combine all matches
    all_matches_list = []
    
    if not exact_rn_match.empty:
        exact_subset = exact_rn_match[[
            "rn_clean_broker", "rn_clean_icea", "Insured_name_brk", "amount_broker",
            "amount_icea", "merged_on", "risk_note_brk", "risk_note_icea"
        ]].copy()
        exact_subset["fuzzy_score_rn"] = 100  # Exact match
        exact_subset["fuzzy_score_name"] = None
        exact_subset["amount_diff"] = exact_subset["amount_icea"] - exact_subset["amount_broker"]
        all_matches_list.append(exact_subset)
    
    if not fuzzy_rn_match.empty:
        all_matches_list.append(fuzzy_rn_match)
    
    if not name_amount_match.empty:
        all_matches_list.append(name_amount_match)

    # Create final matches
    if all_matches_list:
        final_matches = pd.concat(all_matches_list, ignore_index=True)
    else:
        final_matches = pd.DataFrame(columns=[
            "rn_clean_broker", "rn_clean_icea", "Insured_name_brk", "amount_broker",
            "amount_icea", "merged_on", "fuzzy_score_rn", "fuzzy_score_name", "amount_diff",
            "risk_note_brk", "risk_note_icea"
        ])

    # Prepare broker statement for merge
    broker_statement_clean = broker_statement.copy()
    broker_statement_clean["rn_clean_broker"] = (
        broker_statement_clean["risk_note"]
        .astype(str)
        .apply(clean_text)
        .str.replace(r'\b(limited|ltd|agencies|brokers|company|co|kltd)\b', "", regex=True)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )

    # Merge with original broker data
    final_reconciled = broker_statement_clean.merge(
        final_matches, on="rn_clean_broker", how="left"
    ).drop_duplicates().reset_index(drop=True)

    # Split reconciled vs unreconciled
    reconciled_mask = final_reconciled["merged_on"].notna()
    reconciled = final_reconciled[reconciled_mask]
    reconciled.dropna(subset=["rn_clean_broker"], inplace=True)
    unreconciled = final_reconciled[~reconciled_mask]

    logger.info(f"Reconciliation complete: {len(reconciled)} reconciled, {len(unreconciled)} unreconciled")
    
    return reconciled, unreconciled