"""
File Name: redemption_tracker.py

Description: Track redemption history to prevent duplicate processing
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

HISTORY_FILE = "redemption_history.txt"


def load_redemption_history() -> Dict[str, Any]:
    """
    Load redemption history from text file.
    
    """
    if not os.path.exists(HISTORY_FILE):
        return {
            "last_redemption_date": None,
            "last_redemption_hour": None,
            "history": []
        }
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading redemption history: {e}")
        return {
            "last_redemption_date": None,
            "last_redemption_hour": None,
            "history": []
        }


def save_redemption_history(history_data: Dict[str, Any]):
    """
    Save redemption history to text file.
    """
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving redemption history: {e}")


def add_redemption_record(
    reimburse_date: str,
    start_hour: int,
    end_hour: int,
    files_generated: list
) -> bool:
    """
    Add a new redemption record to history.
    
    Args:
        reimburse_date: Date in YYYYMMDD format
        start_hour: Starting hour (0-23)
        end_hour: Ending hour (0-23)
        files_generated: List of generated file names
    
    Returns:
        True if successful, False otherwise
    """
    history = load_redemption_history()
    
    # Create new record
    new_record = {
        "date": reimburse_date,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files_generated": files_generated
    }
    
    # Update history
    history["last_redemption_date"] = reimburse_date
    history["last_redemption_hour"] = end_hour
    history["history"].append(new_record)
    
    # Save to file
    save_redemption_history(history)
    
    return True


def check_duplicate_redemption(
    reimburse_date: str,
    start_hour: int,
    end_hour: int
) -> tuple[bool, Optional[str]]:
    """
    Check if redemption for this time range already exists.
    
    Time ranges are treated as half-open intervals [start, end).
    For example:
    - start_hour=12, end_hour=13 covers 12:00:00 to 12:59:59
    - start_hour=13, end_hour=15 covers 13:00:00 to 14:59:59
    
    Returns:
        (is_duplicate, error_message)
    """
    history = load_redemption_history()
    
    # Check against all historical records
    for record in history["history"]:
        if record["date"] == reimburse_date:
            # Check if time ranges overlap
            record_start = record["start_hour"]
            record_end = record["end_hour"]
            
            # Two ranges [a, b) and [c, d) do NOT overlap if:
            # - b <= c (first range ends at or before second range starts)
            # - d <= a (second range ends at or before first range starts)
            no_overlap = (end_hour <= record_start or record_end <= start_hour)
            
            if not no_overlap:
                # Calculate actual time range for error message
                actual_record_end = record_end - 1 if record_end > 0 else 23
                return True, (
                    f"Duplicate redemption detected! This time range overlaps with a previous redemption on {reimburse_date} "
                    f"({record_start:02d}:00 - {actual_record_end:02d}:59)"
                )
    
    return False, None


def get_last_redemption_info() -> Optional[Dict[str, Any]]:
    history = load_redemption_history()
    
    if not history["history"]:
        return None
    
    return history["history"][-1]
