# CDC Voucher System / CDC 消费券管理系统

A full-stack government consumption voucher management platform — covering household registration, voucher claiming, mobile-based redemption, and automated bank reimbursement.

全栈政府消费券管理平台，涵盖住户注册、领券、移动端核销到银行自动报销的完整业务流程。

---

## What Is This? / 这是什么？

The CDC Voucher System simulates a real-world government voucher program (similar to Hong Kong's Consumption Voucher Scheme). Citizens can register, claim vouchers, and spend them at participating merchants. Merchants are then reimbursed by the government through an automated batch process.

本系统模拟真实政府消费券计划（参考香港消费券计划）。市民可在系统中注册、领取消费券，并在参与商户消费核销；商户的消费券收入最终由管理员触发自动批量报销至对应银行。

---

## User Roles / 使用者角色

| Role / 角色 | Description / 说明 |
|-------------|-------------------|
| **Household / 住户** | Register an account, claim vouchers, select voucher denominations and generate a redemption file at merchants / 注册账户、领取消费券、在商户处选择面值并生成核销文件 |
| **Merchant / 商户** | Register business with bank account, scan household voucher files and confirm redemption / 注册商户与银行信息、扫描住户核销文件并确认收款 |
| **Admin / 管理员** | Log in to a protected panel, trigger batch reimbursement to banks for a selected date/time range / 登录管理后台、按日期时间段触发批量银行报销 |

---

## Features / 功能说明

### Household / 住户端
- **Registration / 注册**：Fill in household information to register; system assigns a unique Household ID / 填写住户信息完成注册，系统自动分配唯一住户 ID
- **Voucher Claiming / 领取消费券**：Eligible households claim vouchers from available tranches (e.g. 2025 May, 2026 Jan); each tranche grants a set of $2 / $5 / $10 vouchers / 符合资格的住户可领取各期消费券（如 2025 May、2026 Jan），每期包含 $2 / $5 / $10 面值的券
- **Mobile Redemption / 移动端核销**：Log in to the mobile app, view available voucher balance, select denominations and quantities, generate a voucher selection file for the merchant to scan / 登录移动端 App，查看余额，选择面值与数量，生成核销文件供商户扫描

### Merchant / 商户端
- **Registration / 注册**：Register business name and bank/branch details; bank codes are validated against an official bank directory / 注册商户名称与银行/支行信息，银行代码经官方名录实时校验
- **Voucher Scanning / 核销扫描**：Enter the household ID in the mobile app to retrieve their voucher selection, review the total amount, and confirm redemption; the system deducts the household's balance and records the transaction / 在移动端输入住户 ID 读取其选券记录，确认金额后完成核销，系统自动扣减余额并写入交易记录

### Admin / 管理端
- **Secure Login / 密码登录**：Access the admin panel via password authentication / 通过密码验证进入管理后台
- **Batch Reimbursement / 批量报销**：Select a date and hour range; the system aggregates all transactions within that window, groups them by merchant and bank, and generates one CSV reimbursement file per bank / 选择日期与时间段，系统聚合该窗口内所有交易，按商户和银行分组，为每家银行生成一份 CSV 报销文件
- **Duplicate Prevention / 防重复清算**：The system records every processed time window and rejects re-runs to prevent double payment / 系统记录每次已处理的时间窗口，拒绝重复运行，防止商户被重复打款

---

## How It Works / 系统流程

```
Household registers → Claims vouchers → Selects vouchers on mobile app → TXT file generated
                                                        ↓
                                  Merchant scans TXT → Confirms → Transaction recorded
                                                                          ↓
                                              Admin triggers reimbursement for date/hour range
                                                                          ↓
                                          AVL Tree merchant lookup → Greedy aggregation → Bank CSVs
```

```
住户注册 → 领取消费券 → 手机选券生成 TXT
                                  ↓
                       商户扫描 TXT → 确认核销 → 写入交易记录
                                                      ↓
                                       管理员选择日期时间范围触发报销
                                                      ↓
                                  AVL Tree 查询商户 → 贪心聚合 → 生成银行 CSV
```

---

## Architecture / 系统架构

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

## Tech Stack / 技术栈

| Layer / 层级 | Technology / 技术 |
|--------------|------------------|
| Web Backend / 后端 | Python 3, Flask, Blueprint |
| Mobile App / 移动端 | Flet (cross-platform Python GUI) |
| Data Structure / 数据结构 | Custom AVL Tree (hand-implemented) |
| Algorithm / 算法 | Greedy single-pass aggregation |
| Storage / 存储 | JSON files + CSV |
| Frontend / 前端 | Jinja2 templates, HTML/CSS/JS |

---

## Limitations & Reflections / 局限性与反思

### Gap from a Production System / 与真实系统的差距

| Aspect / 方面 | This Project / 本项目实现 | Production Approach / 真实系统应有的做法 |
|---------------|--------------------------|----------------------------------------|
| **Data Persistence / 数据持久化** | JSON file storage, no transaction guarantee / JSON 文件存储，无事务保障 | Relational DB (e.g. PostgreSQL) + ACID transactions / 关系型数据库 + ACID 事务，防止并发写入时数据损坏 |
| **Authentication / 身份认证** | Login by ID only, no password or OTP / 仅凭 ID 登录，无密码或 OTP | 2FA, JWT / OAuth2 over HTTPS / 双因素认证、JWT / OAuth2，配合 HTTPS 传输 |
| **Security / 安全性** | Admin password hardcoded in source, secret key in plaintext / Admin 密码硬编码，Secret Key 为明文 | Secrets stored in env vars or a key management service / 环境变量或密钥管理服务（如 AWS Secrets Manager）存储凭证 |
| **Concurrency / 并发处理** | Single-process Flask dev server, no file write locks / 单进程，文件写入无锁 | Multi-process deployment (Gunicorn + Nginx) + DB-level locking / 多进程部署 + 数据库行级锁或乐观锁 |
| **Voucher Integrity / 凭证防伪** | TXT files can be copied and reused / 住户凭证为本地 TXT，可被复制伪造 | Signed / encrypted QR codes with server-side single-use validation / 数字签名或加密 QR Code，服务端一次性验证 |
| **Scalability / 可扩展性** | All merchant data loaded into memory / 商户数据全量加载进内存 | Paginated queries + cache (Redis) for millions of merchants / 分页查询 + 缓存（Redis），支持百万级商户 |
| **Error Recovery / 错误恢复** | No rollback if reimbursement fails midway / 报销中途失败无回滚 | DB transaction rollback + idempotent design / 数据库事务回滚 + 幂等性设计，保证报销操作可重试 |

### Reflections / 项目反思

**What went well / 做得好的地方：**
- Implemented AVL Tree from scratch, gaining a deep understanding of rotation logic and complexity guarantees rather than relying on built-in libraries. / 从零手写 AVL Tree，深入理解了自平衡树的旋转逻辑与复杂度保证，而不是直接调用现成库。
- Blueprint-based modular design keeps each business domain isolated, making future extensions straightforward. / Blueprint 模块化设计使各业务域职责清晰，后期新增功能时改动范围可控。
- Greedy aggregation completes merchant-to-bank grouping in a single pass, avoiding nested-loop performance issues. / 贪心聚合算法在单次遍历内完成商户→银行的分组汇总，避免了嵌套循环的性能问题。

**What we would do differently / 如果重来会改变的地方：**
- **Introduce a database / 引入数据库**：JSON files have race conditions under concurrent redemptions; even SQLite would eliminate this. / JSON 文件在多用户并发核销时存在竞态条件，SQLite 甚至就足以解决这个问题。
- **Decouple mobile app from backend / 将移动端与后端解耦**：The Flet app currently reads/writes JSON files directly, bypassing the Flask API layer and making data consistency hard to guarantee; ideally it should communicate via REST API. / 目前 Flet app 直接读写本地 JSON 文件，绕过了 Flask API 层，导致数据一致性难以保证；理想方案是 Flet 通过 REST API 与后端通信。
- **Add automated tests / 更完善的测试**：The project lacks unit and integration tests; edge cases in the algorithm (empty transactions, cross-day time ranges) rely on manual verification. / 项目缺乏单元测试和集成测试，算法的边界情况（空交易、跨日时间段）依赖手动验证，容易遗漏。

---

## Getting Started / 快速开始

```bash
# Install dependencies / 安装依赖
pip install flask flet

# Run the server / 启动服务器
python Main_APP.py
# Server starts at / 服务器启动于 http://localhost:8000

# The mobile app launches from the web UI (/consume)
# 移动端 App 可从网页 /consume 路由启动，或直接运行：
python mobile_app.py
```
