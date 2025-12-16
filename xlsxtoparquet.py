import pandas as pd
import os

def convert_xlsx_to_parquet(input_file, output_file):
    """
    Reads an Excel file and saves it as a new Parquet file.
    
    Args:
        input_file (str): Path to the source .xlsx file.
        output_file (str): Desired path for the new .parquet file.
    """
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' was not found.")
        return

    try:
        print(f"Reading {input_file}...")
        
        # Read the Excel file into a Pandas DataFrame
        # engine='openpyxl' is the standard for .xlsx files
        df = pd.read_excel(input_file, engine='openpyxl')
        
        print(f"Data loaded. Shape: {df.shape}")
        print(f"Generating new Parquet file at: {output_file}...")

        # Write to Parquet
        # index=False prevents pandas from adding a separate index column unless you want it
        df.to_parquet(output_file, engine='pyarrow', index=False)
        
        print("Success! Conversion complete.")

    except Exception as e:
        print(f"An error occurred during conversion: {e}")

# --- Usage ---
if __name__ == "__main__":
    # Define your file paths here
    source_excel = r"C:\Users\MDC21\vsfiles\.vscode\Gshopping-tracker\google_shopping_brand_hits.xlsx"       # The existing file
    target_parquet = r"C:\Users\MDC21\vsfiles\.vscode\Gshopping-tracker\google_shopping_brand_hits.parquet" # The new file to be generated
    
    convert_xlsx_to_parquet(source_excel, target_parquet)