# CDC Voucher System / CDC 消費券管理系統

A full-stack government consumption voucher management platform — covering household registration, voucher claiming, mobile-based redemption, and automated bank reimbursement.

全端政府消費券管理平台，涵蓋住戶註冊、領券、移動端核銷到銀行自動報銷的完整業務流程。

---

## What Is This? / 這是什麼？

The CDC Voucher System simulates a real-world government voucher program (similar to Hong Kong's Consumption Voucher Scheme). Citizens can register, claim vouchers, and spend them at participating merchants. Merchants are then reimbursed by the government through an automated batch process.

本系統模擬真實政府消費券計劃（參考香港消費券計劃）。市民可在系統中註冊、領取消費券，並在參與商戶消費核銷；商戶的消費券收入最終由管理員觸發自動批量報銷至對應銀行。

---

## User Roles / 使用者角色

| Role / 角色 | Description / 說明 |
|-------------|-------------------|
| **Household / 住戶** | Register an account, claim vouchers, select voucher denominations and generate a redemption file at merchants |
| **Merchant / 商戶** | Register business with bank account, scan household voucher files and confirm redemption |
| **Admin / 管理員** | Log in to a protected panel, trigger batch reimbursement to banks for a selected date/time range |

---

## Features / 功能說明

### Household / 住戶端
- **Registration / 註冊**：Fill in household information to register; system assigns a unique Household ID
- **Voucher Claiming / 領取消費券**：Eligible households claim vouchers from available tranches (e.g. 2025 May, 2026 Jan); each tranche grants a set of $2 / $5 / $10 vouchers
- **Mobile Redemption / 移動端核銷**：Log in to the mobile app, view available voucher balance, select denominations and quantities, generate a voucher selection file for the merchant to scan

### Merchant / 商戶端
- **Registration / 註冊**：Register business name and bank/branch details; bank codes are validated against an official bank directory
- **Voucher Scanning / 核銷掃描**：Enter the household ID in the mobile app to retrieve their voucher selection, review the total amount, and confirm redemption; the system deducts the household's balance and records the transaction

### Admin / 管理端
- **Secure Login / 密碼登入**：Access the admin panel via password authentication
- **Batch Reimbursement / 批量報銷**：Select a date and hour range; the system aggregates all transactions within that window, groups them by merchant and bank, and generates one CSV reimbursement file per bank
- **Duplicate Prevention / 防重複清算**：The system records every processed time window and rejects re-runs to prevent double payment

---

## How It Works / 系統流程

```
住戶註冊 → 領取消費券 → 手機選券生成 TXT
                                  ↓
                       商戶掃描 TXT → 確認核銷 → 寫入交易記錄
                                                      ↓
                                       管理員選擇日期時間範圍觸發報銷
                                                      ↓
                                  AVL Tree 查詢商戶 → 貪心聚合 → 生成銀行 CSV
```

```
Household registers → Claims vouchers → Selects vouchers on mobile app → TXT file generated
                                                        ↓
                                  Merchant scans TXT → Confirms → Transaction recorded
                                                                          ↓
                                              Admin triggers reimbursement for date/hour range
                                                                          ↓
                                          AVL Tree merchant lookup → Greedy aggregation → Bank CSVs
```

---

## Architecture / 系統架構

```
CDC Voucher System
│
├── Main_APP.py              # Flask entry point; Blueprint registration & admin routes
│
├── House_Registration.py    # Household registration, voucher allocation
├── Merchant_api.py          # Merchant registration & lookup
├── Bank_api.py              # Bank directory, branch validation, dropdown APIs
├── Voucher_claim_api.py     # Voucher claiming logic
│
├── mobile_app.py            # Flet mobile app (household voucher selection + merchant scanning)
│
├── algorithm_avl_greedy.py  # AVL Tree + Greedy aggregation for reimbursement processing
├── redemption_tracker.py    # Duplicate reimbursement prevention
├── LoadData.py              # Data I/O: CSV, JSON, transaction file management
│
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS / JS assets
├── transaction/             # Transaction records organized by date/hour
│   └── redeemYYYYMMDD/
│       └── RedeemYYYYMMDDHH.json
├── redeem_output/           # Generated bank reimbursement CSVs
├── voucher_selections/      # Temporary voucher TXT files
├── household_data.json      # Household registry & live voucher balances
├── merchant_data.json       # Merchant registry
└── BankCode.csv             # Official bank/branch/SWIFT reference data
```

---

## Tech Stack / 技術棧

| Layer / 層級 | Technology / 技術 |
|--------------|------------------|
| Web Backend / 後端 | Python 3, Flask, Blueprint |
| Mobile App / 移動端 | Flet (cross-platform Python GUI) |
| Data Structure / 資料結構 | Custom AVL Tree (hand-implemented) |
| Algorithm / 演算法 | Greedy single-pass aggregation |
| Storage / 儲存 | JSON files + CSV |
| Frontend / 前端 | Jinja2 templates, HTML/CSS/JS |

---

## Limitations & Reflections / 局限性與反思

### 與真實系統的差距 / Gap from a Production System

| 方面 | 本項目實現 | 真實系統應有的做法 |
|------|-----------|-----------------|
| **數據持久化** | JSON 文件存儲，無事務保障 | 關係型數據庫（如 PostgreSQL）+ ACID 事務，防止並發寫入時數據損壞 |
| **身份認證** | 住戶/商戶僅憑 ID 登錄，無密碼或 OTP | 雙因素認證（2FA）、JWT / OAuth2，配合 HTTPS 傳輸 |
| **安全性** | Admin 密碼硬編碼在源碼中，Secret Key 為明文 | 環境變量或密鑰管理服務（如 AWS Secrets Manager）存儲憑證 |
| **並發處理** | 單進程 Flask dev server，文件寫入無鎖 | 多進程部署（Gunicorn + Nginx）、數據庫行級鎖或樂觀鎖 |
| **憑證防偽** | 住戶憑證為本地 TXT 文件，可被複製偽造 | 數字簽名或加密 QR Code，服務端一次性驗證 |
| **可擴展性** | 商戶數據全量加載進內存 | 分頁查詢 + 緩存（Redis），支持百萬級商戶 |
| **錯誤恢復** | 報銷中途失敗無回滾機制 | 數據庫事務回滾 + 冪等性設計，保證報銷操作可重試 |

### 項目反思 / Reflections

**做得好的地方 / What went well：**
- 從零手寫 AVL Tree，深入理解了自平衡樹的旋轉邏輯與複雜度保證，而不是直接調用現成庫。
- Blueprint 模塊化設計使各業務域職責清晰，後期新增功能時改動範圍可控。
- 貪心聚合算法在單次遍歷內完成商戶→銀行的分組匯總，避免了嵌套循環的性能問題。

**如果重來會改變的地方 / What we would do differently：**
- **引入數據庫**：JSON 文件在多用戶並發核銷時存在競態條件，SQLite 甚至就足以解決這個問題。
- **將移動端與後端解耦**：目前 Flet app 直接讀寫本地 JSON 文件，繞過了 Flask API 層，導致數據一致性難以保證；理想方案是 Flet 通過 REST API 與後端通信。
- **更完善的測試**：項目缺乏單元測試和集成測試，算法的邊界情況（空交易、跨日時間段）依賴手動驗證，容易遺漏。

---

## Getting Started / 快速開始

```bash
# Install dependencies / 安裝依賴
pip install flask flet

# Run the server / 啟動服務器
python Main_APP.py
# Server starts at / 服務器啟動於 http://localhost:8000

# The mobile app launches from the web UI (/consume)
# 移動端 App 可從網頁 /consume 路由啟動，或直接運行：
python mobile_app.py
```
