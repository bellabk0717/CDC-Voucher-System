# 02_Merchant_api_call.py
# ------------------------------------------------------------
# Module 2: Merchant Repository (No-seed version)
#
# Purpose:
# - Provide a persistence layer for merchant records.
# - Maintain in-memory indexes for fast lookup:
#     1) merchants_by_id: merchant_id -> merchant_record
#     2) merchant_id_by_uen: UEN -> merchant_id  (for uniqueness check)
# - Support server restart recovery:
#     load_merchant_data() reads merchant_data.json into memory.
#     save_merchant_data() writes memory back to merchant_data.json.
#
# What this module does NOT do (by design):
# - No CSV seed import (removed).
# - No Flask routes / endpoints (routes belong to Module 3).
# ------------------------------------------------------------

import os
import json
from datetime import datetime
from typing import Dict, Any


# ============================================================
# File path configuration (important for Windows / IDE)
# ============================================================
# Use absolute path based on this file location so that
# the program still works when the working directory changes.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Main persistence file (flat-file JSON, used for restart recovery)
MERCHANT_JSON_PATH = os.path.join(BASE_DIR, "merchant_data.json")


# ============================================================
# In-memory indexes (single source of truth at runtime)
# ============================================================
# Primary index: O(1) lookup by merchant_id
merchants_by_id: Dict[str, Dict[str, Any]] = {}

# Secondary index: enforce UEN uniqueness quickly (also O(1))
merchant_id_by_uen: Dict[str, str] = {}


# ============================================================
# Normalization helpers (keep data consistent across modules)
# ============================================================

def normalize_uen(uen: str) -> str:
    """
    Normalize UEN for uniqueness checks.
    We keep it simple:
    - strip spaces
    - uppercase
    """
    return (uen or "").strip().upper()


def normalize_merchant_id(mid: str) -> str:
    """
    Normalize merchant_id format.

    Current chosen rule (consistent with your existing CSV style):
      - 'M' + 3 digits, e.g., M001, M037

    Examples:
      'm37'  -> 'M037'
      'M37'  -> 'M037'
      'M037' -> 'M037'
    """
    mid = (mid or "").strip().upper()
    if not mid:
        return ""

    if mid.startswith("M"):
        digits = "".join(ch for ch in mid[1:] if ch.isdigit())
        if digits:
            return "M" + digits.zfill(3)

    return mid


def normalize_bank_code(code: str) -> str:
    """
    Normalize bank_code as digits-only string.
    Example: ' 7171 ' -> '7171'
    """
    code = (code or "").strip()
    return "".join(ch for ch in code if ch.isdigit())


def zfill_branch_code(code: str) -> str:
    """
    Normalize branch_code into 3-digit string.
    Example:
      '1'  -> '001'
      '81' -> '081'

    This is critical because BankCode.csv uses 3-digit branch codes.
    """
    code = (code or "").strip()
    digits = "".join(ch for ch in code if ch.isdigit())
    return digits.zfill(3)


def normalize_status(status: str) -> str:
    """
    Normalize status into a controlled enum:
      - 'active'
      - 'suspended'

    Accept common variants:
      Active/ACTIVE -> active
      Inactive/Disabled -> suspended
    """
    s = (status or "").strip().lower()
    if s in ("active", "activated"):
        return "active"
    if s in ("suspended", "inactive", "disabled"):
        return "suspended"
    return "active"


def normalize_date_to_iso(date_str: str) -> str:
    """
    Convert date formats into ISO string: YYYY-MM-DD

    Accepts common formats:
      - 2025/10/15
      - 2025-10-15

    If parsing fails, fallback to today's date.
    """
    s = (date_str or "").strip()
    if not s:
        return datetime.today().strftime("%Y-%m-%d")

    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return datetime.today().strftime("%Y-%m-%d")


def normalize_account_number(acc: str) -> str:
    """
    Keep account number as a string.
    - Do NOT convert to int (leading zeros could be lost)
    - Remove spaces only
    """
    return (acc or "").strip().replace(" ", "")


# ============================================================
# Index maintenance
# ============================================================

def rebuild_uen_index() -> None:
    """
    Rebuild merchant_id_by_uen from merchants_by_id.

    Why:
    - After loading JSON, we need to reconstruct the secondary index.
    - This ensures UEN uniqueness checks remain O(1).
    """
    global merchant_id_by_uen
    merchant_id_by_uen = {}

    for mid, rec in merchants_by_id.items():
        uen = normalize_uen(rec.get("uen", ""))
        if uen:
            merchant_id_by_uen[uen] = mid


# ============================================================
# Persistence APIs: Load / Save
# ============================================================

