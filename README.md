# CDC Voucher System

A full-stack government consumption voucher management platform built with Python, Flask, and Flet.

---

## Features

The system supports the complete lifecycle of a government voucher program:

| Module | Description |
|--------|-------------|
| Household Registration | Citizens register, receive voucher allocations across tranches (e.g. 2025 May, 2026 Jan) |
| Voucher Claiming | Registered households claim their voucher entitlements via web interface |
| Mobile Redemption App | Households generate a voucher selection file; merchants scan and confirm redemption on-device |
| Merchant Registration | Merchants register with bank/branch details; bank codes are validated against a master BankCode.csv |
| Admin Reimbursement | Password-protected admin panel triggers batch reimbursement processing for a specified date/hour range |
| Duplicate Prevention | Redemption history tracker prevents re-processing the same time window twice |

---

## Architecture

```
CDC Voucher System
│
├── Main_APP.py              # Flask application entry point; Blueprint registration
│
├── House_Registration.py    # Blueprint: /household — registration, voucher allocation
├── Merchant_api.py          # Blueprint: /merchant  — merchant registration & lookup
├── Bank_api.py              # Blueprint: /api/banks — bank directory, branch validation
├── Voucher_claim_api.py     # Blueprint: /api/voucher/claim — voucher claiming logic
│
├── mobile_app.py            # Flet cross-platform mobile app (launched as subprocess)
│   ├── Household view       #   Select voucher denominations, export selection as TXT
│   └── Merchant view        #   Scan household TXT, confirm redemption, write transaction JSON
│
├── algorithm_avl_greedy.py  # Core algorithm: AVL Tree + Greedy aggregation
├── redemption_tracker.py    # Tracks processed time windows; blocks duplicate runs
├── LoadData.py              # Data I/O helpers: CSV, JSON, transaction file management
│
├── templates/               # Jinja2 HTML templates (web frontend)
├── static/                  # CSS / JS assets
├── transaction/             # Runtime transaction store (organized by date/hour)
│   └── redeemYYYYMMDD/
│       └── RedeemYYYYMMDDHH.json
├── redeem_output/           # Generated reimbursement CSVs (one per bank per run)
├── voucher_selections/      # Temporary voucher TXT files (deleted after merchant scan)
├── household_data.json      # Household registry & live voucher balances
├── merchant_data.json       # Merchant registry
└── BankCode.csv             # Master bank/branch/SWIFT reference data
```

### Key Design Decisions

- **Flask Blueprint pattern** — each domain (household, merchant, bank, voucher) is an independent module, keeping concerns separated and the codebase extensible.
- **AVL Tree for merchant lookup** — merchants are indexed into a self-balancing BST at startup, giving O(log n) search during reimbursement processing instead of O(n) list scans.
- **Greedy aggregation** — transactions are grouped by merchant, then by bank SWIFT code, summing amounts in a single pass. This produces one CSV per bank with one row per merchant, ready for direct bank transfer.
- **File-based transaction store** — transactions are appended to hourly JSON files (`RedeemYYYYMMDDHH.json`). The admin selects a date + hour range at reimbursement time, allowing flexible batch windows without a database.
- **Flet mobile app as subprocess** — the web server spawns the Flet GUI as a separate process (`subprocess.Popen`), allowing a native-feel mobile interface to coexist with the Flask backend without tight coupling.

---

## Reimbursement Flow

```
Admin selects date + hour range
        ↓
Load transactions from JSON files in range
        ↓
Build merchant AVL Tree (O(n log n))
        ↓
Greedy aggregate: merchant → bank SWIFT group
        ↓
Write one CSV per bank  →  redeem_output/YYYYMMDD/
        ↓
Write Reimburse_ID back into each transaction JSON
        ↓
Log run to redemption history (prevents re-run)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Backend | Python 3, Flask, Blueprint |
| Mobile App | Flet (cross-platform Python GUI) |
| Data Structure | Custom AVL Tree (from scratch) |
| Algorithm | Greedy single-pass aggregation |
| Storage | JSON files + CSV |
| Frontend | Jinja2 templates, HTML/CSS/JS |

---

## Limitations & Reflections

### 与真实系统的差距

| 方面 | 本项目实现 | 真实系统应有的做法 |
|------|-----------|-----------------|
| **数据持久化** | JSON 文件存储，无事务保障 | 关系型数据库（如 PostgreSQL）+ ACID 事务，防止并发写入时数据损坏 |
| **身份认证** | 住户/商家仅凭 ID 登录，无密码或 OTP | 双因素认证（2FA）、JWT / OAuth2，配合 HTTPS 传输 |
| **安全性** | Admin 密码硬编码在源码中，Secret Key 为明文 | 环境变量或密钥管理服务（如 AWS Secrets Manager）存储凭证 |
| **并发处理** | 单进程 Flask dev server，文件写入无锁 | 多进程部署（Gunicorn + Nginx）、数据库行级锁或乐观锁 |
| **凭证防伪** | 住户凭证为本地 TXT 文件，可被复制伪造 | 数字签名或加密 QR Code，服务端一次性验证 |
| **可扩展性** | 商家数据全量加载进内存 | 分页查询 + 缓存（Redis），支持百万级商家 |
| **错误恢复** | 报销中途失败无回滚机制 | 数据库事务回滚 + 幂等性设计，保证报销操作可重试 |

### 项目反思

**做得好的地方：**
- 从零手写 AVL Tree，深入理解了自平衡树的旋转逻辑与复杂度保证，而不是直接调用现成库。
- Blueprint 模块化设计使各业务域职责清晰，后期新增功能时改动范围可控。
- 贪心聚合算法在单次遍历内完成商家→银行的分组汇总，避免了嵌套循环的性能问题。

**如果重来会改变的地方：**
- **引入数据库**：JSON 文件在多用户并发核销时存在竞态条件，SQLite 甚至就足以解决这个问题。
- **将移动端与后端解耦**：目前 Flet app 直接读写本地 JSON 文件，绕过了 Flask API 层，导致数据一致性难以保证；理想方案是 Flet 通过 REST API 与后端通信。
- **更完善的测试**：项目缺乏单元测试和集成测试，算法的边界情况（空交易、跨日时间段）依赖手动验证，容易遗漏。

---

## Getting Started

```bash
# Install dependencies
pip install flask flet

# Run the server
python Main_APP.py
# Server starts at http://localhost:8000

# The mobile redemption app launches automatically
# from the web UI (/consume route), or run directly:
python mobile_app.py
```
