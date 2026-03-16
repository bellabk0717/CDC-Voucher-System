# Voucher_claim_api.py
# ------------------------------------------------------------
# Voucher Claim (Count-based, no per-voucher codes)
#
# Data source: household_data.json (dict keyed by Household_ID)
# Update household_data.json by adding:
#   - voucher counts: "2": int, "5": int, "10": int
#   - tranche flags:  "2025 May": 0/1, "2026 Jan": 0/1
#
# API:
#   POST /api/voucher/claim
#     Body: {"Household_ID": "...", "Tranche_Time": "May 2025" or "Jan 2026"}
# ------------------------------------------------------------

import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple

from flask import Blueprint, request, jsonify

voucher_claim_bp = Blueprint("voucher_claim_bp", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOUSEHOLD_FILE = os.path.join(BASE_DIR, "household_data.json")

# Tranche -> denomination counts (from your spec table)
TRANCHE_CONFIG = {
    "May 2025":  {"2": 50, "5": 20, "10": 30},  # total $500
    "Jan 2026":  {"2": 30, "5": 12, "10": 18},  # total $300 (30*2 + 12*5 + 18*10 = 300)
}

# Store flags in household_data.json using these keys
TRANCHE_FLAG_KEY = {
    "May 2025": "2025 May",
    "Jan 2026": "2026 Jan",
}


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_households() -> Dict[str, Any]:
    if not os.path.exists(HOUSEHOLD_FILE):
        raise FileNotFoundError(f"household_data.json not found at: {HOUSEHOLD_FILE}")

    with open(HOUSEHOLD_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("household_data.json must be a dict keyed by Household_ID")

    return data


def _save_households(data: Dict[str, Any]) -> None:
    with open(HOUSEHOLD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_tranche(x: str) -> str:
    t = (x or "").strip().lower()
    if t in ("may 2025", "may2025", "2025 may", "2025may"):
        return "May 2025"
    if t in ("jan 2026", "january 2026", "jan2026", "2026 jan", "2026jan"):
        return "Jan 2026"
    return ""


def _ensure_claim_fields(rec: Dict[str, Any]) -> None:
    """
    Ensure voucher count fields and tranche flags exist.
    Counts are integers (number of vouchers left).
    Flags are 0/1 (whether that tranche has been claimed).
    """
    rec.setdefault("2", 0)
    rec.setdefault("5", 0)
    rec.setdefault("10", 0)

    # tranche flags
    rec.setdefault("2025 May", 0)
    rec.setdefault("2026 Jan", 0)

    # optional metadata
    rec.setdefault("last_claim_time", "")
    rec.setdefault("last_claim_tranche", "")


def claim_vouchers_count_based(household_id: str, tranche_time: str) -> Tuple[bool, str, Dict[str, Any]]:
    tranche = _normalize_tranche(tranche_time)
    if not tranche:
        return False, "Invalid Tranche_Time (use 'May 2025' or 'Jan 2026')", {}

    households = _load_households()

    if household_id not in households:
        return False, "Household_ID not found", {}

    rec = households[household_id]
    _ensure_claim_fields(rec)

    # Optional: only Active households can claim
    status = (rec.get("status") or "").strip().lower()
    if status and status != "active":
        return False, f"Household status is not Active: {rec.get('status')}", {}

    flag_key = TRANCHE_FLAG_KEY[tranche]
    if int(rec.get(flag_key, 0)) == 1:
        return False, f"Tranche already claimed: {flag_key}", {}

    # Apply tranche counts
    add = TRANCHE_CONFIG[tranche]
    rec["2"] = int(rec.get("2", 0)) + add["2"]
    rec["5"] = int(rec.get("5", 0)) + add["5"]
    rec["10"] = int(rec.get("10", 0)) + add["10"]

    # Mark tranche claimed
    rec[flag_key] = 1

    # Store metadata (optional but useful)
    rec["last_claim_time"] = _now_str()
    rec["last_claim_tranche"] = flag_key

    households[household_id] = rec
    _save_households(households)

    summary = {
        "Household_ID": household_id,
        "Tranche_Time": tranche,
        "flag_set": flag_key,
        "counts_added": add,
        "counts_now": {"2": rec["2"], "5": rec["5"], "10": rec["10"]},
        "claim_time": rec["last_claim_time"],
    }
    return True, "OK", summary


@voucher_claim_bp.route("/api/voucher/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "voucher_claim_bp is registered",
        "household_file": HOUSEHOLD_FILE
    }), 200


@voucher_claim_bp.route("/api/voucher/claim", methods=["POST"])
def api_voucher_claim():
    payload = request.get_json(silent=True) or {}
    household_id = (payload.get("Household_ID") or payload.get("household_id") or "").strip()
    tranche_time = (payload.get("Tranche_Time") or payload.get("Tranche_Time") or payload.get("tranche_time") or "").strip()

    if not household_id or not tranche_time:
        return jsonify({"status": "error", "message": "Household_ID and Tranche_Time are required"}), 400

    try:
        ok, msg, summary = claim_vouchers_count_based(household_id, tranche_time)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

    if not ok:
        return jsonify({"status": "error", "message": msg}), 400

    return jsonify({"status": "success", "summary": summary}), 200