def load_merchant_data(json_path: str = MERCHANT_JSON_PATH) -> None:
    """
    Load merchant_data.json into in-memory indexes.

    Supported JSON formats:
    1) Dict format:
       {
         "M001": {...},
         "M002": {...}
       }

    2) List format:
       [
         {"merchant_id":"M001", ...},
         {"merchant_id":"M002", ...}
       ]

    After load:
    - merchants_by_id is populated
    - merchant_id_by_uen is rebuilt
    - important fields are normalized
    """
    global merchants_by_id

    # If file does not exist, start with empty in-memory store.
    if not os.path.exists(json_path):
        merchants_by_id = {}
        rebuild_uen_index()
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    merchants_by_id = {}

    # Case 1: dict keyed by merchant_id
    if isinstance(data, dict):
        for k, v in data.items():
            mid = normalize_merchant_id(k)
            if isinstance(v, dict) and mid:
                v["merchant_id"] = mid
                merchants_by_id[mid] = v

    # Case 2: list of records
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                mid = normalize_merchant_id(item.get("merchant_id", ""))
                if mid:
                    item["merchant_id"] = mid
                    merchants_by_id[mid] = item

    # Normalize key fields after loading (data hygiene)
    for mid, rec in merchants_by_id.items():
        rec["merchant_id"] = mid
        rec["uen"] = normalize_uen(rec.get("uen", rec.get("UEN", "")))
        rec["bank_code"] = normalize_bank_code(rec.get("bank_code", rec.get("Bank_Code", "")))
        rec["branch_code"] = zfill_branch_code(rec.get("branch_code", rec.get("Branch_Code", "")))
        rec["status"] = normalize_status(rec.get("status", "active"))
        rec["registration_date"] = normalize_date_to_iso(
            rec.get("registration_date", rec.get("Registration_Date", ""))
        )
        rec["account_number"] = normalize_account_number(
            rec.get("account_number", rec.get("Account_Number", ""))
        )

    # Rebuild secondary index for UEN uniqueness checks
    rebuild_uen_index()


def save_merchant_data(json_path: str = MERCHANT_JSON_PATH) -> None:
    """
    Save in-memory merchants to merchant_data.json.

    We persist as a dict keyed by merchant_id because:
    - It matches our in-memory structure.
    - It makes merge/diff easier if you inspect the file.
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merchants_by_id, f, ensure_ascii=False, indent=2)

# ============================================================
# Module 3: Merchant Registration API (Service + Routes)
# ============================================================

from flask import Blueprint, jsonify, request
from datetime import datetime

# ---- Import bank directory indexes from Module 1 ----
# Bank_api.py should expose these variables/functions.
from Bank_api import (
    load_bank_directory,
    bank_branch_index,
    normalize_bank_code,
    zfill_branch_code,
)

# ---- Import repo functions and in-memory indexes from Module 2 ----
# If Module 2 code is inside THIS SAME FILE, you do NOT need these imports.
# If Module 2 is in another file, then import like:
# from Merchant_repo import merchants_by_id, merchant_id_by_uen, save_merchant_data, normalize_uen, normalize_account_number, normalize_status
#
# Here we assume Module 2 is already in Merchant_api.py, so we use them directly:
#   merchants_by_id
#   merchant_id_by_uen
#   save_merchant_data(...)
#   normalize_uen(...)
#   normalize_account_number(...)
#   normalize_status(...)

merchant_bp = Blueprint("merchant_bp", __name__)


# ============================================================
# Helper: generate next merchant_id (M001, M002, ...)
# ============================================================

def generate_next_merchant_id() -> str:
    """
    Generate the next merchant_id in format M### based on current in-memory data.
    Example: if existing max is M037, next is M038.

    Why:
    - Simple and deterministic.
    - Works without a database.
    """
    max_num = 0
    for mid in merchants_by_id.keys():
        # Expect format M###; safely extract digits
        if isinstance(mid, str) and mid.upper().startswith("M"):
            digits = "".join(ch for ch in mid[1:] if ch.isdigit())
            if digits:
                max_num = max(max_num, int(digits))
    return "M" + str(max_num + 1).zfill(3)


def today_iso_date() -> str:
    """Return today's date in ISO format YYYY-MM-DD."""
    return datetime.today().strftime("%Y-%m-%d")


# ============================================================
# Endpoint 1: Register merchant (from scratch)
# POST /api/merchants/register
# ============================================================

