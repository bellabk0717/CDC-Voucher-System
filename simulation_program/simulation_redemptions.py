"""
File Name: simulation_redemptions.py

Description : Generate simulated hourly Transaction JSON files (TransactionYYYYMMDDHH.json).
Each file contains transaction records with voucher counts in Transaction.json format.
"""

import json
import random
import datetime
from pathlib import Path

# Configuration
NUM_DAYS = 2  # Number of days to simulate
MIN_TX_PER_HOUR = 10  # Minimum transactions per hour
MAX_TX_PER_HOUR = 15  # Maximum transactions per hour
START_DATE = datetime.date(2026, 1, 1)  # Start date for simulation
TX_COUNTER = 100001  # Starting transaction_ID number

# Merchant and household pools for simulation
NUM_MERCHANTS = 20  # Number of distinct simulated merchants
NUM_HOUSEHOLDS = 4  # Number of distinct simulated households


def format_datetime_str(date_obj: datetime.date, hour: int, minute: int, second: int) -> str:
    """
    Format transaction time as YYYY-MM-DD-hhmmss.
    """
    dt = datetime.datetime(
        year=date_obj.year,
        month=date_obj.month,
        day=date_obj.day,
        hour=hour,
        minute=minute,
        second=second,
    )
    return dt.strftime("%Y-%m-%d-%H%M%S")


def generate_voucher_combination():
    """
    Generate random voucher combination for a transaction.
    Returns tuple of (voucher_2_count, voucher_5_count, voucher_10_count, total_amount)
    """
    valid_combinations = [
        (1, 0, 0, 2),   # 1x$2 = $2
        (2, 0, 0, 4),   # 2x$2 = $4
        (0, 1, 0, 5),   # 1x$5 = $5
        (3, 0, 0, 6),   # 3x$2 = $6
        (1, 1, 0, 7),   # 1x$2 + 1x$5 = $7
        (4, 0, 0, 8),   # 4x$2 = $8
        (2, 1, 0, 9),   # 2x$2 + 1x$5 = $9
        (0, 0, 1, 10),  # 1x$10 = $10
        (0, 2, 0, 10),  # 2x$5 = $10
        (5, 0, 0, 10),  # 5x$2 = $10
        (1, 0, 1, 12),  # 1x$2 + 1x$10 = $12
        (1, 2, 0, 12),  # 1x$2 + 2x$5 = $12
        (6, 0, 0, 12),  # 6x$2 = $12
    ]
    return random.choice(valid_combinations)


def generate_single_transaction(date_obj: datetime.date, hour: int, tx_index: int):
    """
    Generate a single transaction record in Transaction.json format.
    """
    global TX_COUNTER

    # Generate transaction ID in format T + DateTime
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    dt_str = format_datetime_str(date_obj, hour, minute, second)
    transaction_id = f"T{dt_str.replace('-', '')}"

    # Choose merchant and household
    hh_numeric = random.randint(0, NUM_HOUSEHOLDS - 1)
    household_id = f"H{hh_numeric:011d}"
    merchant_idx = random.randint(1, NUM_MERCHANTS)
    merchant_id = f"M{merchant_idx:03d}"

    # Get voucher combination
    voucher_2, voucher_5, voucher_10, amount = generate_voucher_combination()

    # Payment status - all completed for simulation
    payment_status = "Completed"

    transaction = {
        "Transaction_ID": transaction_id,
        "Household_ID": household_id,
        "Merchant_ID": merchant_id,
        "Transaction_Date_Time": dt_str,
        "Voucher_2": voucher_2,
        "Voucher_5": voucher_5,
        "Voucher_10": voucher_10,
        "Amount_Redeemed": amount,
        "Payment_Status": payment_status
    }

    TX_COUNTER += 1
    return transaction


def generate_single_hour_data(date_obj: datetime.date, day_index: int, hour: int):
    """
    Generate transaction records for one hour.
    """
    num_transactions = random.randint(MIN_TX_PER_HOUR, MAX_TX_PER_HOUR)
    transactions = []

    for tx_index in range(1, num_transactions + 1):
        transaction = generate_single_transaction(
            date_obj=date_obj,
            hour=hour,
            tx_index=tx_index,
        )
        transactions.append(transaction)

    return transactions


def write_transaction_json(output_path: Path, transactions):
    """
    Write one hourly transaction JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=4, ensure_ascii=False)


def generate_transactions_for_days():
    """
    Generate transaction JSON files for NUM_DAYS starting from START_DATE.
    """
    base_dir = Path(__file__).resolve().parent
    current_date = START_DATE

    for day_index in range(NUM_DAYS):
        date_str = current_date.strftime("%Y%m%d")
        daily_output_dir = base_dir / f"Redeem{date_str}"
        daily_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Generating data for date: {current_date.isoformat()}")

        for hour in range(24):
            filename = f"Redeem{date_str}{hour:02d}.json"
            output_path = daily_output_dir / filename
            transactions = generate_single_hour_data(current_date, day_index, hour)
            write_transaction_json(output_path, transactions)
            print(
                f"  Hour {hour:02d}: wrote {len(transactions)} transactions "
                f"to {output_path.name}"
            )

        current_date += datetime.timedelta(days=1)

    print("Done. All transaction files generated.")


def main():
    """
    Entry point to generate simulated transaction JSON files.
    """
    generate_transactions_for_days()


if __name__ == "__main__":
    main()
