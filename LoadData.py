"""
File Name: LoadData.py

Description: Load and clean data from BankCode.csv, merchant_data.json, and Transaction JSON files.
"""

import csv
import json
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple
import os


def parse_amount(amount_value) -> float:
    """
    Parse amount value (can be int, float, or string).
    """
    try:
        if isinstance(amount_value, (int, float)):
            return float(amount_value)
        return float(str(amount_value).replace('$', '').strip())
    except (ValueError, AttributeError):
        return 0.0

    
def load_bankcodes(file_path: str) -> List[Dict[str, str]]:
    """
    Load bank information from BankCode.csv into a list of dicts.
    """
    bankcodes = []

    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # clean whitespace from each field
                clean_row = {
                    k: (v.strip() if isinstance(v, str) else v)
                    for k, v in row.items()
                }
                bankcodes.append(clean_row)
    
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        raise
        
    except Exception as e:
        print(f"An error occurred while reading BankCode file: {e}")
        raise
    
    return bankcodes


def load_merchant_json(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load merchant_data.json file into a list of dictionaries.
    
    Expected JSON format:
    {
      "M001": {...merchant data...},
      "M002": {...merchant data...}
    }
    """
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Convert dict to list of merchants
        merchants = []
        for merchant_id, merchant_data in data.items():
            # Ensure merchant_id is in the data
            merchant_data['merchant_id'] = merchant_id
            # Map to uppercase keys for compatibility
            merchant_data['Merchant_ID'] = merchant_id
            merchant_data['Merchant_Name'] = merchant_data.get('merchant_name', '')
            merchant_data['Bank_Code'] = str(merchant_data.get('bank_code', ''))
            merchant_data['Branch_Code'] = str(merchant_data.get('branch_code', ''))
            merchant_data['Account_Number'] = str(merchant_data.get('account_number', ''))
            merchants.append(merchant_data)
        
        return merchants

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"An error occurred while reading merchant JSON file: {e}")
        return None


def load_transactions_json(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load a JSON file containing transaction data.
    
    Expected JSON format: List of transaction objects
    [
      {
        "Transaction_ID": "T20260123192311",
        "Household_ID": "H91128044939",
        "Merchant_ID": "M001",
        "Transaction_Date_Time": "2026-01-23-192311",
        "Voucher_2": 1,
        "Voucher_5": 1,
        "Voucher_10": 0,
        "Amount_Redeemed": 7,
        "Payment_Status": "Completed"
      }
    ]
    """
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            transactions = json.load(file)
        
        # Process each transaction
        for tx in transactions:
            # Parse amount
            if 'Amount_Redeemed' in tx:
                tx['Amount_Redeemed_Float'] = parse_amount(tx['Amount_Redeemed'])
            
            # Parse transaction date/time (format: YYYY-MM-DD-HHMMSS)
            if 'Transaction_Date_Time' in tx:
                txn_dt = datetime.strptime(
                    tx['Transaction_Date_Time'],
                    '%Y-%m-%d-%H%M%S'
                )
                tx['Transaction_DateTime'] = txn_dt
                tx['Transaction_Date'] = txn_dt.date()
        
        return transactions
    
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"An error occurred while reading transaction JSON file: {e}")
        return None


def build_bank_swift_lookup(bank_list: List[Dict[str, str]]) -> Dict[Tuple[str, str], str]:
    """
    Build a dictionary for lookup of SWIFT code by (Bank_Code, Branch_Code).
    """
    if not bank_list:
        return {}

    swift_dict: Dict[Tuple[str, str], str] = {}

    for row in bank_list:
        bank_code = str(row.get('Bank_Code', '')).strip()
        branch_code = str(row.get('Branch_Code', '')).strip()
        swift_code = row.get('SWIFT_Code', '').strip()

        if bank_code and branch_code and swift_code:
            key = (bank_code, branch_code)
            swift_dict[key] = swift_code

    return swift_dict


def load_transactions_by_date_and_hour(
    transaction_date: str,
    data_folder: str,
    tran_folder: str,
    hour: int,
    start_date: str,
    end_date: str,
    start_hour: int,
    end_hour: int
) -> List[Dict[str, Any]]:
    """
    Load transactions from JSON file for a specific date and hour.
    File format: redeem{YYYYMMDD}{HH}.json
    """
    # Convert date strings to datetime for comparison
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    current_dt = datetime.strptime(transaction_date, '%Y%m%d')

    # Early hour filtering
    if current_dt == start_dt == end_dt:
        # Single-day range
        if not (start_hour <= hour <= end_hour):
            return []
    elif current_dt == start_dt:
        # First day
        if hour < start_hour:
            return []
    elif current_dt == end_dt:
        # Last day
        if hour > end_hour:
            return []

    # Build file path - changed from CSV to JSON
    # 使用 os.path.join 正确处理路径分隔符
    daily_folder = os.path.join(data_folder, tran_folder, f"Redeem{transaction_date}")
    filename = f"redeem{transaction_date}{hour:02d}.json"
    filepath = os.path.join(daily_folder, filename)

    if not os.path.exists(filepath):
        return []

    # Load JSON instead of CSV
    return load_transactions_json(filepath) or []


