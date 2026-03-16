# bank_directory.py
# ------------------------------------------------------------
# Module 1: Bank Directory
# - Loads BankCode.csv (given by the assignment)
# - Builds in-memory lookup indexes for O(1) validation / resolve
# - Provides dropdown APIs for frontend:
#     GET /api/banks
#     GET /api/banks/<bank_code>/branches
#     GET /api/bank/resolve?bank_code=...&branch_code=...
# ------------------------------------------------------------

from flask import Blueprint, jsonify, request
import csv
import os
from typing import Dict, List, Tuple


# ============================================================
# Paths (IMPORTANT on Windows)
# ============================================================
# Use absolute path based on this file's directory to avoid
# issues when the working directory changes in VSCode / PyCharm.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANKCODE_CSV_PATH = os.path.join(BASE_DIR, "BankCode.csv")


# ============================================================
# In-memory Indexes (Single source of truth)
# ============================================================
# bank_code -> {bank_code, bank_name, swift_code, remarks}
banks_by_code: Dict[str, Dict[str, str]] = {}

# bank_code -> list of {branch_code, branch_name}
branches_by_bank: Dict[str, List[Dict[str, str]]] = {}

# (bank_code, branch_code) -> full resolve info
bank_branch_index: Dict[Tuple[str, str], Dict[str, str]] = {}


# ============================================================
# Utility Functions
# ============================================================

def zfill_branch_code(code: str) -> str:
    """
    Normalize branch code into 3-digit string:
      "1"  -> "001"
      "81" -> "081"
      "001" stays "001"

    Why:
    - Your Merchant.csv may have "81" but BankCode has "081".
    - If we don't normalize, lookups will fail.
    """
    code = (code or "").strip()
    digits = "".join(ch for ch in code if ch.isdigit())
    return digits.zfill(3)


def normalize_bank_code(code: str) -> str:
    """
    Normalize bank_code as digits-only string (no padding assumed).
    Example: " 7171 " -> "7171"
    """
    code = (code or "").strip()
    digits = "".join(ch for ch in code if ch.isdigit())
    return digits


def load_bank_directory(csv_path: str = BANKCODE_CSV_PATH) -> None:
    """
    Load BankCode.csv and build indexes.

    Output indexes:
    - banks_by_code[bank_code] -> bank info
    - branches_by_bank[bank_code] -> list of branches
    - bank_branch_index[(bank_code, branch_code)] -> bank+branch resolve info

    Why we do this:
    - Merchant registration needs to validate (bank_code, branch_code) fast.
    - Frontend needs bank/branch lists for dropdowns.
    """
    global banks_by_code, branches_by_bank, bank_branch_index

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"BankCode CSV not found: {csv_path}")

    # Reset indexes (useful if you ever want to reload)
    # Reset indexes WITHOUT rebinding (keep same dict object)
    banks_by_code.clear()
    branches_by_bank.clear()
    bank_branch_index.clear()


    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Expected columns:
        # Bank_Code, Bank_Name, Branch_Code, Branch_Name, SWIFT_Code, Remarks
        for row in reader:
            bank_code = normalize_bank_code(row.get("Bank_Code", ""))
            bank_name = (row.get("Bank_Name", "") or "").strip()

            branch_code = zfill_branch_code(row.get("Branch_Code", ""))
            branch_name = (row.get("Branch_Name", "") or "").strip()

            swift_code = (row.get("SWIFT_Code", "") or "").strip()
            remarks = (row.get("Remarks", "") or "").strip()

            # Skip incomplete rows
            if not bank_code or not bank_name or not branch_code or not branch_name:
                continue

            # 1) Store bank-level info once per bank_code
            if bank_code not in banks_by_code:
                banks_by_code[bank_code] = {
                    "bank_code": bank_code,
                    "bank_name": bank_name,
                    "swift_code": swift_code,
                    "remarks": remarks,
                }

            # 2) Append branch into bank's branch list
            branches_by_bank.setdefault(bank_code, [])
            branches_by_bank[bank_code].append({
                "branch_code": branch_code,
                "branch_name": branch_name,
            })

            # 3) Exact lookup for (bank_code, branch_code)
            bank_branch_index[(bank_code, branch_code)] = {
                "bank_code": bank_code,
                "bank_name": bank_name,
                "branch_code": branch_code,
                "branch_name": branch_name,
                "swift_code": swift_code,
                "remarks": remarks,
            }

    # Sort branches to keep UI dropdown stable and predictable
    for bc in branches_by_bank:
        branches_by_bank[bc].sort(key=lambda x: x["branch_code"])


# ============================================================
# Blueprint: Bank APIs
# ============================================================
# Blueprint allows this module to be "plugged into" app.py
bank_bp = Blueprint("bank_bp", __name__)


@bank_bp.route("/api/banks", methods=["GET"])
def api_get_banks():
    """
    Return the list of banks.
    Frontend can use this to populate bank dropdown.
    """
    banks = list(banks_by_code.values())
    banks.sort(key=lambda x: x["bank_code"])
    return jsonify({
        "status": "success",
        "count": len(banks),
        "banks": banks
    }), 200


@bank_bp.route("/api/banks/<bank_code>/branches", methods=["GET"])
def api_get_branches(bank_code: str):
    """
    Return branches under a given bank_code.
    Frontend can call this after selecting a bank.
    """
    bc = normalize_bank_code(bank_code)
    if bc not in banks_by_code:
        return jsonify({"status": "error", "message": "Bank not found"}), 404

    branches = branches_by_bank.get(bc, [])
    return jsonify({
        "status": "success",
        "bank": banks_by_code[bc],
        "count": len(branches),
        "branches": branches
    }), 200


@bank_bp.route("/api/bank/resolve", methods=["GET"])
def api_resolve_bank_branch():
    """
    Resolve (bank_code, branch_code) -> names + swift + remarks.

    Example:
      /api/bank/resolve?bank_code=7171&branch_code=1
    branch_code will be normalized to 001.
    """
    bank_code = normalize_bank_code(request.args.get("bank_code", ""))
    branch_code = zfill_branch_code(request.args.get("branch_code", ""))

    if not bank_code or not branch_code:
        return jsonify({
            "status": "error",
            "message": "bank_code and branch_code are required"
        }), 400

    key = (bank_code, branch_code)
    if key not in bank_branch_index:
        return jsonify({"status": "error", "message": "Bank+Branch not found"}), 404

    return jsonify({"status": "success", "data": bank_branch_index[key]}), 200
