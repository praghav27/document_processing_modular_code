import os
import pandas as pd
from config import TABLES_DIR


class TableStorage:
    """Handle table-related storage operations"""
    
    def __init__(self):
        pass
    
    def save_table(self, df: pd.DataFrame, filename: str, table_index: int) -> str:
        """Save table as CSV file"""
        csv_filename = f"{filename}_table_{table_index}.csv"
        csv_path = os.path.join(TABLES_DIR, csv_filename)
        df.to_csv(csv_path, index=False)
        print(f"💾 Saved table {table_index}: {csv_path}")
        return csv_path