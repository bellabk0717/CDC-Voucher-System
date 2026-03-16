import flet as ft
import json
import os
import glob
from typing import Dict, Any, Optional
from datetime import datetime

# ==========================================
# 路径与配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOUSEHOLD_DATA_FILE = os.path.join(BASE_DIR, "household_data.json")
MERCHANT_DATA_FILE = os.path.join(BASE_DIR, "merchant_data.json")
TRANSACTION_FILE = os.path.join(BASE_DIR, "Transaction.json")
1.
TX_ROOT_DIR = os.path.join(BASE_DIR, "transaction") # 交易记录根目录
if not os.path.exists(TX_ROOT_DIR):
    os.makedirs(TX_ROOT_DIR)

# 新增：定义存放 TXT 的专用文件夹路径
VOUCHER_DIR = os.path.join(BASE_DIR, "voucher_selections")
if not os.path.exists(VOUCHER_DIR):
    os.makedirs(VOUCHER_DIR)

TRANCHE_CONFIG = {
    "2025 May": {"2": 50, "5": 20, "10": 30},
    "2026 Jan": {"2": 30, "5": 12, "10": 15},
}

# ==========================================
# 数据管理类 (OOP)
# ==========================================
class DataManager:
    @staticmethod
    def load_households() -> Dict:
        if not os.path.exists(HOUSEHOLD_DATA_FILE): return {}
        with open(HOUSEHOLD_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_households(data: Dict):
        with open(HOUSEHOLD_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_merchants() -> Dict:
        if not os.path.exists(MERCHANT_DATA_FILE): return {}
        with open(MERCHANT_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_transaction(tx: Dict):
        """
        保存规则：
        文件夹: transaction/redeemYYYYMMDD/
        文件名: RedeemYYYYMMDDHH.json
        """
        now = datetime.now()
        date_folder = f"redeem{now.strftime('%Y%m%d')}" # 例如: redeem20260101
        hour_file = f"Redeem{now.strftime('%Y%m%d%H')}.json" # 例如: Redeem2026010108.json
        
        # 1. 创建当天的日期文件夹路径
        target_dir = os.path.join(TX_ROOT_DIR, date_folder)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        # 2. 完整的文件路径
        file_path = os.path.join(target_dir, hour_file)
        
        # 3. 读取当前小时已有的交易数据 (如果有)
        data = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        # 4. 追加本次交易并保存
        data.append(tx)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

# ==========================================
# 业务逻辑与界面
# ==========================================
def main(page: ft.Page):
    page.title = "CDC Redemption App"
    page.window.width = 400
    page.window.height = 750
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    state = {
        "current_id": "",
        "role": "",
        "vouchers": {}
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
        page.update()

    # ------------------------------------------
    # 角色选择
    # ------------------------------------------
    def go_to_role_select():
        page.add(
            ft.Column(
                [
                    ft.Text("CDC SYSTEM", size=32, weight="bold"),
                    ft.Text("Please select your role"),
                    ft.ElevatedButton("Household User", width=250, on_click=lambda _: switch_view("household_login")),
                    ft.ElevatedButton("Merchant", width=250, on_click=lambda _: switch_view("merchant_login")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    # ------------------------------------------
    # 登录
    # ------------------------------------------
    def go_to_login(role):
        state["role"] = role
        label = "Household ID" if role == "household" else "Merchant ID"
        id_input = ft.TextField(label=label, width=300)

        def login_click(e):
            input_val = id_input.value.strip()
            if role == "household":
                households = DataManager.load_households()
                if input_val in households:
                    state["current_id"] = input_val
                    go_to_household_dashboard()
                else: show_msg("Household ID not found", True)
            else:
                merchants = DataManager.load_merchants()
                if input_val in merchants:
                    state["current_id"] = input_val
                    go_to_merchant_dashboard()
                else: show_msg("Merchant ID not found", True)

        page.add(
            ft.Column(
                [
                    ft.Text("LOGIN", size=24, weight="bold"),
                    id_input,
                    ft.ElevatedButton("Sign In", on_click=login_click),
                    ft.TextButton("Back", on_click=lambda _: switch_view("role_select"))
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

    # ==========================================
    # HOUSEHOLD 模块
    # ==========================================
    qty_inputs: Dict[str, ft.TextField] = {}

    def go_to_household_dashboard():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text(f"User: {state['current_id']}"))
        
        h_all = DataManager.load_households()
        h_data = h_all[state["current_id"]]
        
        existed = {"2": 0, "5": 0, "10": 0}
        if h_data.get("2025 May") == 1:
            for k in existed: existed[k] += TRANCHE_CONFIG["2025 May"][k]
        if h_data.get("2026 Jan") == 1:
            for k in existed: existed[k] += TRANCHE_CONFIG["2026 Jan"][k]
        
        balance = {"2": int(h_data.get("2", 0)), "5": int(h_data.get("5", 0)), "10": int(h_data.get("10", 0))}
        used = {k: existed[k] - balance[k] for k in existed}

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
            
            # 路径改动：保存到 VOUCHER_DIR
            full_path = os.path.join(VOUCHER_DIR, fname)
            
            content = f"{state['current_id']}, $2, {q2}, $5, {q5}, $10, {q10}"
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            page.clean()
            page.add(ft.Column([
                ft.Text("SUCCESS", size=24, weight="bold", color="green"),
                ft.Text(f"Saved to: voucher_selections/"),
                ft.Text(f"Filename: {fname}"),
                ft.Text(f"Content: {content}"),
                ft.ElevatedButton("Done", on_click=lambda _: switch_view("role_select"))
            ], horizontal_alignment="center"))
            page.update()

        page.add(
            ft.Column([
                create_voucher_row("2"),
                create_voucher_row("5"),
                create_voucher_row("10"),
                ft.ElevatedButton("Generate Voucher TXT", width=300, on_click=generate_txt_click),
                ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
            ], scroll="auto")
        )

    # ==========================================
    # MERCHANT 模块
    # ==========================================
    def go_to_merchant_dashboard():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text(f"Merchant: {state['current_id']}"))
        
        target_h_id = ft.TextField(label="Enter Household ID to scan", width=300)
        result_area = ft.Column()

        def scan_txt_click(e):
            hid = target_h_id.value.strip()
            # 路径改动：在 VOUCHER_DIR 文件夹内搜索
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
            h_rec["2"] = int(h_rec.get("2", 0)) - v["2"]
            h_rec["5"] = int(h_rec.get("5", 0)) - v["5"]
            h_rec["10"] = int(h_rec.get("10", 0)) - v["10"]
            
            if h_rec["2"] < 0 or h_rec["5"] < 0 or h_rec["10"] < 0:
                show_msg("Insufficient balance in database!", True)
                return

            DataManager.save_households(households)

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
            
            # 可选：兑换成功后可以删除该 TXT 文件或重命名，防止重复扫描
            os.remove(v["file"]) 
            
            result_area.controls.clear()
            target_h_id.value = ""
            page.update()

        page.add(
            ft.Column([
                target_h_id,
                ft.ElevatedButton("Scan Selection Folder", on_click=scan_txt_click),
                result_area,
                ft.TextButton("Logout", on_click=lambda _: switch_view("role_select"))
            ], horizontal_alignment="center")
        )

    go_to_role_select()

if __name__ == "__main__":
    ft.app(target=main)