"""
File Name: simulation_merchants.py

Description : Generate simulated merchant JSON file (merchant_data.json).
Each merchant (M001 to M100) is associated with a random bank from BankCode.csv.
"""

import json
import random
import datetime
from pathlib import Path
import LoadData

BANKCODE_FILE = "BankCode.csv"  # Input bank code file
OUTPUT_FILE = "merchant_data.json"  # Output merchant file
NUM_MERCHANTS = 100  # Number of merchants to generate


def random_uen(i: int) -> str:
    """
    Generate a simple UEN-like string.
    Example pattern: 2025XXXXXXA.
    """
    year = random.randint(2010, 2025)
    seq = random.randint(10000, 99999)
    suffix = chr(ord("A") + (i % 26))
    return f"{year}{seq}{suffix}"


def random_account_number() -> str:
    """
    Generate a random account number string.
    The style loosely follows the assignment sample:
    - Either '123-456-789'
    - Or '4567890123'
    """
    style = random.choice(["dash", "plain"])
    if style == "dash":
        part1 = random.randint(100, 999)
        part2 = random.randint(100, 999)
        part3 = random.randint(100, 999)
        return f"{part1}-{part2}-{part3}"
    else:
        return "".join(str(random.randint(0, 9)) for _ in range(10))


def random_registration_date() -> str:
    """
    Generate a random registration date string in YYYY-MM-DD format.
    """
    base_date = datetime.date(2025, 10, 1)  # Start date
    delta_days = random.randint(0, 60)
    d = base_date + datetime.timedelta(days=delta_days)
    return d.isoformat()


def generate_merchant_dict(bankcodes, num_merchants: int):
    """
    Generate a dictionary of merchants (M001 to M100) using the given bank code records.
    Returns a dict where keys are merchant IDs and values are merchant data dicts.
    """
    merchants = {}

    for i in range(1, num_merchants + 1):
        merchant_id = f"M{i:03d}"  # e.g. M001
        merchant_name = f"Num {i:03d} Merchant LTD"

        # Randomly select one bank record
        bank = random.choice(bankcodes)
        bank_name = bank["Bank_Name"]
        bank_code = bank["Bank_Code"]
        branch_code = bank["Branch_Code"]
        branch_name = bank.get("Branch_Name", "Main Branch")
        swift_code = bank.get("SWIFT_Code", "")
        remarks = bank.get("Remarks", "FAST/GIRO Enabled")

        uen = random_uen(i)
        account_number = random_account_number()
        account_holder_name = f"Num {i:03d} Merchant LTD"
        registration_date = random_registration_date()
        status = "active"

        merchant_data = {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "uen": uen,
            "bank_code": bank_code,
            "bank_name": bank_name,
            "branch_code": branch_code,
            "branch_name": branch_name,
            "swift_code": swift_code,
            "remarks": remarks,
            "account_number": account_number,
            "account_holder_name": account_holder_name,
            "registration_date": registration_date,
            "status": status,
        }

        merchants[merchant_id] = merchant_data

    return merchants


def write_merchant_json(path: str, merchants_dict):
    """
    Write the merchant dictionary into merchant_data.json with proper formatting.
    """
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(merchants_dict, f, indent=2, ensure_ascii=False)


def main():
    """
    Entry point to generate merchant_data.json using BankCode.csv.
    """
    project_dir = Path(__file__).resolve().parent
    bankcode_path = project_dir / BANKCODE_FILE
    output_path = project_dir / OUTPUT_FILE

    print(f"Loading bank codes from: {bankcode_path}")
    bankcodes = LoadData.load_bankcodes(str(bankcode_path))

    print(f"Generating {NUM_MERCHANTS} merchants (M001 to M{NUM_MERCHANTS:03d})...")
    merchants = generate_merchant_dict(bankcodes, NUM_MERCHANTS)

    print(f"Writing merchants to: {output_path}")
    write_merchant_json(str(output_path), merchants)

    print("Done. Please check merchant_data.json in the current folder.")


if __name__ == "__main__":
    main()