@merchant_bp.route("/api/merchants/register", methods=["POST"])
def register_merchant():
    """
    Register a new merchant account.

    Expected JSON input:
    {
      "merchant_name": "...",
      "uen": "...",
      "bank_code": "7171",
      "branch_code": "001",   # can be "1" -> will normalize to "001"
      "account_number": "...",
      "account_holder_name": "..."
    }

    Output:
    - Create merchant_id
    - Validate bank+branch via BankCode index
    - Persist to merchant_data.json
    - Return created merchant record
    """
    payload = request.get_json(silent=True) or {}

    # 1) Required fields check
    required_fields = [
        "merchant_name",
        "uen",
        "bank_code",
        "branch_code",
        "account_number",
        "account_holder_name",
    ]
    missing = [f for f in required_fields if not str(payload.get(f, "")).strip()]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    merchant_name = str(payload.get("merchant_name", "")).strip()
    uen = normalize_uen(payload.get("uen", ""))
    bank_code = normalize_bank_code(payload.get("bank_code", ""))
    branch_code = zfill_branch_code(payload.get("branch_code", ""))
    account_number = normalize_account_number(payload.get("account_number", ""))
    account_holder_name = str(payload.get("account_holder_name", "")).strip()

    # 2) UEN uniqueness check (O(1) using index)
    if uen in merchant_id_by_uen:
        existing_id = merchant_id_by_uen[uen]
        return jsonify({
            "status": "error",
            "message": "UEN already registered",
            "existing_merchant_id": existing_id
        }), 409

    # 3) Validate bank+branch exists in BankCode directory (O(1))
    key = (bank_code, branch_code)
    if key not in bank_branch_index:
        return jsonify({
            "status": "error",
            "message": "Invalid bank_code + branch_code (not found in BankCode directory)",
            "bank_code": bank_code,
            "branch_code": branch_code
        }), 404

    # Auto-fill bank/branch metadata from directory
    bank_info = bank_branch_index[key]
    bank_name = bank_info.get("bank_name", "")
    branch_name = bank_info.get("branch_name", "")
    swift_code = bank_info.get("swift_code", "")
    remarks = bank_info.get("remarks", "")

    # 4) Generate merchant_id and build record
    merchant_id = generate_next_merchant_id()

    record = {
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "uen": uen,
        "bank_code": bank_code,
        "bank_name": bank_name,
        "branch_code": branch_code,
        "branch_name": branch_name,
        "swift_code": swift_code,     # optional but useful downstream
        "remarks": remarks,           # optional reference
        "account_number": account_number,
        "account_holder_name": account_holder_name,
        "registration_date": today_iso_date(),
        "status": "active"            # default status at registration
    }

    # 5) Update in-memory indexes
    merchants_by_id[merchant_id] = record
    merchant_id_by_uen[uen] = merchant_id

    # 6) Persist to JSON
    save_merchant_data()  # uses default MERCHANT_JSON_PATH from Module 2

    return jsonify({
        "status": "success",
        "merchant": record
    }), 201


# ============================================================
# Endpoint 2: Get merchant by ID
# GET /api/merchants/<merchant_id>
# ============================================================

@merchant_bp.route("/api/merchants/<merchant_id>", methods=["GET"])
def get_merchant(merchant_id: str):
    """
    Retrieve merchant details by merchant_id.
    This is required for downstream redemption validation (O(1) lookup).
    """
    mid = normalize_merchant_id(merchant_id)
    if mid not in merchants_by_id:
        return jsonify({"status": "error", "message": "Merchant not found"}), 404

    return jsonify({"status": "success", "merchant": merchants_by_id[mid]}), 200


# ============================================================
# (Optional) Endpoint 3: List merchants
# GET /api/merchants?status=active
# ============================================================

@merchant_bp.route("/api/merchants", methods=["GET"])
def list_merchants():
    """
    List merchants (useful for debugging and dashboard later).
    Optional query params:
      - status=active/suspended
    """
    status = (request.args.get("status", "") or "").strip().lower()

    data = list(merchants_by_id.values())
    if status in ("active", "suspended"):
        data = [m for m in data if (m.get("status", "") == status)]

    return jsonify({
        "status": "success",
        "count": len(data),
        "merchants": data
    }), 200


# ============================================================
# (Optional) Endpoint 4: Update status
# PATCH /api/merchants/<merchant_id>/status
# ============================================================

@merchant_bp.route("/api/merchants/<merchant_id>/status", methods=["PATCH"])
def update_merchant_status(merchant_id: str):
    """
    Update merchant status (active <-> suspended).
    Useful for preventing redemption by suspended merchants.
    """
    mid = normalize_merchant_id(merchant_id)
    if mid not in merchants_by_id:
        return jsonify({"status": "error", "message": "Merchant not found"}), 404

    payload = request.get_json(silent=True) or {}
    new_status = normalize_status(payload.get("status", ""))

    # Only allow two states
    if new_status not in ("active", "suspended"):
        return jsonify({"status": "error", "message": "Invalid status"}), 400

    merchants_by_id[mid]["status"] = new_status
    save_merchant_data()

    return jsonify({"status": "success", "merchant": merchants_by_id[mid]}), 200
