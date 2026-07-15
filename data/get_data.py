import pandas as pd
import numpy as np


def get_data():
    """Function to generate a sample DataFrame."""
    df = pd.DataFrame({
            "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
            "Amount": [10, 15, 7, 20, 12, 9],
            "City": ["Nairobi", "Nairobi", "Nairobi", "Mombasa", "Mombasa", "Mombasa"]
        })
    return df