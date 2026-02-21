# 🎫 Discord 開單機器人 | Ticket Bot

一個功能完整的 Discord 開單（Ticket）機器人，包含 **商品目錄開單系統**、**客服工單系統**、**VIP 專屬工單**、**員工領單機制**、**代理結算/分潤系統** 等功能。類似 [TicketTool](https://docs.tickettool.xyz/)，但更精確、更客製化。

---

## 📋 功能總覽

### 系統一：商品目錄開單系統（圖1、2）

此系統在指定頻道顯示商品目錄面板，用戶透過下拉選單選擇商品後自動開單。

| 功能 | 說明 |
|------|------|
| 商品目錄面板 | 嵌入訊息展示商品列表、付款方式 |
| 下拉選單選擇 | 用戶從下拉選單中選擇想購買的商品 |
| 自動開單 | 選擇商品後自動建立私人頻道 |
| 開單資訊顯示 | 開單後顯示所選商品名稱、價格方案、開單時間 |
| 管理員領單 | 管理員可認領負責此工單 |
| 設定金額 | 管理員可設定此單金額 |
| 結單按鈕 | 兩次確認機制防止誤觸 |
| 聊天記錄保存 | 結單時保存到結單頻道 + 代理結單頻道 |

### 系統二：客服工單系統（圖3、4、5）

此系統提供 Priority Support 面板，用戶點擊按鈕後選擇工單原因開單。

| 功能 | 說明 |
|------|------|
| VIP 支援面板 | 嵌入訊息展示支援資訊 |
| Priority Ticket 按鈕 | 紅色醒目按鈕觸發開單流程 |
| 原因選擇下拉選單 | Buy / Support / Other |
| 自動開單 | 選擇原因後自動建立私人頻道 |
| 管理員領單 | 管理員可認領負責此工單 |
| 設定金額 | 管理員可設定此單金額 |
| 結單按鈕 | 兩次確認機制防止誤觸 |
| 聊天記錄保存 | 結單時保存到結單頻道 + 代理結單頻道 |

### 系統三：VIP 專屬工單

| 功能 | 說明 |
|------|------|
| VIP 身分組限制 | 僅 `vip-buyer` 身分組可見 VIP 頻道 |
| VIP 專屬按鈕 | 👑 VIP Priority Ticket 按鈕 |
| 身分驗證 | 點擊時自動檢查是否有 VIP 身分組 |

### 員工領單機制

開單後，機器人會自動發送一則 **僅管理員可見** 的訊息，包含：
- 「📋 此單總負責人」標題
- 「此票單尚未有管理員負責」提示
- 綠色「📋 負責此單」按鈕
- @管理員 提及通知

管理員點擊按鈕後即認領此工單，認領資訊會在結單時記錄。

### 代理結算/分潤系統

結單後，工單資訊會自動發送到 **代理結單頻道**，包含：
- 工單類型、客戶、負責人、訂單金額
- 💸 **撥款分潤** 按鈕（僅老闆可用）
- ✅ **標記已結算** 按鈕（僅老闆可用）

老闆點擊撥款按鈕後可輸入撥款金額和備註。

---

## 🔧 身分組配置

| 身分組 | ID | 用途 |
|--------|-----|------|
| 管理員 | `1474803724978360586` | 領單、設定金額、管理工單 |
| 老闆 | `1474803734851748060` | 撥款分潤、標記結算 |
| VIP Buyer | `1474804234393227525` | 存取 VIP 專屬頻道和工單 |

## 📡 頻道配置

### 商品目錄開單系統

| 頻道 | ID |
|------|-----|
| 開單類別 | `1474794311047446699` |
| 開單頻道（面板） | `1474794324758892605` |
| 結單頻道 | `1474794844520972428` |

### 客服工單系統 / VIP 工單

| 頻道 | ID |
|------|-----|
| 開單類別 | `1474799425309376676` |
| 開單頻道（面板） | `1474799468800118815` |
| 結單頻道 | `1474799482750369792` |

### 代理結算系統

| 頻道 | ID |
|------|-----|
| 結算類別 | `1474802616109367596` |
| 代理結單頻道 | `1474802583444127876` |

---

## 🔧 前置需求

1. **Discord Bot Token**：前往 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式並取得 Token。
2. **Bot 權限**：邀請 Bot 時需要以下權限：
   - `Manage Channels`、`Manage Roles`、`Send Messages`、`Embed Links`
   - `Read Message History`、`Use Application Commands`、`Manage Messages`
   - `Mention Everyone`（用於 @管理員 通知）
3. **Privileged Gateway Intents**：在 Developer Portal 中啟用：
   - `MESSAGE CONTENT INTENT`
   - `SERVER MEMBERS INTENT`

---

## 📁 專案結構

```
discord-ticket-bot/
├── bot.py              # 主程式（所有功能）
├── requirements.txt    # Python 依賴
├── .env.example        # 環境變數範例
├── .gitignore          # Git 忽略文件
├── Procfile            # Railway 部署配置
├── railway.toml        # Railway 部署設定
├── nixpacks.toml       # Nixpacks 建構設定
└── README.md           # 本文件
```

---

## 🚀 部署到 Railway

### 步驟 1：準備 GitHub 倉庫

```bash
cd discord-ticket-bot
git init
git add .
git commit -m "Initial commit: Discord Ticket Bot"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 步驟 2：在 Railway 上部署

1. 前往 [railway.com](https://railway.com) 並登入
2. 點擊 **New Project** → **Deploy from GitHub repo**
3. 選擇你的 GitHub 倉庫
4. 在 **Variables** 頁面新增環境變數：

| 變數名稱 | 值 |
|----------|-----|
| `DISCORD_TOKEN` | 你的 Discord Bot Token |

5. Railway 會自動偵測並開始部署
6. 確認部署成功後，Bot 將自動上線

### 步驟 3：設置面板和權限

Bot 上線後，在 Discord 中依序使用以下斜線命令：

```
/setup-vip-permissions   → 設置 VIP 頻道權限（僅 vip-buyer 可見）
/setup-product           → 在商品開單頻道設置商品目錄面板
/setup-support           → 在客服開單頻道設置客服工單面板
/setup-vip               → 在 VIP 頻道設置 VIP 專屬工單面板
```

---

## 📝 所有斜線命令

| 命令 | 權限 | 說明 |
|------|------|------|
| `/setup-product` | 管理員 | 設置商品目錄面板 |
| `/setup-support` | 管理員 | 設置客服工單面板 |
| `/setup-vip` | 管理員 | 設置 VIP 專屬工單面板 |
| `/setup-vip-permissions` | 管理員 | 設置 VIP 頻道權限（僅 vip-buyer 可見） |
| `/set-price` | 管理員 | 在工單頻道中設定訂單金額 |
| `/add-product` | 管理員 | 動態新增商品 |
| `/remove-product` | 管理員 | 移除商品 |
| `/list-products` | 管理員 | 列出所有商品 |

---

## 🔄 完整工作流程

### 商品購買流程

```
用戶在商品頻道看到面板
    ↓
從下拉選單選擇商品（如 Seliware）
    ↓
Bot 自動建立私人頻道（order-用戶名）
    ↓
頻道內顯示：
  ① 選擇的商品、價格方案、開單資訊（所有人可見）
  ② 結單按鈕（所有人可見）
  ③ @管理員 領單訊息 + 「負責此單」按鈕（管理員可見）
  ④ 管理員操作面板 + 「設定金額」按鈕（管理員可見）
    ↓
管理員點擊「負責此單」認領工單
    ↓
管理員點擊「設定金額」輸入此單金額
    ↓
用戶與工作人員溝通
    ↓
點擊「🔒 結單」→「✅ 確認結單」（兩次確認）
    ↓
聊天記錄保存到結單頻道
    ↓
結算資訊發送到代理結單頻道（含金額、負責人）
    ↓
老闆在代理結單頻道點擊「💸 撥款分潤」進行撥款
    ↓
老闆點擊「✅ 標記已結算」完成結算
    ↓
頻道自動刪除
```

### 客服工單 / VIP 工單流程

```
用戶點擊「Priority Ticket」/「VIP Priority Ticket」按鈕
    ↓
選擇原因（Buy / Support / Other）
    ↓
Bot 自動建立私人頻道
    ↓
（同上：領單 → 設定金額 → 溝通 → 結單 → 代理結算）
```

---

## ⚙️ 自訂配置

### 修改身分組 ID

在 `bot.py` 頂部修改：

```python
ADMIN_ROLE_ID = 1474803724978360586       # 管理員
BOSS_ROLE_ID = 1474803734851748060        # 老闆
VIP_BUYER_ROLE_ID = 1474804234393227525   # VIP Buyer
```

### 新增商品（代碼方式）

在 `PRODUCTS` 列表中新增：

```python
{
    "name": "新商品名稱",
    "emoji": "",
    "display_emoji": "🔷",
    "description": "3.99$ / week | 9.99$ / month",
    "prices": {
        "Weekly": "$3.99",
        "Monthly": "$9.99"
    },
    "details": "商品詳細說明"
},
```

### 修改工單原因

在 `TICKET_REASONS` 列表中修改或新增。

---

## 🔒 結單記錄格式

結單後，以下資訊會被保存到 **結單頻道** 和 **代理結單頻道**：

| 項目 | 說明 |
|------|------|
| 工單類型 | 商品購買 / 客服工單 / VIP 工單 |
| 開單者 | 用戶名稱和 mention |
| 開單選擇 | 選擇的商品或工單原因 |
| 負責人 | 認領此單的管理員 |
| 訂單金額 | 管理員設定的金額（特別註明） |
| 訊息數量 | 聊天記錄總數 |
| 開單/結單時間 | 時間戳 |
| 完整聊天記錄 | 所有訊息內容（含附件） |

---

## ❓ 常見問題

**Q: Bot 重啟後面板按鈕還能用嗎？**
A: 可以。Bot 使用了持久化 View，重啟後所有按鈕和下拉選單仍然有效。

**Q: 如何獲取頻道/身分組 ID？**
A: 在 Discord 設定中開啟「開發者模式」，然後右鍵點擊 → 複製 ID。

**Q: 撥款分潤是自動的嗎？**
A: 不是。撥款需要老闆手動在代理結單頻道操作，輸入撥款金額。

**Q: VIP 頻道的權限是自動設置的嗎？**
A: 使用 `/setup-vip-permissions` 命令即可自動設置，使 VIP 頻道僅對 vip-buyer 身分組可見。

---

## 📄 授權

此專案僅供學習和個人使用。
