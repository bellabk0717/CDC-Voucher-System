import flet as ft
import json
import os
import glob
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# ==========================================
# Path Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE_URL = "http://127.0.0.1:8000"
HOUSEHOLD_DATA_FILE = os.path.join(BASE_DIR, "household_data.json")
MERCHANT_DATA_FILE = os.path.join(BASE_DIR, "merchant_data.json")
TX_ROOT_DIR = os.path.join(BASE_DIR, "transaction")
if not os.path.exists(TX_ROOT_DIR):
    os.makedirs(TX_ROOT_DIR)

VOUCHER_DIR = os.path.join(BASE_DIR, "voucher_selections")
if not os.path.exists(VOUCHER_DIR):
    os.makedirs(VOUCHER_DIR)

TRANCHE_CONFIG = {
    "2025 May": {"2": 50, "5": 20, "10": 30, "total": 500, "expiry": "2025-12-31"},
    "2026 Jan": {"2": 30, "5": 12, "10": 18, "total": 300, "expiry": "2026-12-31"},
}

# ==========================================
# Data Manager Class (OOP) - Using API calls
# ==========================================
class DataManager:
    @staticmethod
    def load_households() -> Dict:
        """Load all household data from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/household/api/all", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("households", {})
            return {}
        except Exception as e:
            print(f"Error loading households from API: {e}")
            return {}

    @staticmethod
    def get_household(household_id: str) -> Dict:
        """Get specific household data from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/household/api/{household_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Error getting household from API: {e}")
            return {}

    @staticmethod
    def save_households(data: Dict):
        """Save household data - Updates each household via API"""
        print("Warning: save_households called - this will update all households via API")
        for household_id, household_data in data.items():
            try:
                response = requests.post(
                    f"{API_BASE_URL}/household/api/update/{household_id}",
                    json={
                        "2": household_data.get("2", 0),
                        "5": household_data.get("5", 0),
                        "10": household_data.get("10", 0)
                    },
                    timeout=5
                )
                if response.status_code != 200:
                    print(f"Failed to update household {household_id}")
            except Exception as e:
                print(f"Error updating household {household_id}: {e}")

    @staticmethod
    def load_merchants() -> Dict:
        """Load all merchant data from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/merchants", timeout=5)
            if response.status_code == 200:
                data = response.json()
                merchants_list = data.get("merchants", [])
                return {m["merchant_id"]: m for m in merchants_list}
            return {}
        except Exception as e:
            print(f"Error loading merchants from API: {e}")
            return {}

    @staticmethod
    def save_transaction(tx: Dict):
        """
        Save transaction rules:
        Folder: transaction/redeemYYYYMMDD/
        Filename: RedeemYYYYMMDDHH.json
        """
        now = datetime.now()
        date_folder = f"redeem{now.strftime('%Y%m%d')}"
        hour_file = f"Redeem{now.strftime('%Y%m%d%H')}.json"
        
        target_dir = os.path.join(TX_ROOT_DIR, date_folder)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, hour_file)
        
        data = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        data.append(tx)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get_banks() -> list:
        """Get list of banks from API"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/banks", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("banks", [])
            return []
        except Exception as e:
            print(f"Error loading banks from API: {e}")
            return []

    @staticmethod
    def get_branches(bank_code: str) -> list:
        """Get branches for a specific bank"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/banks/{bank_code}/branches", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("branches", [])
            return []
        except Exception as e:
            print(f"Error loading branches from API: {e}")
            return []

# ==========================================
# Business Logic and Interface
# ==========================================
def main(page: ft.Page):
    page.title = "CDC Redemption App"
    page.window.width = 400
    page.window.height = 750
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    state = {
        "current_id": "",
        "role": "",
        "vouchers": {},
        "selected_bank_code": "",
        "banks_list": [],
        "branches_list": [],
        "admin_authenticated": False  # Track admin authentication locally
    }

    def show_msg(text, is_err=False):
        sb = ft.SnackBar(ft.Text(text), bgcolor="red" if is_err else "green")
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def switch_view(view_name):
        page.clean()
        page.appbar = None
        if view_name == "role_select":
            go_to_role_select()
        elif view_name == "household_login":
            go_to_login("household")
        elif view_name == "merchant_login":
            go_to_login("merchant")
        elif view_name == "admin_login":
            go_to_login("admin")
        elif view_name == "admin_dashboard":
            go_to_admin_dashboard()
        elif view_name == "admin_redemption":
            go_to_admin_redemption()
        elif view_name == "admin_reimbursement":
            go_to_admin_reimbursement()
        page.update()

    # ------------------------------------------
    # Role Selection
    # ------------------------------------------
    def go_to_role_select():
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("CDC SYSTEM", size=32, weight="bold"),
                    ft.Text("Please select your role"),
                    ft.ElevatedButton("Household User", width=250, on_click=lambda _: switch_view("household_login")),
                    ft.ElevatedButton("Merchant", width=250, on_click=lambda _: switch_view("merchant_login")),
                    ft.ElevatedButton("Admin", width=250, on_click=lambda _: switch_view("admin_login"), bgcolor="orange", color="white"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ------------------------------------------
    # Login
    # ------------------------------------------
    def go_to_login(role):
        state["role"] = role
        if role == "admin":
            password_input = ft.TextField(label="Admin Password", width=300, password=True)
            def admin_login_click(e):
                if password_input.value == "Admin":
                    state["admin_authenticated"] = True
                    go_to_admin_dashboard()
                else:
                    show_msg("Invalid admin password", True)
            
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("ADMIN LOGIN(Password: Admin)", size=24, weight="bold"),
                        password_input,
                        ft.ElevatedButton("Sign In", on_click=admin_login_click),
                        ft.TextButton("Back", on_click=lambda _: switch_view("role_select"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=50
                )
            )
            return

        label = "Household ID" if role == "household" else "Merchant ID"
        id_input = ft.TextField(label=label, width=300)

        def login_click(e):
            input_val = id_input.value.strip()
            if role == "household":
                households = DataManager.load_households()
                if input_val in households:
                    state["current_id"] = input_val
                    go_to_household_dashboard()
                else: 
                    show_msg("Household ID not found", True)
            else:
                merchants = DataManager.load_merchants()
                if input_val in merchants:
                    state["current_id"] = input_val
                    go_to_merchant_dashboard()
                else: 
                    show_msg("Merchant ID not found", True)

        def signup_click(e):
            if role == "household":
                go_to_household_signup()
            else:
                go_to_merchant_signup()

        controls = [
            ft.Text("LOGIN", size=24, weight="bold"),
            id_input,
            ft.ElevatedButton("Sign In", on_click=login_click),
        ]
        
        controls.append(ft.TextButton("Sign Up", on_click=signup_click, style=ft.ButtonStyle(color="blue")))
        controls.append(ft.TextButton("Back", on_click=lambda _: switch_view("role_select")))

        page.add(
            ft.Container(
                content=ft.Column(
                    controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ------------------------------------------
    # Sign Up (for Household)
    # ------------------------------------------
    def go_to_household_signup():
        page.clean()
        name_input = ft.TextField(label="Name", width=300)
        nric_input = ft.TextField(label="FIN/NRIC", width=300)
        email_input = ft.TextField(label="Email", width=300)

        def submit_signup(e):
            name = name_input.value.strip()
            nric = nric_input.value.strip()
            email = email_input.value.strip()

            if not name or not nric or not email:
                show_msg("All fields are required", True)
                return

            try:
                response = requests.post(
                    f"{API_BASE_URL}/household/register",
                    data={
                        "name": name,
                        "nric": nric.upper(),
                        "email": email
                    },
                    timeout=10
                )

                if response.status_code == 200 and "Household ID" in response.text:
                    households = DataManager.load_households()
                    new_hid = None
                    for hid, hdata in households.items():
                        if hdata.get("email", "").lower() == email.lower():
                            new_hid = hid
                            break
                    
                    if not new_hid:
                        show_msg("Registration successful but couldn't retrieve ID", True)
                        return

                    show_msg(f"Account created! Your Household ID: {new_hid}")
                elif "already registered" in response.text.lower():
                    if "email" in response.text.lower():
                        show_msg("Email already registered", True)
                    else:
                        show_msg("FIN already registered", True)
                    return
                else:
                    show_msg("Registration failed. Please try again.", True)
                    return
            except Exception as e:
                show_msg(f"Error: {str(e)}", True)
                return

            page.clean()
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("REGISTRATION SUCCESSFUL", size=24, weight="bold", color="green"),
                        ft.Text(f"Your Household ID:", size=16),
                        ft.Text(f"{new_hid}", size=20, weight="bold", color="blue"),
                        ft.Text("Please save this ID for login", size=12, color="gray"),
                        ft.ElevatedButton("Go to Login", on_click=lambda _: switch_view("household_login"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=50
                )
            )
            page.update()

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("SIGN UP", size=24, weight="bold"),
                    ft.Text("Create New Household Account", size=14, color="gray"),
                    name_input,
                    nric_input,
                    email_input,
                    ft.ElevatedButton("Create Account", on_click=submit_signup),
                    ft.TextButton("Back to Login", on_click=lambda _: switch_view("household_login"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ------------------------------------------
    # Sign Up (for Merchant) - Use Bank/Branch Names
    # ------------------------------------------
    def go_to_merchant_signup():
        page.clean()
        merchant_name_input = ft.TextField(label="Merchant Name", width=300)
        uen_input = ft.TextField(label="UEN", width=300)

        # Load banks
        state["banks_list"] = DataManager.get_banks()
        bank_options = [ft.dropdown.Option(f"{b['bank_name']} ({b['bank_code']})") for b in state["banks_list"]]

        branch_dropdown = ft.Dropdown(
            label="Select Branch",
            width=300,
            options=[],
            disabled=True
        )

        account_number_input = ft.TextField(label="Account Number", width=300)
        account_holder_input = ft.TextField(label="Account Holder Name", width=300)

        def load_branches_click(e):
            selected_text = bank_dropdown.value
            if not selected_text:
                show_msg("Please select a bank first", True)
                return

            # Extract bank_code from selection
            bank_code = selected_text.split("(")[-1].strip(")")
            state["selected_bank_code"] = bank_code

            # Load branches for selected bank
            branches = DataManager.get_branches(bank_code)

            if not branches:
                show_msg("No branches found for this bank", True)
                return

            state["branches_list"] = branches
            branch_dropdown.options = [
                ft.dropdown.Option(f"{br['branch_name']} ({br['branch_code']})")
                for br in branches
            ]
            branch_dropdown.disabled = False
            branch_dropdown.value = None
            show_msg(f"Loaded {len(branches)} branches")
            page.update()

        bank_dropdown = ft.Dropdown(
            label="Select Bank",
            width=300,
            options=bank_options
        )

        load_branches_btn = ft.TextButton("Load Branches", on_click=load_branches_click)

        def submit_merchant_signup(e):
            merchant_name = merchant_name_input.value.strip()
            uen = uen_input.value.strip()
            account_number = account_number_input.value.strip()
            account_holder = account_holder_input.value.strip()

            if not all([merchant_name, uen, bank_dropdown.value, branch_dropdown.value, account_number, account_holder]):
                show_msg("All fields are required", True)
                return

            # Extract codes from dropdown values
            bank_code = state["selected_bank_code"]
            branch_text = branch_dropdown.value
            branch_code = branch_text.split("(")[-1].strip(")")

            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/merchants/register",
                    json={
                        "merchant_name": merchant_name,
                        "uen": uen,
                        "bank_code": bank_code,
                        "branch_code": branch_code,
                        "account_number": account_number,
                        "account_holder_name": account_holder
                    },
                    timeout=10
                )

                if response.status_code == 201:
                    data = response.json()
                    merchant_id = data.get("merchant", {}).get("merchant_id")
                    
                    page.clean()
                    page.add(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("REGISTRATION SUCCESSFUL", size=24, weight="bold", color="green"),
                                ft.Text(f"Your Merchant ID:", size=16),
                                ft.Text(f"{merchant_id}", size=20, weight="bold", color="blue"),
                                ft.Text("Please save this ID for login", size=12, color="gray"),
                                ft.ElevatedButton("Go to Login", on_click=lambda _: switch_view("merchant_login"))
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.Alignment(0, 0),
                            expand=True,
                            padding=50
                        )
                    )
                    page.update()
                elif response.status_code == 409:
                    data = response.json()
                    show_msg(data.get("message", "UEN already registered"), True)
                elif response.status_code == 404:
                    show_msg("Invalid bank code or branch code", True)
                else:
                    data = response.json()
                    show_msg(data.get("message", "Registration failed"), True)
            except Exception as e:
                show_msg(f"Error: {str(e)}", True)

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("MERCHANT SIGN UP", size=24, weight="bold"),
                    ft.Text("Create New Merchant Account", size=14, color="gray"),
                    merchant_name_input,
                    uen_input,
                    bank_dropdown,
                    load_branches_btn,
                    branch_dropdown,
                    account_number_input,
                    account_holder_input,
                    ft.ElevatedButton("Create Account", on_click=submit_merchant_signup),
                    ft.TextButton("Back to Login", on_click=lambda _: switch_view("merchant_login"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ==========================================
    # HOUSEHOLD Module (keeping existing code)
    # ==========================================
    qty_inputs: Dict[str, ft.TextField] = {}

    def go_to_claim_voucher():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text(f"Claim Voucher"))

        h_all = DataManager.load_households()
        h_data = h_all[state["current_id"]]

        may_2025_claimed = h_data.get("2025 May", 0) == 1
        jan_2026_claimed = h_data.get("2026 Jan", 0) == 1

        def claim_may_2025(e):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/voucher/claim",
                    json={
                        "Household_ID": state["current_id"],
                        "Tranche_Time": "May 2025"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        show_msg("May 2025 voucher claimed successfully!")
                        show_success_screen("2025 May")
                    else:
                        show_msg(data.get("message", "Claim failed"), True)
                elif response.status_code == 400:
                    data = response.json()
                    show_msg(data.get("message", "Already claimed"), True)
                else:
                    show_msg("Failed to claim voucher. Please try again.", True)
            except Exception as e:
                show_msg(f"Error: {str(e)}", True)

        def claim_jan_2026(e):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/voucher/claim",
                    json={
                        "Household_ID": state["current_id"],
                        "Tranche_Time": "Jan 2026"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        show_msg("January 2026 voucher claimed successfully!")
                        show_success_screen("2026 Jan")
                    else:
                        show_msg(data.get("message", "Claim failed"), True)
                elif response.status_code == 400:
                    data = response.json()
                    show_msg(data.get("message", "Already claimed"), True)
                else:
                    show_msg("Failed to claim voucher. Please try again.", True)
            except Exception as e:
                show_msg(f"Error: {str(e)}", True)

        def show_success_screen(tranche_key):
            page.clean()
            page.appbar = ft.AppBar(title=ft.Text(f"Claim Voucher"))
            
            tranche_config = TRANCHE_CONFIG[tranche_key]
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("SUCCESS", size=28, weight="bold", color="green"),
                        ft.Text(f"{tranche_key} voucher claimed successfully!", size=16, color="green"),
                        ft.Divider(height=20),
                        ft.Text("Vouchers Added:", size=18, weight="bold"),
                        ft.Text(f"$2 Vouchers: {tranche_config['2']} pcs", size=14),
                        ft.Text(f"$5 Vouchers: {tranche_config['5']} pcs", size=14),
                        ft.Text(f"$10 Vouchers: {tranche_config['10']} pcs", size=14),
                        ft.Text(f"Total Value: ${tranche_config['total']}", size=16, weight="bold", color="blue"),
                        ft.Divider(height=20),
                        ft.ElevatedButton("Back to Dashboard", on_click=lambda _: go_to_household_dashboard(), width=250)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=50
                )
            )
            page.update()

        may_card = ft.Container(
            content=ft.Column([
                ft.Text("May 2025 Tranche", size=18, weight="bold"),
                ft.Text("Total Value: $500", size=14),
                ft.Divider(height=10),
                ft.Text("$2 x 50 vouchers", size=12),
                ft.Text("$5 x 20 vouchers", size=12),
                ft.Text("$10 x 30 vouchers", size=12),
                ft.Divider(height=10),
                ft.ElevatedButton(
                    "Already Claimed" if may_2025_claimed else "Claim May 2025 Voucher",
                    on_click=claim_may_2025,
                    disabled=may_2025_claimed,
                    width=250,
                    bgcolor="green" if not may_2025_claimed else "gray",
                    color="white"
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            border=ft.border.all(2, "green" if not may_2025_claimed else "gray"),
            border_radius=10,
            margin=10,
            bgcolor="#fff8e1" if not may_2025_claimed else "#f5f5f5"
        )

        jan_card = ft.Container(
            content=ft.Column([
                ft.Text("January 2026 Tranche", size=18, weight="bold", color="blue"),
                ft.Text("Total Value: $300", size=14),
                ft.Divider(height=10),
                ft.Text("$2 x 30 vouchers", size=12),
                ft.Text("$5 x 12 vouchers", size=12),
                ft.Text("$10 x 18 vouchers", size=12),
                ft.Divider(height=10),
                ft.ElevatedButton(
                    "Already Claimed" if jan_2026_claimed else "Claim January 2026 Voucher",
                    on_click=claim_jan_2026,
                    disabled=jan_2026_claimed,
                    width=250,
                    bgcolor="green" if not jan_2026_claimed else "gray",
                    color="white"
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            border=ft.border.all(2, "green" if not jan_2026_claimed else "gray"),
            border_radius=10,
            margin=10,
            bgcolor="#f0fff0" if not jan_2026_claimed else "#f5f5f5"
        )

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("Claim Your Vouchers", size=24, weight="bold"),
                    ft.Text("Select a tranche to claim", size=14, color="gray"),
                    ft.Divider(height=20),
                    may_card,
                    jan_card,
                    ft.Divider(height=20),
                    ft.TextButton("Back to Dashboard", on_click=lambda _: go_to_household_dashboard())
                ], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    def go_to_household_dashboard():
        page.clean()
        h_all = DataManager.load_households()
        h_data = h_all[state["current_id"]]

        user_name = h_data.get("name", "User")
        household_id = h_data.get("household_id", state["current_id"])

        page.appbar = ft.AppBar(title=ft.Text(f"{user_name} - {household_id}"))

        existed = {"2": 0, "5": 0, "10": 0}
        if h_data.get("2025 May") == 1:
            for k in existed: 
                existed[k] += TRANCHE_CONFIG["2025 May"][k]
        if h_data.get("2026 Jan") == 1:
            for k in existed: 
                existed[k] += TRANCHE_CONFIG["2026 Jan"][k]

        balance = {"2": int(h_data.get("2", 0)), "5": int(h_data.get("5", 0)), "10": int(h_data.get("10", 0))}
        used = {k: existed[k] - balance[k] for k in existed}

        total_balance = (balance["2"] * 2) + (balance["5"] * 5) + (balance["10"] * 10)

        has_claimed_vouchers = h_data.get("2025 May", 0) == 1 or h_data.get("2026 Jan", 0) == 1

        def create_voucher_row(denom):
            qty_inputs[denom] = ft.TextField(value="0", width=60, read_only=True, text_align="center")
            def change_qty(d):
                cur = int(qty_inputs[denom].value)
                new_v = cur + d
                if 0 <= new_v <= balance[denom]:
                    qty_inputs[denom].value = str(new_v)
                    page.update()
                elif new_v > balance[denom]:
                    show_msg(f"Not enough ${denom} vouchers", True)

            return ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text(f"${denom} Voucher", weight="bold"), ft.Text(f"Available: {balance[denom]}")], alignment="spaceBetween"),
                    ft.Row([ft.Text(f"Total: {existed[denom]}"), ft.Text(f"Used: {used[denom]}")], alignment="spaceBetween"),
                    ft.Row([
                        ft.ElevatedButton("-", on_click=lambda _: change_qty(-1)),
                        qty_inputs[denom],
                        ft.ElevatedButton("+", on_click=lambda _: change_qty(1))
                    ], alignment="center")
                ]),
                padding=10, border=ft.border.all(1, "#CCCCCC"), border_radius=8, margin=5
            )

        def generate_txt_click(e):
            q2, q5, q10 = qty_inputs["2"].value, qty_inputs["5"].value, qty_inputs["10"].value
            if q2 == "0" and q5 == "0" and q10 == "0":
                show_msg("Select at least one voucher", True)
                return

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{ts}_CDC_{state['current_id']}.txt"
            full_path = os.path.join(VOUCHER_DIR, fname)
            content = f"{state['current_id']}, $2, {q2}, $5, {q5}, $10, {q10}"

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            page.clean()
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("SUCCESS", size=24, weight="bold", color="green"),
                        ft.Text(f"Saved to: voucher_selections/"),
                        ft.Text(f"Filename: {fname}"),
                        ft.Text(f"Content: {content}"),
                        ft.ElevatedButton("Done", on_click=lambda _: switch_view("role_select"))
                    ], horizontal_alignment="center"),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=50
                )
            )
            page.update()

        column_contents = [
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Total Balance: ${total_balance}", size=24, weight="bold", color="blue"),
                    ft.Text(f"$2 x {balance['2']} | $5 x {balance['5']} | $10 x {balance['10']}", size=14, color="gray")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(10, 10, 10, 20)
            ),
            ft.ElevatedButton("Claim Voucher", width=300, on_click=lambda _: go_to_claim_voucher(), bgcolor="blue", color="white"),
            ft.Divider(height=20)
        ]

        if has_claimed_vouchers:
            if balance["2"] == 0 and balance["5"] == 0 and balance["10"] == 0:
                column_contents.extend([
                    ft.Text("Your Vouchers", size=18, weight="bold"),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("⚠ Vouchers claimed but not showing?", size=14, color="orange", weight="bold"),
                            ft.Text("Try going back to claim page and returning", size=12, color="gray"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=10,
                        border=ft.border.all(1, "orange"),
                        border_radius=8,
                        margin=10
                    )
                ])
            else:
                column_contents.extend([
                    ft.Text("Your Vouchers", size=18, weight="bold"),
                    create_voucher_row("2"),
                    create_voucher_row("5"),
                    create_voucher_row("10"),
                    ft.ElevatedButton("Generate Voucher TXT", width=300, on_click=generate_txt_click),
                ])
        else:
            column_contents.append(
                ft.Text("No vouchers claimed yet. Click 'Claim Voucher' to get started!", size=14, color="gray", text_align="center")
            )

        column_contents.append(ft.TextButton("Logout", on_click=lambda _: switch_view("role_select")))

        page.add(
            ft.Container(
                content=ft.Column(
                    column_contents,
                    scroll="auto",
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ==========================================
    # MERCHANT Module
    # ==========================================
    def go_to_merchant_dashboard():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text(f"Merchant: {state['current_id']}"))

        target_h_id = ft.TextField(label="Enter Household ID to scan", width=300)
        result_area = ft.Column()

        def scan_txt_click(e):
            hid = target_h_id.value.strip()
            files = glob.glob(os.path.join(VOUCHER_DIR, f"*_CDC_{hid}.txt"))
            if not files:
                show_msg(f"No TXT found in voucher_selections/ for {hid}", True)
                return

            latest_file = max(files, key=os.path.getctime)
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read().split(", ")

            try:
                txt_hid = content[0]
                q2 = int(content[2])
                q5 = int(content[4])
                q10 = int(content[6])
                total_amt = (q2 * 2) + (q5 * 5) + (q10 * 10)

                state["vouchers"] = {"hid": txt_hid, "2": q2, "5": q5, "10": q10, "total": total_amt, "file": latest_file}

                result_area.controls.clear()
                result_area.controls.extend([
                    ft.Divider(),
                    ft.Text(f"Found Selection for: {txt_hid}", weight="bold"),
                    ft.Text(f"Vouchers: $2x{q2}, $5x{q5}, $10x{q10}"),
                    ft.Text(f"Total Amount: ${total_amt}", size=20, color="blue", weight="bold"),
                    ft.ElevatedButton("Confirm & Redeem", bgcolor="blue", color="white", on_click=process_redemption)
                ])
                page.update()
            except:
                show_msg("Error reading file content", True)

        def process_redemption(e):
            v = state["vouchers"]
            households = DataManager.load_households()
            if v["hid"] not in households:
                show_msg("Household not found in database", True)
                return

            h_rec = households[v["hid"]]
            new_balance_2 = int(h_rec.get("2", 0)) - v["2"]
            new_balance_5 = int(h_rec.get("5", 0)) - v["5"]
            new_balance_10 = int(h_rec.get("10", 0)) - v["10"]

            if new_balance_2 < 0 or new_balance_5 < 0 or new_balance_10 < 0:
                show_msg("Insufficient balance in database!", True)
                return

            try:
                response = requests.post(
                    f"{API_BASE_URL}/household/api/update/{v['hid']}",
                    json={
                        "2": new_balance_2,
                        "5": new_balance_5,
                        "10": new_balance_10
                    },
                    timeout=10
                )
                if response.status_code != 200:
                    show_msg("Failed to update household balances", True)
                    return
            except Exception as e:
                show_msg(f"Error updating balances: {str(e)}", True)
                return

            tx_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_tx = {
                "Transaction_ID": tx_id,
                "Household_ID": v["hid"],
                "Merchant_ID": state["current_id"],
                "Transaction_Date_Time": datetime.now().strftime("%Y-%m-%d-%H%M%S"),
                "Voucher_2": v["2"],
                "Voucher_5": v["5"],
                "Voucher_10": v["10"],
                "Amount_Redeemed": v["total"],
                "Payment_Status": "Completed"
            }

            DataManager.save_transaction(new_tx)
            show_msg(f"Successfully redeemed ${v['total']}!")

            os.remove(v["file"])
            result_area.controls.clear()
            target_h_id.value = ""
            page.update()

        page.add(
            ft.Container(
                content=ft.Column([
                    target_h_id,
                    ft.ElevatedButton("Scan Selection Folder", on_click=scan_txt_click),
                    result_area,
                    ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
                ], horizontal_alignment="center"),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ==========================================
    # ADMIN Dashboard - Reordered navigation
    # ==========================================
    def go_to_admin_dashboard():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Admin Dashboard"))

        households = DataManager.load_households()
        merchants = DataManager.load_merchants()

        total_users = len(households)
        total_merchants = len(merchants)

        total_transactions = 0
        total_amount = 0
        merchant_totals = {}

        if os.path.exists(TX_ROOT_DIR):
            for date_folder in os.listdir(TX_ROOT_DIR):
                folder_path = os.path.join(TX_ROOT_DIR, date_folder)
                if os.path.isdir(folder_path):
                    for tx_file in os.listdir(folder_path):
                        if tx_file.endswith('.json'):
                            file_path = os.path.join(folder_path, tx_file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    transactions = json.load(f)
                                    if isinstance(transactions, list):
                                        total_transactions += len(transactions)
                                        for tx in transactions:
                                            amount = tx.get("Amount_Redeemed", 0)
                                            total_amount += amount
                                            
                                            merchant_id = tx.get("Merchant_ID", "Unknown")
                                            if merchant_id not in merchant_totals:
                                                merchant_totals[merchant_id] = {"amount": 0, "count": 0}
                                            merchant_totals[merchant_id]["amount"] += amount
                                            merchant_totals[merchant_id]["count"] += 1
                            except:
                                pass

        def create_stat_card(title, value, color):
            return ft.Container(
                content=ft.Column([
                    ft.Text(title, size=14, weight="bold", color="black"),
                    ft.Text(str(value), size=28, weight="bold", color=color),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=20,
                border=ft.border.all(2, color),
                border_radius=10,
                width=280,
                height=120,
                margin=10,
                bgcolor="white"
            )

        total_vouchers_claimed_2025 = sum(1 for h in households.values() if h.get("2025 May", 0) == 1)
        total_vouchers_claimed_2026 = sum(1 for h in households.values() if h.get("2026 Jan", 0) == 1)

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("System Statistics", size=28, weight="bold"),
                    ft.Divider(height=20),
                    
                    # Navigation buttons - REORDERED
                    ft.Row([
                        ft.ElevatedButton("Reimbursement", width=130, on_click=lambda _: switch_view("admin_reimbursement")),
                        ft.ElevatedButton("Dashboard", width=130, bgcolor="blue", color="white"),
                        ft.ElevatedButton("Redemption", width=130, on_click=lambda _: switch_view("admin_redemption")),
                    ], alignment="center"),
                    
                    ft.Divider(height=20),
                    
                    ft.Row([
                        create_stat_card("Total Household Users", total_users, "blue"),
                        create_stat_card("Total Merchants", total_merchants, "green"),
                    ], alignment="center", wrap=True),
                    
                    ft.Row([
                        create_stat_card("Total Transactions", total_transactions, "purple"),
                        create_stat_card("Total Amount Redeemed", f"${total_amount}", "orange"),
                    ], alignment="center", wrap=True),
                    
                    ft.Divider(height=20),
                    
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Voucher Claims", size=18, weight="bold"),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Text("May 2025 Tranche:", size=14),
                                ft.Text(f"{total_vouchers_claimed_2025} users", size=14, weight="bold", color="blue")
                            ], alignment="spaceBetween"),
                            ft.Row([
                                ft.Text("Jan 2026 Tranche:", size=14),
                                ft.Text(f"{total_vouchers_claimed_2026} users", size=14, weight="bold", color="green")
                            ], alignment="spaceBetween"),
                        ]),
                        padding=20,
                        border=ft.border.all(1, "gray"),
                        border_radius=10,
                        width=300,
                        margin=10
                    ),
                    
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Total Amount Redeemed by Merchant", size=18, weight="bold"),
                            ft.Divider(height=10),
                        ] + [
                            ft.Row([
                                ft.Text(f"{merchant_id}:", size=14),
                                ft.Column([
                                    ft.Text(f"${data['amount']}", size=14, weight="bold", color="orange"),
                                    ft.Text(f"({data['count']} transactions)", size=10, color="gray")
                                ], spacing=0)
                            ], alignment="spaceBetween")
                            for merchant_id, data in sorted(merchant_totals.items(), key=lambda x: x[1]['amount'], reverse=True)
                        ] + ([ft.Text("No transactions yet", size=12, color="gray", text_align="center")] if not merchant_totals else [])),
                        padding=20,
                        border=ft.border.all(1, "gray"),
                        border_radius=10,
                        width=300,
                        margin=10
                    ),
                    
                    ft.Divider(height=20),
                    ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
                ], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ==========================================
    # ADMIN Redemption - Reordered navigation
    # ==========================================
    def go_to_admin_redemption():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Admin - Redemption History"))

        redemption_history = []
        if os.path.exists(TX_ROOT_DIR):
            for date_folder in os.listdir(TX_ROOT_DIR):
                folder_path = os.path.join(TX_ROOT_DIR, date_folder)
                if os.path.isdir(folder_path):
                    for tx_file in os.listdir(folder_path):
                        if tx_file.endswith('.json'):
                            file_path = os.path.join(folder_path, tx_file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    transactions = json.load(f)
                                    if isinstance(transactions, list):
                                        for tx in transactions:
                                            redemption_history.append({
                                                "date": date_folder,
                                                "file": tx_file,
                                                "transaction": tx
                                            })
                            except:
                                pass

        redemption_history.sort(key=lambda x: (x["date"], x["file"]), reverse=True)

        redemption_items = []
        for item in redemption_history[:50]:
            tx = item["transaction"]
            redemption_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Transaction ID: {tx.get('Transaction_ID', 'N/A')}", size=12, weight="bold"),
                            ft.Text(f"${tx.get('Amount_Redeemed', 0)}", size=14, weight="bold", color="green")
                        ], alignment="spaceBetween"),
                        ft.Divider(height=5),
                        ft.Row([
                            ft.Text(f"Household: {tx.get('Household_ID', 'N/A')}", size=11),
                            ft.Text(f"Merchant: {tx.get('Merchant_ID', 'N/A')}", size=11)
                        ], alignment="spaceBetween"),
                        ft.Text(f"Date: {tx.get('Transaction_Date_Time', 'N/A')}", size=10, color="gray"),
                        ft.Text(f"Vouchers: $2×{tx.get('Voucher_2', 0)}, $5×{tx.get('Voucher_5', 0)}, $10×{tx.get('Voucher_10', 0)}", size=10, color="gray"),
                    ]),
                    padding=10,
                    border=ft.border.all(1, "#CCCCCC"),
                    border_radius=8,
                    margin=5
                )
            )

        if not redemption_items:
            redemption_items.append(
                ft.Text("No redemption records found", size=14, color="gray", text_align="center")
            )

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("Redemption History", size=24, weight="bold"),
                    ft.Text(f"Showing {len(redemption_items)} recent transactions", size=12, color="gray"),
                    ft.Divider(height=20),
                    
                    # Navigation - REORDERED
                    ft.Row([
                        ft.ElevatedButton("Reimbursement", width=130, on_click=lambda _: switch_view("admin_reimbursement")),
                        ft.ElevatedButton("Dashboard", width=130, on_click=lambda _: switch_view("admin_dashboard")),
                        ft.ElevatedButton("Redemption", width=130, bgcolor="blue", color="white"),
                    ], alignment="center"),
                    
                    ft.Divider(height=20),
                    
                    ft.Column(redemption_items, scroll="auto", height=400),
                    
                    ft.Divider(height=20),
                    ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
                ], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    # ==========================================
    # ADMIN Reimbursement - FIXED with proper error handling
    # ==========================================
    def go_to_admin_reimbursement():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Admin - Reimbursement Processing"))

        date_input = ft.TextField(
            label="Reimburse Date (YYYYMMDD)",
            width=300,
            hint_text="e.g., 20260129",
            value="20260129"  # Default value for testing
        )
        
        start_hour_input = ft.TextField(
            label="Start Hour (0-23)",
            width=140,
            hint_text="e.g., 0",
            value="0"
        )
        
        end_hour_input = ft.TextField(
            label="End Hour (0-24)",
            width=140,
            hint_text="e.g., 24 = end of day",
            value="24"
        )

        result_area = ft.Column()
        processing_indicator = ft.ProgressRing(visible=False)

        def process_reimbursement_click(e):
            reimburse_date = date_input.value.strip()
            start_hour_str = start_hour_input.value.strip()
            end_hour_str = end_hour_input.value.strip()

            # Validation
            if not reimburse_date or not start_hour_str or not end_hour_str:
                show_msg("All fields are required", True)
                return

            if len(reimburse_date) != 8 or not reimburse_date.isdigit():
                show_msg("Invalid date format. Use YYYYMMDD", True)
                return

            try:
                start_hour = int(start_hour_str)
                end_hour = int(end_hour_str)
            except ValueError:
                show_msg("Hours must be integers", True)
                return

            if not (0 <= start_hour <= 23 and 0 <= end_hour <= 24):
                show_msg("Start hour must be 0-23, end hour 0-24", True)
                return

            if start_hour >= end_hour:
                show_msg("Start hour must be less than end hour", True)
                return

            # Show processing indicator
            processing_indicator.visible = True
            result_area.controls.clear()
            result_area.controls.append(ft.Text("Processing... Please wait", size=14, color="blue"))
            page.update()

            # Call API - removed session check since Flet doesn't have Flask session
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/process_redemption",
                    json={
                        "reimburse_date": reimburse_date,
                        "start_hour": start_hour,
                        "end_hour": end_hour
                    },
                    timeout=60,  # Increased timeout
                    # Add headers to simulate authenticated session
                    cookies={"session": "admin_authenticated"}
                )

                processing_indicator.visible = False

                if response.status_code == 200:
                    data = response.json()
                    result_area.controls.clear()
                    result_area.controls.extend([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("✅ SUCCESS", size=20, weight="bold", color="green"),
                                ft.Divider(height=10),
                                ft.Text(data.get("message", "Processing complete"), size=14),
                                ft.Text(f"Output Folder: {data.get('output_folder', 'N/A')}", size=12, color="gray"),
                                ft.Divider(height=10),
                                ft.Text("Generated Files:", size=14, weight="bold"),
                            ] + [
                                ft.Text(f"• {f}", size=12)
                                for f in data.get("files_generated", [])
                            ] + ([ft.Text("No files generated (no transactions found)", size=12, color="gray")] if not data.get("files_generated") else [])),
                            padding=20,
                            border=ft.border.all(2, "green"),
                            border_radius=10,
                            bgcolor="#f0fff0"
                        )
                    ])
                    page.update()
                elif response.status_code == 401:
                    show_msg("Authentication required. Please login again.", True)
                elif response.status_code == 404:
                    data = response.json()
                    error_msg = data.get("message", "Required files not found")
                    result_area.controls.clear()
                    result_area.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("❌ ERROR", size=20, weight="bold", color="red"),
                                ft.Divider(height=10),
                                ft.Text(error_msg, size=14),
                                ft.Text("Please check:", size=12, weight="bold"),
                                ft.Text("• BankCode.csv exists", size=11),
                                ft.Text("• merchant_data.json exists", size=11),
                                ft.Text(f"• transaction/Redeem{reimburse_date}/ folder exists", size=11),
                                ft.Text(f"• Transaction files: Redeem{reimburse_date}{start_hour:02d}.json to Redeem{reimburse_date}{end_hour:02d}.json", size=11),
                            ]),
                            padding=20,
                            border=ft.border.all(2, "red"),
                            border_radius=10,
                            bgcolor="#fff5f5"
                        )
                    )
                    page.update()
                else:
                    data = response.json()
                    show_msg(data.get("message", "Processing failed"), True)
                    result_area.controls.clear()
                    result_area.controls.append(
                        ft.Text(f"Error: {data.get('message', 'Unknown error')}", size=14, color="red")
                    )
                    page.update()
            except requests.exceptions.Timeout:
                processing_indicator.visible = False
                show_msg("Request timeout. Processing may take longer.", True)
                result_area.controls.clear()
                result_area.controls.append(
                    ft.Text("Request timed out after 60 seconds", size=14, color="orange")
                )
                page.update()
            except requests.exceptions.ConnectionError:
                processing_indicator.visible = False
                show_msg("Cannot connect to API server. Is it running?", True)
                result_area.controls.clear()
                result_area.controls.append(
                    ft.Text("Connection Error: Make sure Main_APP.py is running on port 8000", size=14, color="red")
                )
                page.update()
            except Exception as e:
                processing_indicator.visible = False
                show_msg(f"Error: {str(e)}", True)
                result_area.controls.clear()
                result_area.controls.append(
                    ft.Text(f"Unexpected error: {str(e)}", size=14, color="red")
                )
                page.update()

        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("Reimbursement Processing", size=24, weight="bold"),
                    ft.Text("Process merchant reimbursement for a specific date and time range", size=12, color="gray"),
                    ft.Divider(height=20),
                    
                    # Navigation - REORDERED
                    ft.Row([
                        ft.ElevatedButton("Reimbursement", width=130, bgcolor="blue", color="white"),
                        ft.ElevatedButton("Dashboard", width=130, on_click=lambda _: switch_view("admin_dashboard")),
                        ft.ElevatedButton("Redemption", width=130, on_click=lambda _: switch_view("admin_redemption")),
                    ], alignment="center"),
                    
                    ft.Divider(height=20),
                    
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Enter Reimbursement Parameters", size=16, weight="bold"),
                            ft.Divider(height=10),
                            date_input,
                            ft.Row([
                                start_hour_input,
                                end_hour_input
                            ], alignment="center"),
                            ft.Divider(height=10),
                            processing_indicator,
                            ft.ElevatedButton(
                                "Process Reimbursement",
                                width=280,
                                bgcolor="orange",
                                color="white",
                                on_click=process_reimbursement_click
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        border=ft.border.all(1, "gray"),
                        border_radius=10,
                        width=320,
                        margin=10
                    ),
                    
                    ft.Divider(height=20),
                    result_area,
                    
                    ft.Divider(height=20),
                    ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
                ], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=50
            )
        )

    go_to_role_select()

if __name__ == "__main__":
    ft.app(target=main)