def load_transactions_by_time_range(
    start_date: str,
    end_date: str,
    start_hour: int,
    end_hour: int,
    data_folder: str = "."
) -> List[Dict[str, Any]]:
    """
    Load transaction records within a specified date and time range.
    """
    all_transactions: List[Dict[str, Any]] = []

    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')

    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y%m%d')

        for hour in range(0, 24):
            hourly_transactions = load_transactions_by_date_and_hour(
                transaction_date=date_str,
                data_folder=data_folder,
                tran_folder="transaction",
                hour=hour,
                start_date=start_date,
                end_date=end_date,
                start_hour=start_hour,
                end_hour=end_hour
            )

            if hourly_transactions:
                all_transactions.extend(hourly_transactions)

        current_dt += timedelta(days=1)

    return all_transactions


def calculate_transaction_time_range(
    reimburse_date: str, 
    current_run_hour: int,
    run_hour1: int,
    run_hour2: int
) -> Tuple[str, str, int, int]:
    """
    Calculate transaction time range between current run (RUN_HOUR1) and previous run (RUN_HOUR2).
    """
    reimburse_dt = datetime.strptime(reimburse_date, '%Y%m%d')
    
    if run_hour1 == run_hour2:
        # Run once per day
        start_dt = reimburse_dt - timedelta(days=1)
        end_dt = reimburse_dt
        start_hour = run_hour2
        end_hour = run_hour1 - 1
        
    elif run_hour1 > run_hour2:
        # Same day processing
        start_dt = reimburse_dt
        end_dt = reimburse_dt
        start_hour = run_hour2
        end_hour = run_hour1 - 1
        
    else:  # run_hour1 < run_hour2
        # Crosses midnight
        start_dt = reimburse_dt - timedelta(days=1)
        end_dt = reimburse_dt
        start_hour = run_hour2
        end_hour = run_hour1 - 1
    
    start_date = start_dt.strftime('%Y%m%d')
    end_date = end_dt.strftime('%Y%m%d')
    
    return start_date, end_date, start_hour, end_hour


def write_reimbursement_csv(
    bank_merchants: Dict[str, Dict[str, Dict[str, Any]]],
    reimburse_date: str,
    current_run_hour: int,
    output_folder: str = "."
) -> List[str]:
    """
    Write reimbursement CSV files with merchant-level aggregation.
    
    Input:
        bank_merchants:
            {
                SWIFT_Code: {
                    Merchant_ID: {
                        'merchant_id': str,
                        'merchant_info': dict,
                        'total_amount': float,
                        'transaction_ids': list
                    }
                }
            }
        reimburse_date: YYYYMMDD format
        current_run_hour: Current run hour for Reimburse_ID generation
    
    Returns:
        List of generated file names
    """
    generated_files: List[str] = []

    reimburse_date_formatted = (
        f"{reimburse_date[:4]}-{reimburse_date[4:6]}-{reimburse_date[6:]}"
    )

    date_folder = os.path.join(output_folder, reimburse_date)
    os.makedirs(date_folder, exist_ok=True)

    for swift_code, merchants in bank_merchants.items():
        total_count = len(merchants)
        file_suffix = f"{total_count:02d}"
        filename = f"{swift_code}_{reimburse_date}_{file_suffix}.csv"
        filepath = os.path.join(date_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Merchant_ID', 'Merchant_Name', 'Reimburse_ID',
                'Reimburse_Date', 'Amount_Reimbursed', 
                'Bank_Account', 'Remarks'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for merchant_id, merchant_data in merchants.items():
                merchant_info = merchant_data['merchant_info']
                
                # Generate Reimburse_ID: R + YYYYMMDDHH + merchant number
                # Extract merchant number from M001 -> 001
                merchant_num = merchant_id.replace('M', '').replace('m', '')
                reimburse_id = f"R{reimburse_date}{current_run_hour:02d}{merchant_num}"

                writer.writerow({
                    'Merchant_ID': merchant_id,
                    'Merchant_Name': merchant_info.get('Merchant_Name', ''),
                    'Reimburse_ID': reimburse_id,
                    'Reimburse_Date': reimburse_date_formatted,
                    'Amount_Reimbursed': f"{merchant_data['total_amount']:.2f}",
                    'Bank_Account': merchant_info.get('Account_Number', ''),
                    'Remarks': 'CDC Voucher'
                })
                
                # Store reimburse_id for updating transaction files
                merchant_data['reimburse_id'] = reimburse_id

        generated_files.append(filename)

    return generated_files


def update_transaction_json_with_reimburse_id(
    transaction_date: str,
    hour: int,
    merchant_reimburse_ids: Dict[str, str],
    data_folder: str = "."
):
    """
    Update transaction JSON file by adding reimburse_id to each transaction.
    
    Args:
        transaction_date: YYYYMMDD format
        hour: Hour of the transaction file
        merchant_reimburse_ids: Dict mapping merchant_id to reimburse_id
        data_folder: Base data folder
    """
    daily_folder = os.path.join(data_folder, f"Redeem{transaction_date}")
    filename = f"redeem{transaction_date}{hour:02d}.json"
    filepath = os.path.join(daily_folder, filename)

    if not os.path.exists(filepath):
        return

    # Read existing transactions
    with open(filepath, 'r', encoding='utf-8') as f:
        transactions = json.load(f)

    # Update each transaction with reimburse_id
    updated = False
    for tx in transactions:
        merchant_id = tx.get('Merchant_ID')
        if merchant_id in merchant_reimburse_ids:
            tx['Reimburse_ID'] = merchant_reimburse_ids[merchant_id]
            updated = True

    # Write back if updated
    if updated:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
