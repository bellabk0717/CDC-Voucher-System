"""
File Name: complete.py

Description: Complete script for merchant reimbursement processing with user inputs.
             Integrates LoadData.py and algorithm_avl_greedy.py

User inputs:
    - REIMBURSE_DATE (YYYYMMDD)
    - RUN_HOUR1 (current run hour)
    - RUN_HOUR2 (previous run hour)

Output:
    - Reimbursement CSV files grouped by bank (SWIFT code)
"""

import os
import sys
from datetime import datetime

from algorithm_avl_greedy import process_reimbursement_avlgreedy_main

def validate_date(date_str: str) -> bool:
    """
    Validate if date string is in YYYYMMDD format and represents a valid date.
    """
    if len(date_str) != 8 or not date_str.isdigit():
        return False
    
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def validate_hour(hour_str: str) -> bool:
    """
    Validate if hour string represents a valid hour (0-23).
    """
    try:
        hour = int(hour_str)
        return 0 <= hour <= 23
    except ValueError:
        return False

def get_user_inputs():
    """
    Get and validate user inputs for reimbursement processing.
    """
    print("=" * 70)
    print("CDC Voucher Reimbursement Processing System")
    print("=" * 70)
    
    # Get REIMBURSE_DATE
    while True:
        reimburse_date = input("Enter REIMBURSE_DATE (format: YYYYMMDD, e.g., 20260101): ").strip()
        
        if reimburse_date.lower() == 'exit':
            return None
        
        if validate_date(reimburse_date):
            break
        else:
            print("❌ Invalid date format. Please enter date in YYYYMMDD format.")
            print("Type 'exit' to quit.\n")
    
    # Get RUN_HOUR1 (current run time)
    while True:
        run_hour1_str = input("Enter RUN_HOUR1 (current run time, 0-23): ").strip()
        
        if run_hour1_str.lower() == 'exit':
            return None
        
        if validate_hour(run_hour1_str):
            run_hour1 = int(run_hour1_str)
            break
        else:
            print("❌ Invalid hour. Please enter a number between 0 and 23.")
            print("Type 'exit' to quit.\n")
    
    # Get RUN_HOUR2 (previous run time)
    while True:
        run_hour2_str = input("Enter RUN_HOUR2 (previous run time, 0-23): ").strip()
        
        if run_hour2_str.lower() == 'exit':
            return None
        
        if validate_hour(run_hour2_str):
            run_hour2 = int(run_hour2_str)
            break
        else:
            print("❌ Invalid hour. Please enter a number between 0 and 23.")
            print("Type 'exit' to quit.\n")
    
    # Get DATA_FOLDER
    data_folder = input("Enter DATA_FOLDER path (press Enter for current directory): ").strip()
    if data_folder.lower() == 'exit':
        return None
    if not data_folder:
        data_folder = "."
    print(f"Data folder set to: {data_folder}")
    
    # Get OUTPUT_FOLDER
    output_folder = input("Enter OUTPUT_FOLDER path (press Enter for current directory): ").strip()
    if output_folder.lower() == 'exit':
        return None
    if not output_folder:
        output_folder = "."
    print(f"Output folder set to: {output_folder}")

    return reimburse_date, run_hour1, run_hour2, data_folder, output_folder

def display_summary(reimburse_date: str, run_hour1: int, run_hour2: int, data_folder: str, output_folder: str):
    # Explain transaction time range
    if run_hour1 == run_hour2:
        print("Processing Mode: Daily run (24-hour cycle)")
        print(f"Transaction Range: Previous day {run_hour2:02d}:00 to current day {run_hour1-1:02d}:59")
    elif run_hour1 > run_hour2:
        print("Processing Mode: Same-day run")
        print(f"Transaction Range: Current day {run_hour2:02d}:00 to {run_hour1-1:02d}:59")
    else:
        print("Processing Mode: Overnight run (crosses midnight)")
        print(f"Transaction Range: Previous day {run_hour2:02d}:00 to current day {run_hour1-1:02d}:59")

def main():
    """
    Main function to run the complete reimbursement processing workflow.
    """
    # Get user inputs
    inputs = get_user_inputs()
    
    if inputs is None:
        print("\n Processing cancelled by user.")
        sys.exit(0)
    
    reimburse_date, run_hour1, run_hour2, data_folder, output_folder = inputs

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Display processing summary
    display_summary(reimburse_date, run_hour1, run_hour2, data_folder, output_folder)
    
    # Confirm before processing
    confirm = input("Do you want to proceed with processing? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("\n Processing cancelled by user.")
        sys.exit(0)
    
    print("Starting reimbursement processing...")
    
    try:
        # Run the processing algorithm
        generated_files = process_reimbursement_avlgreedy_main(
            reimburse_date=reimburse_date,
            current_run_hour=run_hour1,  # Pass as parameter (not used in new logic)
            run_hour1=run_hour1,
            run_hour2=run_hour2,
            data_folder=data_folder,
            output_folder=output_folder
        )
        
        # Display results
        print("✅ Processing Complete!")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print("=" * 70)
        print("❌ Error: Required data files not found")
        print(f"Details: {e}")
        print("Please ensure the following files/folders exist:")
        print(f"  - {data_folder}/BankCode.csv")
        print(f"  - {data_folder}/Merchant.csv")
        print(f"  - {data_folder}/Redeem{reimburse_date}/ (folder with hourly CSV files)")
        print("=" * 70)
        sys.exit(1)
        
    except Exception as e:
        print("=" * 70)
        print("❌ Error during processing")
        print(f"Details: {e}")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()