import discord
from discord.ext import commands
from discord import app_commands
import os
import sys
import datetime
import asyncio
import io
import json
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 配置區域 - 可自行修改
# ============================================================

# Bot Token（從環境變數讀取）
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ============================================================
# 身分組 ID
# ============================================================
ADMIN_ROLE_ID = 1474803724978360586       # 管理員身分組
BOSS_ROLE_ID = 1474803734851748060        # 老闆身分組
VIP_BUYER_ROLE_ID = 1474804234393227525   # VIP Buyer 身分組

# ============================================================
# 系統一：商品目錄開單系統
# ============================================================
PRODUCT_CATEGORY_ID = 1474794311047446699       # 開單類別
PRODUCT_PANEL_CHANNEL_ID = 1474794324758892605  # 開單頻道（面板所在）
PRODUCT_LOG_CHANNEL_ID = 1474794844520972428    # 結單頻道（記錄保存）

# ============================================================
# 系統二：客服工單系統（一般）
# ============================================================
SUPPORT_CATEGORY_ID = 1474799425309376676       # 開單類別
SUPPORT_PANEL_CHANNEL_ID = 1474799468800118815  # 開單頻道（面板所在）
SUPPORT_LOG_CHANNEL_ID = 1474799482750369792    # 結單頻道（記錄保存）

# ============================================================
# VIP 頻道（vip-buyer-support）- 僅 vip-buyer 身分組可見
# ============================================================
VIP_CATEGORY_ID = 1474799425309376676           # 開單類別（與客服共用）
VIP_PANEL_CHANNEL_ID = 1474799468800118815      # 開單頻道
VIP_LOG_CHANNEL_ID = 1474799482750369792        # 結單頻道

# ============================================================
# 代理結算系統
# ============================================================
SETTLEMENT_CATEGORY_ID = 1474802616109367596    # 結算類別
AGENT_LOG_CHANNEL_ID = 1474802583444127876      # 代理結單頻道

# ============================================================
# 餘額頻道 ID（使用 /setup-balance-channel 設定）
# ============================================================
BALANCE_CHANNEL_ID = 0  # 預設為 0，使用命令設定

# ============================================================
# 商品列表 - 可自行新增/修改商品
# ============================================================
PRODUCTS = [
    {
        "name": "Seliware",
        "emoji": "",
        "display_emoji": "🔷",
        "description": "3.99$ / week | 9.99$ / month",
        "prices": {
            "Weekly": "$3.99",
            "Monthly": "$9.99"
        },
        "details": "Premium Roblox exploit with advanced features."
    },
    {
        "name": "Volt",
        "emoji": "",
        "display_emoji": "⚡",
        "description": "5.99$ / week | 19.99$ / month | 49.99$ / 90 days",
        "prices": {
            "Weekly": "$5.99",
            "Monthly": "$19.99",
            "90 Days": "$49.99"
        },
        "details": "High-performance Roblox tool with premium support."
    },
    {
        "name": "Volcano",
        "emoji": "",
        "display_emoji": "🌋",
        "description": "5.99$ / week | 19.99$ / month",
        "prices": {
            "Weekly": "$5.99",
            "Monthly": "$19.99"
        },
        "details": "Powerful Roblox exploit with unique capabilities."
    },
    {
        "name": "Wave",
        "emoji": "",
        "display_emoji": "🌊",
        "description": "2.49$ / day | 5.99$ / week | 18.99$ / month | 39.99$ / 90 days",
        "prices": {
            "Daily": "$2.49",
            "Weekly": "$5.99",
            "Monthly": "$18.99",
            "90 Days": "$39.99"
        },
        "details": "Versatile Roblox tool with flexible pricing options."
    },
    {
        "name": "Bunni.lol",
        "emoji": "",
        "display_emoji": "🐰",
        "description": "1.00$ / 2 days | 3.00$ / week | 9.99$ / month | 34.99$ / lifetime",
        "prices": {
            "2 Days": "$1.00",
            "Weekly": "$3.00",
            "Monthly": "$9.99",
            "Lifetime": "$34.99"
        },
        "details": "Affordable Roblox exploit with lifetime option."
    },
]

# ============================================================
# 客服工單原因列表
# ============================================================
TICKET_REASONS = [
    {
        "label": "Buy",
        "value": "buy",
        "emoji": "💰",
        "description": "Questions about purchasing products"
    },
    {
        "label": "Support",
        "value": "support",
        "emoji": "☂️",
        "description": "Technical support or issues"
    },
    {
        "label": "Other",
        "value": "other",
        "emoji": "❇️",
        "description": "Other questions or requests"
    },
]

# ============================================================
# 內存存儲
# ============================================================
# 工單資料: { channel_id: { ... } }
ticket_data = {}
# 餘額資料: { user_id: float }
balance_data = {}

BALANCE_FILE = "balances.json"

def load_balance_data():
    """從文件載入餘額資料"""
    global balance_data
    try:
        if os.path.exists(BALANCE_FILE):
            with open(BALANCE_FILE, "r") as f:
                raw = json.load(f)
                balance_data = {int(k): float(v) for k, v in raw.items()}
                print(f"💰 已載入 {len(balance_data)} 筆餘額資料")
    except Exception as e:
        print(f"⚠️ 載入餘額資料失敗: {e}")
        balance_data = {}

def save_balance_data():
    """保存餘額資料到文件"""
    try:
        with open(BALANCE_FILE, "w") as f:
            json.dump({str(k): v for k, v in balance_data.items()}, f, indent=2)
    except Exception as e:
        print(f"⚠️ 保存餘額資料失敗: {e}")
# 已結單的頻道集合（防止重複結單）
closed_tickets = set()

# ============================================================
# Bot 初始化
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ============================================================
# 工具函數
# ============================================================

def has_role(member: discord.Member, role_id: int) -> bool:
    return any(role.id == role_id for role in member.roles)

def is_admin(member: discord.Member) -> bool:
    return has_role(member, ADMIN_ROLE_ID)

def is_boss(member: discord.Member) -> bool:
    return has_role(member, BOSS_ROLE_ID)

def is_vip_buyer(member: discord.Member) -> bool:
    return has_role(member, VIP_BUYER_ROLE_ID)

def get_ticket_data(channel_id: int) -> dict:
    if channel_id not in ticket_data:
        ticket_data[channel_id] = {
            "price": None,
            "claimed_by": None,
            "claimed_name": None,
            "ticket_type": "未知",
            "ticket_info": "未知",
            "owner_id": None,
            "log_channel_id": None,
            "is_vip": False,
        }
    return ticket_data[channel_id]


# ============================================================
# 結單記錄保存（簡潔格式：Embed + txt 附件，如圖三）
# ============================================================

async def save_transcript(channel: discord.TextChannel, log_channel: discord.TextChannel,
                          ticket_owner: discord.Member, ticket_type: str, ticket_info: str,
                          price: str = None, claimed_by_name: str = None,
                          closer: discord.Member = None):
    """保存聊天記錄到結單頻道 - 簡潔 Embed + txt 附件格式"""
    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        messages.append(msg)

    if not messages:
        return

    # 建立聊天記錄 txt 文件
    chat_lines = []
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content if msg.content else "[嵌入訊息/附件]"
        if msg.attachments:
            attachments_text = " | ".join([att.url for att in msg.attachments])
            content += f"\n  附件: {attachments_text}"
        if msg.embeds and not msg.content:
            embed_texts = []
            for emb in msg.embeds:
                if emb.title:
                    embed_texts.append(f"[Embed: {emb.title}]")
                if emb.description:
                    embed_texts.append(emb.description[:100])
            content = " | ".join(embed_texts) if embed_texts else "[嵌入訊息]"
        chat_lines.append(f"[{timestamp}] {msg.author}: {content}")

    chat_text = "\n".join(chat_lines)

    # 建立 txt 附件
    file_bytes = chat_text.encode("utf-8")
    txt_file = discord.File(
        io.BytesIO(file_bytes),
        filename=f"{channel.name}-log.txt"
    )

    # 建立簡潔的 Embed（類似圖三的樣式）
    open_time = messages[0].created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    transcript_embed = discord.Embed(
        title=f"📋 票單 #{channel.name} 聊天記錄",
        color=discord.Color.purple()
    )

    transcript_embed.add_field(
        name="",
        value=f"**開單者：**{ticket_owner.mention} (<@{ticket_owner.id}>)",
        inline=False
    )

    if claimed_by_name:
        transcript_embed.add_field(
            name="",
            value=f"**負責人：**{claimed_by_name}",
            inline=False
        )
    else:
        transcript_embed.add_field(
            name="",
            value="**負責人：**❌ 無人認領",
            inline=False
        )

    if closer:
        transcript_embed.add_field(
            name="",
            value=f"**結單者：**{closer.mention} (<@{closer.id}>)",
            inline=False
        )

    transcript_embed.add_field(
        name="",
        value=f"**開單時間：**{open_time}",
        inline=False
    )

    await log_channel.send(embed=transcript_embed, file=txt_file)


async def send_to_agent_log(guild: discord.Guild, channel: discord.TextChannel,
                            ticket_owner: discord.Member, ticket_type: str, ticket_info: str,
                            price: str = None, claimed_by_name: str = None):
    """發送結單資訊到代理結單頻道，供老闆撥款分潤"""
    agent_log = guild.get_channel(AGENT_LOG_CHANNEL_ID)
    if not agent_log:
        return

    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    agent_embed = discord.Embed(
        title="💼 代理結算單 | Agent Settlement",
        description="此工單已結單，以下為結算資訊。老闆可進行撥款分潤操作。",
        color=discord.Color.purple(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    agent_embed.add_field(name="📌 工單類型", value=ticket_type, inline=True)
    agent_embed.add_field(name="👤 客戶", value=f"{ticket_owner.mention} ({ticket_owner})", inline=True)
    agent_embed.add_field(name="📝 開單選擇", value=ticket_info, inline=False)

    if claimed_by_name:
        agent_embed.add_field(name="👨‍💼 負責人（代理）", value=claimed_by_name, inline=True)
    else:
        agent_embed.add_field(name="👨‍💼 負責人（代理）", value="無人認領", inline=True)

    if price:
        agent_embed.add_field(name="💰 訂單金額", value=f"**{price}**", inline=True)
    else:
        agent_embed.add_field(name="💰 訂單金額", value="未設定", inline=True)

    agent_embed.add_field(name="📅 結單時間", value=f"<t:{now_ts}:F>", inline=True)
    agent_embed.add_field(name="🏷️ 原頻道名稱", value=f"`{channel.name}`", inline=True)
    agent_embed.set_footer(text="請老闆確認後進行撥款分潤")

    data = ticket_data.get(channel.id, {})
    claimed_by_id = data.get("claimed_by")

    payout_view = PayoutView(
        ticket_owner_id=ticket_owner.id,
        ticket_owner_name=str(ticket_owner),
        claimed_by_id=claimed_by_id,
        claimed_by_name=claimed_by_name or "無",
        price=price or "未設定",
        ticket_type=ticket_type,
        ticket_info=ticket_info,
        channel_name=channel.name
    )
    await agent_log.send(embed=agent_embed, view=payout_view)


# ============================================================
# 設定金額 Modal（僅 VIP 工單使用）
# ============================================================

class SetPriceModal(discord.ui.Modal, title="💰 設定訂單金額 | Set Order Price"):
    price_input = discord.ui.TextInput(
        label="訂單金額 (Order Price)",
        placeholder="例如: 5000台幣 或 $19.99 USD",
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ 僅管理員可設定金額。", ephemeral=True)
            return

        channel = interaction.channel
        price_value = self.price_input.value
        data = get_ticket_data(channel.id)
        data["price"] = price_value

        price_embed = discord.Embed(
            title="💰 訂單金額已設定 | Price Set",
            description=(
                f"**金額: {price_value}**\n\n"
                f"設定者: {interaction.user.mention}\n"
                f"時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=price_embed)


# ============================================================
# 管理員操作面板（設定金額按鈕）- 僅 VIP 工單
# ============================================================

class AdminTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 設定金額 | Set Price", style=discord.ButtonStyle.primary, custom_id="set_price_btn")
    async def set_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ 僅管理員可使用此功能。", ephemeral=True)
            return
        modal = SetPriceModal()
        await interaction.response.send_modal(modal)


# ============================================================
# 員工領單按鈕
# ============================================================

class ClaimTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 負責此單", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ 僅管理員可認領工單。", ephemeral=True)
            return

        channel = interaction.channel
        data = get_ticket_data(channel.id)

        if data["claimed_by"]:
            await interaction.response.send_message(
                f"❌ 此工單已由 **{data['claimed_name']}** 認領。",
                ephemeral=True
            )
            return

        data["claimed_by"] = interaction.user.id
        data["claimed_name"] = str(interaction.user)

        claimed_embed = discord.Embed(
            title="📋 此單總負責人",
            description=(
                f"✅ 此票單已由 **{interaction.user.mention}** 負責。\n\n"
                f"認領時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.green()
        )
        claimed_embed.set_footer(text="此訊息僅管理員可見")

        button.disabled = True
        button.label = f"✅ 已由 {interaction.user.display_name} 負責"
        button.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(embed=claimed_embed, view=self)

        notify_embed = discord.Embed(
            description=f"👨‍💼 管理員 **{interaction.user.display_name}** 已認領負責此工單。",
            color=discord.Color.green()
        )
        await channel.send(embed=notify_embed)


# ============================================================
# 撥款分潤（代理結單頻道 - 老闆用）
# ============================================================

class PayoutModal(discord.ui.Modal, title="💸 撥款分潤 | Payout"):
    payout_amount = discord.ui.TextInput(
        label="撥款金額 (Payout Amount)",
        placeholder="例如: 200",
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )
    payout_note = discord.ui.TextInput(
        label="備註 (Note)",
        placeholder="選填備註...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=200
    )

    def __init__(self, claimed_by_name: str, claimed_by_id: int, price: str, channel_name: str):
        super().__init__()
        self.claimed_by_name = claimed_by_name
        self.claimed_by_id = claimed_by_id
        self.price = price
        self.channel_name = channel_name

    async def on_submit(self, interaction: discord.Interaction):
        if not is_boss(interaction.user):
            await interaction.response.send_message("❌ 僅老闆可進行撥款操作。", ephemeral=True)
            return

        # 更新餘額
        try:
            amount = float(self.payout_amount.value.replace("$", "").replace(",", "").strip())
            if self.claimed_by_id and self.claimed_by_id > 0:
                if self.claimed_by_id not in balance_data:
                    balance_data[self.claimed_by_id] = 0.0
                balance_data[self.claimed_by_id] += amount
                save_balance_data()
                print(f"💰 已更新用戶 {self.claimed_by_id} 餘額: +{amount} = {balance_data[self.claimed_by_id]}")
        except (ValueError, TypeError):
            pass

        payout_embed = discord.Embed(
            title="✅ 撥款完成 | Payout Completed",
            description=(
                f"**工單:** `{self.channel_name}`\n"
                f"**訂單金額:** {self.price}\n"
                f"**代理（負責人）:** {self.claimed_by_name}\n"
                f"**撥款金額:** {self.payout_amount.value}\n"
                f"**撥款者:** {interaction.user.mention}\n"
                f"**時間:** <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.green()
        )
        if self.payout_note.value:
            payout_embed.add_field(name="📝 備註", value=self.payout_note.value, inline=False)

        await interaction.response.send_message(embed=payout_embed)


class PayoutView(discord.ui.View):
    def __init__(self, ticket_owner_id: int, ticket_owner_name: str,
                 claimed_by_id: int, claimed_by_name: str,
                 price: str, ticket_type: str, ticket_info: str, channel_name: str):
        super().__init__(timeout=None)
        self.ticket_owner_id = ticket_owner_id
        self.ticket_owner_name = ticket_owner_name
        self.claimed_by_id = claimed_by_id
        self.claimed_by_name = claimed_by_name
        self.price = price
        self.ticket_type = ticket_type
        self.ticket_info = ticket_info
        self.channel_name = channel_name

    @discord.ui.button(label="💸 撥款分潤 | Payout", style=discord.ButtonStyle.success, custom_id="payout_btn")
    async def payout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_boss(interaction.user):
            await interaction.response.send_message("❌ 僅老闆身分組可進行撥款操作。", ephemeral=True)
            return

        modal = PayoutModal(
            claimed_by_name=self.claimed_by_name,
            claimed_by_id=self.claimed_by_id,
            price=self.price,
            channel_name=self.channel_name
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="✅ 標記已結算", style=discord.ButtonStyle.secondary, custom_id="mark_settled_btn")
    async def mark_settled(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_boss(interaction.user):
            await interaction.response.send_message("❌ 僅老闆身分組可進行此操作。", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        settled_embed = discord.Embed(
            title="💼 代理結算單 | Agent Settlement",
            description=(
                f"✅ **已結算** - 由 {interaction.user.mention} 標記\n\n"
                f"**工單:** `{self.channel_name}`\n"
                f"**客戶:** {self.ticket_owner_name}\n"
                f"**負責人:** {self.claimed_by_name}\n"
                f"**金額:** {self.price}\n"
                f"**結算時間:** <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=settled_embed, view=self)


# ============================================================
# 結單按鈕 View（兩次確認 - 僅管理員可結單，防止重複結單）
# ============================================================

class CloseTicketView(discord.ui.View):
    """結單按鈕 - 第一次點擊（僅管理員可操作）"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 結單 | Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_first")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 僅管理員可結單
        if not is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 僅管理員可進行結單操作。\nOnly admins can close tickets.",
                ephemeral=True
            )
            return

        # 檢查是否已結單
        if interaction.channel.id in closed_tickets:
            await interaction.response.send_message("❌ 此工單已經結單，請勿重複操作。", ephemeral=True)
            return

        data = get_ticket_data(interaction.channel.id)
        price_text = f"\n**💰 訂單金額: {data['price']}**" if data.get("price") else ""
        claimed_text = f"\n**👨‍💼 負責人: {data['claimed_name']}**" if data.get("claimed_name") else ""

        confirm_embed = discord.Embed(
            title="⚠️ 確認結單 | Confirm Close",
            description=(
                "你確定要結單嗎？此操作無法撤銷。\n"
                "Are you sure you want to close this ticket? This action cannot be undone.\n\n"
                "**聊天記錄將會被保存到結單區。**\n"
                "**Chat logs will be saved to the transcript channel.**"
                f"{price_text}{claimed_text}"
            ),
            color=discord.Color.orange()
        )
        confirm_view = ConfirmCloseView()
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view)


class ConfirmCloseView(discord.ui.View):
    """結單確認 - 第二次確認（僅管理員可操作，防止重複結單）"""
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="✅ 確認結單 | Confirm Close", style=discord.ButtonStyle.danger, custom_id="close_ticket_confirm")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 再次檢查管理員權限
        if not is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 僅管理員可進行結單操作。\nOnly admins can close tickets.",
                ephemeral=True
            )
            return

        # 防止重複結單
        if interaction.channel.id in closed_tickets:
            await interaction.response.send_message("❌ 此工單已經結單，請勿重複操作。", ephemeral=True)
            return

        # 標記為已結單（立即標記防止並發）
        closed_tickets.add(interaction.channel.id)

        # 禁用所有按鈕防止再次點擊
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        channel = interaction.channel
        guild = interaction.guild
        data = get_ticket_data(channel.id)

        log_channel_id = data.get("log_channel_id", PRODUCT_LOG_CHANNEL_ID)
        ticket_type = data.get("ticket_type", "未知")
        ticket_info = data.get("ticket_info", "未知")
        price = data.get("price")
        claimed_by_name = data.get("claimed_name")
        is_vip = data.get("is_vip", False)

        # 從頻道主題解析
        if channel.topic:
            if "商品購買工單" in channel.topic:
                ticket_type = "商品購買 | Product Order"
                log_channel_id = PRODUCT_LOG_CHANNEL_ID
                try:
                    product_name = channel.topic.split("product:")[1].split("|")[0].strip()
                    product = next((p for p in PRODUCTS if p["name"] == product_name), None)
                    if product:
                        ticket_info = f"商品: {product['name']} | 價格: {product['description']}"
                except (IndexError, StopIteration):
                    pass
            elif "VIP工單" in channel.topic:
                ticket_type = "VIP 客服工單 | VIP Support Ticket"
                log_channel_id = VIP_LOG_CHANNEL_ID
                is_vip = True
                try:
                    reason_label = channel.topic.split("reason:")[1].split("|")[0].strip()
                    reason = next((r for r in TICKET_REASONS if r["label"] == reason_label), None)
                    if reason:
                        ticket_info = f"原因: {reason['emoji']} {reason['label']} - {reason['description']}"
                except (IndexError, StopIteration):
                    pass
            elif "客服工單" in channel.topic:
                ticket_type = "客服工單 | Support Ticket"
                log_channel_id = SUPPORT_LOG_CHANNEL_ID
                try:
                    reason_label = channel.topic.split("reason:")[1].split("|")[0].strip()
                    reason = next((r for r in TICKET_REASONS if r["label"] == reason_label), None)
                    if reason:
                        ticket_info = f"原因: {reason['emoji']} {reason['label']} - {reason['description']}"
                except (IndexError, StopIteration):
                    pass

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            await interaction.followup.send("❌ 找不到結單頻道，請聯繫管理員。", ephemeral=True)
            closed_tickets.discard(channel.id)
            return

        # 發送結單中提示
        closing_embed = discord.Embed(
            title="🔒 結單中... | Closing Ticket...",
            description="正在保存聊天記錄...\nSaving chat transcript...",
            color=discord.Color.red()
        )
        await channel.send(embed=closing_embed)

        # 獲取工單擁有者
        ticket_owner = interaction.user
        if channel.topic:
            try:
                owner_id = int(channel.topic.split("owner:")[1].split("|")[0].strip())
                member = guild.get_member(owner_id)
                if member:
                    ticket_owner = member
            except (ValueError, IndexError):
                pass

        # 保存聊天記錄到結單頻道（簡潔格式：Embed + txt 附件）
        await save_transcript(channel, log_channel, ticket_owner, ticket_type, ticket_info,
                              price=price, claimed_by_name=claimed_by_name,
                              closer=interaction.user)

        # 僅 VIP 工單才發送到代理結單頻道
        if is_vip:
            await send_to_agent_log(guild, channel, ticket_owner, ticket_type, ticket_info,
                                    price=price, claimed_by_name=claimed_by_name)

        # 清理內存
        if channel.id in ticket_data:
            del ticket_data[channel.id]

        await asyncio.sleep(3)
        await channel.delete(reason=f"工單結單 by {interaction.user}")

    @discord.ui.button(label="❌ 取消 | Cancel", style=discord.ButtonStyle.secondary, custom_id="close_ticket_cancel")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ 已取消結單。| Close cancelled.", ephemeral=True)
        self.stop()


# ============================================================
# 開單後發送管理員專用訊息
# ============================================================

async def send_admin_panel(channel: discord.TextChannel, guild: discord.Guild, is_vip_ticket: bool = False):
    """在開單頻道發送管理員操作面板"""
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    if not admin_role:
        return

    # 發送領單訊息（@管理員）
    claim_embed = discord.Embed(
        title="📋 此單總負責人",
        description=(
            "此票單尚未有管理員負責。\n\n"
            "請點擊下方按鈕認領此票單。\n\n"
            "此訊息僅管理員可見。"
        ),
        color=discord.Color.red(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    claim_embed.set_footer(text="此訊息僅管理員可見")

    claim_view = ClaimTicketView()
    await channel.send(
        content=f"{admin_role.mention} 新票單已建立！",
        embed=claim_embed,
        view=claim_view
    )

    # 僅 VIP 工單才顯示設定金額按鈕和提示
    if is_vip_ticket:
        admin_embed = discord.Embed(
            title="⚙️ 管理員操作面板 | Admin Panel",
            description=(
                "**僅管理員可使用以下功能：**\n\n"
                "💰 **設定金額** - 設定此工單的訂單金額\n"
                "（結單時金額將被記錄到結單區和代理結單頻道）"
            ),
            color=discord.Color.blurple()
        )
        admin_embed.set_footer(text="僅管理員可操作")

        admin_view = AdminTicketView()
        await channel.send(embed=admin_embed, view=admin_view)


# ============================================================
# 系統一：商品目錄開單系統
# ============================================================

class ProductSelectMenu(discord.ui.Select):
    def __init__(self):
        options = []
        for product in PRODUCTS:
            options.append(
                discord.SelectOption(
                    label=product["name"],
                    description=product["description"][:100],
                    value=product["name"],
                    emoji=product["display_emoji"]
                )
            )
        super().__init__(
            placeholder="Select a product to view...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="product_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_name = self.values[0]
        product = next((p for p in PRODUCTS if p["name"] == selected_name), None)

        if not product:
            await interaction.response.send_message("❌ 商品不存在。", ephemeral=True)
            return

        guild = interaction.guild
        category = guild.get_channel(PRODUCT_CATEGORY_ID)

        if not category:
            await interaction.response.send_message("❌ 找不到開單類別，請聯繫管理員。", ephemeral=True)
            return

        existing = discord.utils.get(
            guild.text_channels,
            name=f"order-{interaction.user.name.lower().replace(' ', '-')}"
        )
        if existing:
            await interaction.response.send_message(
                f"❌ 你已經有一個開啟的工單: {existing.mention}\n請先結單後再開新單。",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        admin_role = guild.get_role(ADMIN_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                attach_files=True, embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                manage_channels=True, manage_messages=True
            )
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                attach_files=True, embed_links=True
            )

        ticket_channel = await guild.create_text_channel(
            name=f"order-{interaction.user.name.lower().replace(' ', '-')}",
            category=category,
            overwrites=overwrites,
            topic=f"owner:{interaction.user.id} | product:{selected_name} | 商品購買工單"
        )

        # 正常開單：is_vip = False，不需要設定金額
        data = get_ticket_data(ticket_channel.id)
        data["ticket_type"] = "商品購買 | Product Order"
        data["ticket_info"] = f"商品: {product['name']} | 價格: {product['description']}"
        data["owner_id"] = interaction.user.id
        data["log_channel_id"] = PRODUCT_LOG_CHANNEL_ID
        data["is_vip"] = False

        price_text = "\n".join([f"• **{period}**: {price}" for period, price in product["prices"].items()])

        ticket_embed = discord.Embed(
            title="🛒 商品購買工單 | Product Order",
            description=(
                f"歡迎 {interaction.user.mention}！\n\n"
                f"你選擇了以下商品：\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**{product['display_emoji']} {product['name']}**\n"
                f"{product['details']}\n\n"
                f"**💰 價格方案 | Pricing:**\n{price_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**📋 開單資訊 | Ticket Info:**\n"
                f"• 開單者: {interaction.user.mention}\n"
                f"• 選擇商品: **{product['name']}**\n"
                f"• 開單時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>\n\n"
                f"請告知您想購買的方案，工作人員將盡快為您服務！\n"
                f"Please let us know which plan you'd like to purchase. Staff will assist you shortly!"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        ticket_embed.set_footer(text=f"工單 ID: {ticket_channel.id}")

        close_view = CloseTicketView()
        await ticket_channel.send(embed=ticket_embed, view=close_view)

        # 正常開單：不含設定金額按鈕（is_vip_ticket=False）
        await send_admin_panel(ticket_channel, guild, is_vip_ticket=False)

        await interaction.followup.send(
            f"✅ 已為您開單！請前往 {ticket_channel.mention} 查看。",
            ephemeral=True
        )


class ProductSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductSelectMenu())


# ============================================================
# 系統二：客服工單系統（一般 + VIP）
# ============================================================

class TicketReasonSelect(discord.ui.Select):
    def __init__(self, is_vip: bool = False):
        self.is_vip = is_vip
        options = []
        for reason in TICKET_REASONS:
            options.append(
                discord.SelectOption(
                    label=reason["label"],
                    description=reason["description"],
                    value=reason["value"],
                    emoji=reason["emoji"]
                )
            )
        custom_id = "vip_ticket_reason_select" if is_vip else "ticket_reason_select"
        super().__init__(
            placeholder="Select ticket reason...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=custom_id
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        reason = next((r for r in TICKET_REASONS if r["value"] == selected_value), None)

        if not reason:
            await interaction.response.send_message("❌ 無效的選擇。", ephemeral=True)
            return

        guild = interaction.guild

        if self.is_vip:
            category_id = VIP_CATEGORY_ID
            log_channel_id = VIP_LOG_CHANNEL_ID
            channel_prefix = "vip-ticket"
            topic_suffix = "VIP工單"
            ticket_type = "VIP 客服工單 | VIP Support Ticket"
        else:
            category_id = SUPPORT_CATEGORY_ID
            log_channel_id = SUPPORT_LOG_CHANNEL_ID
            channel_prefix = "ticket"
            topic_suffix = "客服工單"
            ticket_type = "客服工單 | Support Ticket"

        category = guild.get_channel(category_id)
        if not category:
            await interaction.response.send_message("❌ 找不到開單類別，請聯繫管理員。", ephemeral=True)
            return

        existing = discord.utils.get(
            guild.text_channels,
            name=f"{channel_prefix}-{interaction.user.name.lower().replace(' ', '-')}"
        )
        if existing:
            await interaction.response.send_message(
                f"❌ 你已經有一個開啟的工單: {existing.mention}\n請先結單後再開新單。",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        admin_role = guild.get_role(ADMIN_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                attach_files=True, embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                manage_channels=True, manage_messages=True
            )
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True,
                attach_files=True, embed_links=True
            )

        ticket_channel = await guild.create_text_channel(
            name=f"{channel_prefix}-{interaction.user.name.lower().replace(' ', '-')}",
            category=category,
            overwrites=overwrites,
            topic=f"owner:{interaction.user.id} | reason:{reason['label']} | {topic_suffix}"
        )

        data = get_ticket_data(ticket_channel.id)
        data["ticket_type"] = ticket_type
        data["ticket_info"] = f"原因: {reason['emoji']} {reason['label']} - {reason['description']}"
        data["owner_id"] = interaction.user.id
        data["log_channel_id"] = log_channel_id
        data["is_vip"] = self.is_vip

        reason_descriptions = {
            "buy": "我們的工作人員將協助您完成購買流程。\nOur staff will assist you with the purchase process.",
            "support": "請描述您遇到的技術問題，我們將盡快為您解決。\nPlease describe the technical issue you're experiencing.",
            "other": "請描述您的問題或需求，我們將盡快回覆。\nPlease describe your question or request."
        }

        vip_tag = "⭐ VIP " if self.is_vip else "⭐ "

        ticket_embed = discord.Embed(
            title=f"{vip_tag}Priority Ticket - {reason['label']}",
            description=(
                f"歡迎 {interaction.user.mention}！\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**📋 開單資訊 | Ticket Info:**\n"
                f"• 開單者: {interaction.user.mention}\n"
                f"• 工單原因: **{reason['emoji']} {reason['label']}** - {reason['description']}\n"
                f"• 開單時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{reason_descriptions.get(selected_value, '')}\n\n"
                f"工作人員將在 1 小時內回覆您（VIP 優先）。\n"
                f"Staff will respond within 1 hour (VIP priority)."
            ),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        ticket_embed.set_footer(text=f"工單 ID: {ticket_channel.id}")

        close_view = CloseTicketView()
        await ticket_channel.send(embed=ticket_embed, view=close_view)

        # VIP 工單含設定金額，一般工單不含
        await send_admin_panel(ticket_channel, guild, is_vip_ticket=self.is_vip)

        await interaction.followup.send(
            f"✅ 已為您開單！請前往 {ticket_channel.mention} 查看。",
            ephemeral=True
        )


class TicketReasonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketReasonSelect(is_vip=False))


class VipTicketReasonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketReasonSelect(is_vip=True))


class PriorityTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Priority Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🎫",
        custom_id="priority_ticket_btn"
    )
    async def priority_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        reason_embed = discord.Embed(
            title="⭐ Priority Ticket",
            description="Please select the reason for your ticket:",
            color=discord.Color.gold()
        )
        reason_view = TicketReasonView()
        await interaction.response.send_message(embed=reason_embed, view=reason_view, ephemeral=True)


class VipPriorityTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="VIP Priority Ticket",
        style=discord.ButtonStyle.danger,
        emoji="👑",
        custom_id="vip_priority_ticket_btn"
    )
    async def vip_priority_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_vip_buyer(interaction.user):
            await interaction.response.send_message(
                "❌ 此功能僅限 **VIP Buyer** 身分組使用。\n"
                "This feature is only available for **VIP Buyer** members.",
                ephemeral=True
            )
            return

        reason_embed = discord.Embed(
            title="👑 VIP Priority Ticket",
            description="Please select the reason for your VIP ticket:",
            color=discord.Color.gold()
        )
        reason_view = VipTicketReasonView()
        await interaction.response.send_message(embed=reason_embed, view=reason_view, ephemeral=True)


# ============================================================
# Bot 事件
# ============================================================

@bot.event
async def on_ready():
    print(f"✅ Bot 已上線: {bot.user} (ID: {bot.user.id})")
    print(f"📊 伺服器數量: {len(bot.guilds)}")

    # 載入餘額資料
    load_balance_data()

    bot.add_view(ProductSelectView())
    bot.add_view(PriorityTicketView())
    bot.add_view(VipPriorityTicketView())
    bot.add_view(TicketReasonView())
    bot.add_view(VipTicketReasonView())
    bot.add_view(CloseTicketView())
    bot.add_view(ClaimTicketView())
    bot.add_view(AdminTicketView())

    try:
        # 全域同步
        global_synced = await bot.tree.sync()
        print(f"🔄 已全域同步 {len(global_synced)} 個斜線命令")
        # 對每個伺服器也同步一次，確保命令立即出現
        for guild in bot.guilds:
            try:
                guild_synced = await bot.tree.sync(guild=guild)
                print(f"🔄 已同步 {len(guild_synced)} 個命令到伺服器: {guild.name}")
            except Exception as ge:
                print(f"⚠️ 同步到 {guild.name} 失敗: {ge}")
    except Exception as e:
        print(f"❌ 同步命令失敗: {e}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Bot 已準備就緒！")


# ============================================================
# 處理持久化按鈕交互（備用處理器）
# ============================================================

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")

    if custom_id == "payout_btn":
        if not is_boss(interaction.user):
            await interaction.response.send_message("❌ 僅老闆身分組可進行撥款操作。", ephemeral=True)
            return
        msg = interaction.message
        channel_name = "未知"
        claimed_by_name = "未知"
        claimed_by_id = 0
        price = "未設定"
        if msg.embeds:
            emb = msg.embeds[0]
            for field in emb.fields:
                if "負責人" in field.name:
                    claimed_by_name = field.value
                    # 嘗試從負責人名稱中解析用戶 ID
                    import re
                    id_match = re.search(r'<@!?(\d+)>', field.value)
                    if id_match:
                        claimed_by_id = int(id_match.group(1))
                    else:
                        # 嘗試用名稱在伺服器中查找用戶
                        clean_name = field.value.strip()
                        if interaction.guild:
                            for member in interaction.guild.members:
                                if str(member) == clean_name or member.display_name == clean_name or member.name == clean_name:
                                    claimed_by_id = member.id
                                    break
                elif "金額" in field.name:
                    price = field.value.replace("**", "")
                elif "頻道" in field.name:
                    channel_name = field.value.replace("`", "")
        modal = PayoutModal(
            claimed_by_name=claimed_by_name,
            claimed_by_id=claimed_by_id,
            price=price,
            channel_name=channel_name
        )
        await interaction.response.send_modal(modal)
        return

    if custom_id == "mark_settled_btn":
        if not is_boss(interaction.user):
            await interaction.response.send_message("❌ 僅老闆身分組可進行此操作。", ephemeral=True)
            return
        msg = interaction.message
        channel_name = "未知"
        ticket_owner_name = "未知"
        claimed_by_name = "未知"
        price = "未設定"
        if msg.embeds:
            emb = msg.embeds[0]
            for field in emb.fields:
                if "客戶" in field.name:
                    ticket_owner_name = field.value
                elif "負責人" in field.name:
                    claimed_by_name = field.value
                elif "金額" in field.name:
                    price = field.value.replace("**", "")
                elif "頻道" in field.name:
                    channel_name = field.value.replace("`", "")

        view = discord.ui.View(timeout=None)
        for item in msg.components:
            for child in item.children:
                btn = discord.ui.Button(
                    label=child.label,
                    style=child.style,
                    custom_id=child.custom_id,
                    disabled=True
                )
                view.add_item(btn)

        settled_embed = discord.Embed(
            title="💼 代理結算單 | Agent Settlement",
            description=(
                f"✅ **已結算** - 由 {interaction.user.mention} 標記\n\n"
                f"**工單:** `{channel_name}`\n"
                f"**客戶:** {ticket_owner_name}\n"
                f"**負責人:** {claimed_by_name}\n"
                f"**金額:** {price}\n"
                f"**結算時間:** <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=settled_embed, view=view)
        return


# ============================================================
# 斜線命令：設置面板
# ============================================================

# ============================================================
# 【如何修改介紹文字】
# 修改下方 setup_product 函數中 embed 的 title 和 description
# title = 面板標題（如 "🛒 Product Catalog"）
# description = 面板內容（支持 Markdown 格式）
# footer = 底部文字（如 "RobloxCheatz | Premium Gaming Tools"）
# ============================================================

@bot.tree.command(name="setup-product", description="設置商品目錄面板 | Setup Product Catalog Panel")
@app_commands.default_permissions(administrator=True)
async def setup_product(interaction: discord.Interaction):
    if interaction.channel_id != PRODUCT_PANEL_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ 請在 <#{PRODUCT_PANEL_CHANNEL_ID}> 頻道使用此命令。",
            ephemeral=True
        )
        return

    # ====== 修改這裡的文字來更改面板介紹 ======
    embed = discord.Embed(
        title="🛒 Product Catalog",
        description=(
            "**Welcome to RobloxCheatz Store!**\n\n"
            "Browse our premium Roblox tools and exploits.\n"
            "Select a product from the dropdown menu below\n"
            "to view detailed pricing and payment options.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**💳 Accepted Payment Methods:**\n"
            "• 💳 Card, 🪙 Crypto, CashApp, WeChat\n"
            "• 🍎 Apple Pay, **G** Google Pay\n"
            "• 🏦 Bank Transfers, SEPA, AliPay\n"
            "• 🟡 Binance Pay, 🎮 Robux, 🇷🇺 Funpay\n\n"
            "🌐 **INSTANT DELIVERY** on website orders!"
        ),
        color=discord.Color.purple()
    )
    embed.set_footer(text="RobloxCheatz | Premium Gaming Tools")
    # ====== 修改結束 ======

    view = ProductSelectView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ 商品目錄面板已設置！", ephemeral=True)


@bot.tree.command(name="setup-support", description="設置客服工單面板 | Setup Support Ticket Panel")
@app_commands.default_permissions(administrator=True)
async def setup_support(interaction: discord.Interaction):
    if interaction.channel_id != SUPPORT_PANEL_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ 請在 <#{SUPPORT_PANEL_CHANNEL_ID}> 頻道使用此命令。",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="👑 VIP Priority Support",
        description=(
            "**Thank you for your purchases!**\n\n"
            "As a VIP customer ($60+) you get:\n\n"
            "• 🕐 Priority response time (up to 1 hour)\n"
            "• 💲 Exclusive discounts\n"
            "• 👤 VIP chat access\n"
            "• 🎧 Direct admin support\n\n"
            "➡️ Create a priority ticket for fast assistance:"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="RobloxCheatz | VIP Support")

    view = PriorityTicketView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ 客服工單面板已設置！", ephemeral=True)


@bot.tree.command(name="setup-vip", description="設置 VIP 專屬工單面板 | Setup VIP Ticket Panel")
@app_commands.default_permissions(administrator=True)
async def setup_vip(interaction: discord.Interaction):
    if interaction.channel_id != VIP_PANEL_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ 請在 <#{VIP_PANEL_CHANNEL_ID}> 頻道使用此命令。",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="👑 VIP Buyer Exclusive Support",
        description=(
            "**歡迎 VIP Buyer！**\n\n"
            "作為 VIP Buyer，您享有以下專屬權益：\n\n"
            "• 👑 最高優先回覆\n"
            "• 💲 獨家折扣\n"
            "• 🎧 直接管理員支援\n"
            "• ⚡ 即時處理\n\n"
            "➡️ 點擊下方按鈕建立 VIP 專屬工單："
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="此頻道僅 VIP Buyer 身分組可見")

    view = VipPriorityTicketView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ VIP 工單面板已設置！", ephemeral=True)


# ============================================================
# 管理命令
# ============================================================

@bot.tree.command(name="add-product", description="新增商品到目錄 | Add a product to catalog")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    name="商品名稱",
    emoji="商品 Emoji（如 🔷）",
    description="價格描述（如 3.99$/week | 9.99$/month）",
    details="商品詳細說明"
)
async def add_product(interaction: discord.Interaction, name: str, emoji: str, description: str, details: str):
    prices = {}
    for item in description.split("|"):
        item = item.strip()
        if "/" in item:
            parts = item.split("/")
            price = parts[0].strip()
            period = parts[1].strip()
            prices[period] = price

    new_product = {
        "name": name,
        "emoji": "",
        "display_emoji": emoji,
        "description": description,
        "prices": prices,
        "details": details
    }
    PRODUCTS.append(new_product)

    embed = discord.Embed(
        title="✅ 商品已新增",
        description=f"**{emoji} {name}**\n{description}\n\n{details}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remove-product", description="移除商品 | Remove a product from catalog")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(name="要移除的商品名稱")
async def remove_product(interaction: discord.Interaction, name: str):
    global PRODUCTS
    original_len = len(PRODUCTS)
    PRODUCTS = [p for p in PRODUCTS if p["name"].lower() != name.lower()]

    if len(PRODUCTS) < original_len:
        await interaction.response.send_message(f"✅ 已移除商品: **{name}**", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ 找不到商品: **{name}**", ephemeral=True)


@bot.tree.command(name="list-products", description="列出所有商品 | List all products")
@app_commands.default_permissions(administrator=True)
async def list_products(interaction: discord.Interaction):
    if not PRODUCTS:
        await interaction.response.send_message("📦 目前沒有商品。", ephemeral=True)
        return

    embed = discord.Embed(title="📦 商品列表 | Product List", color=discord.Color.blue())
    for i, product in enumerate(PRODUCTS, 1):
        embed.add_field(
            name=f"{product['display_emoji']} {product['name']}",
            value=f"{product['description']}\n{product['details']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set-price", description="設定當前工單金額（僅管理員）| Set ticket price")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(price="訂單金額（如 5000台幣）")
async def set_price_cmd(interaction: discord.Interaction, price: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ 僅管理員可使用此命令。", ephemeral=True)
        return

    channel = interaction.channel
    if not channel.topic or ("工單" not in channel.topic):
        await interaction.response.send_message("❌ 請在工單頻道中使用此命令。", ephemeral=True)
        return

    data = get_ticket_data(channel.id)
    data["price"] = price

    price_embed = discord.Embed(
        title="💰 訂單金額已設定 | Price Set",
        description=(
            f"**金額: {price}**\n\n"
            f"設定者: {interaction.user.mention}\n"
            f"時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=price_embed)


# ============================================================
# 餘額查詢命令
# ============================================================

@bot.tree.command(name="balance", description="查看自己的餘額 | Check your balance")
async def check_balance(interaction: discord.Interaction):
    """查看自己的餘額（僅在餘額頻道可用，僅操作者本人可見）"""
    if BALANCE_CHANNEL_ID > 0 and interaction.channel_id != BALANCE_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ 請在 <#{BALANCE_CHANNEL_ID}> 頻道使用此命令。",
            ephemeral=True
        )
        return

    if not is_admin(interaction.user) and not is_boss(interaction.user):
        await interaction.response.send_message("❌ 僅管理員和老闆可使用此命令。", ephemeral=True)
        return

    user_id = interaction.user.id
    user_balance = balance_data.get(user_id, 0.0)

    balance_embed = discord.Embed(
        title="💰 餘額查詢 | Balance Check",
        description=(
            f"**用戶:** {interaction.user.mention}\n"
            f"**當前餘額:** {user_balance:.2f}\n\n"
            f"查詢時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=balance_embed, ephemeral=True)


@bot.tree.command(name="balance-check", description="查看指定用戶或所有人餘額（僅老闆）| Check user balance")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="要查詢餘額的用戶（不填則查看所有人）")
async def check_user_balance(interaction: discord.Interaction, user: discord.Member = None):
    if BALANCE_CHANNEL_ID > 0 and interaction.channel_id != BALANCE_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ 請在 <#{BALANCE_CHANNEL_ID}> 頻道使用此命令。",
            ephemeral=True
        )
        return

    if not is_boss(interaction.user):
        await interaction.response.send_message("❌ 僅老闆身分組可查看他人餘額。", ephemeral=True)
        return

    if user:
        user_balance = balance_data.get(user.id, 0.0)
        balance_embed = discord.Embed(
            title="💰 用戶餘額查詢 | User Balance",
            description=(
                f"**用戶:** {user.mention} ({user})\n"
                f"**當前餘額:** {user_balance:.2f}\n\n"
                f"查詢者: {interaction.user.mention}\n"
                f"查詢時間: <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=balance_embed, ephemeral=True)
    else:
        if not balance_data:
            await interaction.response.send_message("📊 目前沒有任何餘額記錄。", ephemeral=True)
            return

        balance_embed = discord.Embed(
            title="💰 所有用戶餘額 | All Balances",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )

        for uid, bal in balance_data.items():
            member = interaction.guild.get_member(uid)
            name = str(member) if member else f"用戶 ID: {uid}"
            balance_embed.add_field(
                name=name,
                value=f"💰 {bal:.2f}",
                inline=True
            )

        balance_embed.set_footer(text=f"查詢者: {interaction.user}")
        await interaction.response.send_message(embed=balance_embed, ephemeral=True)


@bot.tree.command(name="set-balance", description="設定用戶餘額（僅老闆）| Set user balance")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="目標用戶", amount="餘額金額")
async def set_balance(interaction: discord.Interaction, user: discord.Member, amount: float):
    if not is_boss(interaction.user):
        await interaction.response.send_message("❌ 僅老闆身分組可設定餘額。", ephemeral=True)
        return

    balance_data[user.id] = amount
    save_balance_data()

    embed = discord.Embed(
        title="✅ 餘額已設定 | Balance Updated",
        description=(
            f"**用戶:** {user.mention}\n"
            f"**新餘額:** {amount:.2f}\n"
            f"**設定者:** {interaction.user.mention}\n"
            f"**時間:** <t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>"
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setup-balance-channel", description="設定當前頻道為餘額查詢頻道 | Set balance channel")
@app_commands.default_permissions(administrator=True)
async def setup_balance_channel(interaction: discord.Interaction):
    global BALANCE_CHANNEL_ID
    BALANCE_CHANNEL_ID = interaction.channel_id

    guild = interaction.guild
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    boss_role = guild.get_role(BOSS_ROLE_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    if boss_role:
        overwrites[boss_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    await interaction.channel.edit(overwrites=overwrites)

    await interaction.response.send_message(
        f"✅ 已將此頻道設定為餘額查詢頻道！\n"
        f"• 頻道: {interaction.channel.mention}\n"
        f"• 僅管理員和老闆可見此頻道\n"
        f"• 使用 `/balance` 查看自己的餘額\n"
        f"• 老闆使用 `/balance-check` 查看所有人餘額\n"
        f"• 老闆使用 `/set-balance` 設定用戶餘額",
        ephemeral=True
    )


# ============================================================
# VIP 頻道權限設置
# ============================================================

@bot.tree.command(name="setup-vip-permissions", description="設置 VIP 頻道權限（僅 vip-buyer 可見）")
@app_commands.default_permissions(administrator=True)
async def setup_vip_permissions(interaction: discord.Interaction):
    guild = interaction.guild
    vip_role = guild.get_role(VIP_BUYER_ROLE_ID)
    admin_role = guild.get_role(ADMIN_ROLE_ID)

    if not vip_role:
        await interaction.response.send_message("❌ 找不到 VIP Buyer 身分組。", ephemeral=True)
        return

    vip_panel = guild.get_channel(VIP_PANEL_CHANNEL_ID)
    if vip_panel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            vip_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await vip_panel.edit(overwrites=overwrites)

    vip_log = guild.get_channel(VIP_LOG_CHANNEL_ID)
    if vip_log:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await vip_log.edit(overwrites=overwrites)

    vip_category = guild.get_channel(VIP_CATEGORY_ID)
    if vip_category:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            vip_role: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await vip_category.edit(overwrites=overwrites)

    await interaction.response.send_message(
        "✅ VIP 頻道權限已設置！\n"
        f"• VIP 面板頻道: 僅 {vip_role.mention} 和管理員可見\n"
        f"• VIP 結單頻道: 僅管理員可見\n"
        f"• VIP 類別: 僅 {vip_role.mention} 和管理員可見",
        ephemeral=True
    )


# ============================================================
# 管理員命令：重啟 / 同步 / 重整
# ============================================================

@bot.tree.command(name="restart", description="🔄 重啟機器人（僅管理員）")
async def restart_bot(interaction: discord.Interaction):
    """重啟機器人進程，讓 Railway 自動重新啟動載入最新代碼"""
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    boss_role = interaction.guild.get_role(BOSS_ROLE_ID)
    has_permission = (
        (admin_role and admin_role in interaction.user.roles) or
        (boss_role and boss_role in interaction.user.roles) or
        interaction.user.guild_permissions.administrator
    )
    if not has_permission:
        await interaction.response.send_message("❌ 僅管理員或老闆可使用此命令。", ephemeral=True)
        return

    await interaction.response.send_message(
        "🔄 **機器人正在重啟中...**\n"
        "Railway 將自動重新啟動機器人進程，請稍候約 10-30 秒。",
        ephemeral=True
    )
    # 給一點時間讓訊息發送出去
    await asyncio.sleep(2)
    # 退出進程，Railway 會自動重啟
    os._exit(0)


@bot.tree.command(name="sync", description="🔄 同步斜線命令（僅管理員）")
async def sync_commands(interaction: discord.Interaction):
    """重新同步所有斜線命令到 Discord，讓新命令立即可用"""
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    boss_role = interaction.guild.get_role(BOSS_ROLE_ID)
    has_permission = (
        (admin_role and admin_role in interaction.user.roles) or
        (boss_role and boss_role in interaction.user.roles) or
        interaction.user.guild_permissions.administrator
    )
    if not has_permission:
        await interaction.response.send_message("❌ 僅管理員或老闆可使用此命令。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        # 同步到當前伺服器
        synced = await bot.tree.sync(guild=interaction.guild)
        # 同步全域命令
        global_synced = await bot.tree.sync()
        await interaction.followup.send(
            f"✅ **斜線命令同步完成！**\n"
            f"• 伺服器命令: {len(synced)} 個\n"
            f"• 全域命令: {len(global_synced)} 個\n"
            f"新命令現在應該已經可以使用了。",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ 同步失敗: {e}", ephemeral=True)


@bot.tree.command(name="refresh", description="🔄 重整機器人狀態（僅管理員）")
async def refresh_bot(interaction: discord.Interaction):
    """重新載入持久化 View 和同步命令，不需要重啟"""
    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
    boss_role = interaction.guild.get_role(BOSS_ROLE_ID)
    has_permission = (
        (admin_role and admin_role in interaction.user.roles) or
        (boss_role and boss_role in interaction.user.roles) or
        interaction.user.guild_permissions.administrator
    )
    if not has_permission:
        await interaction.response.send_message("❌ 僅管理員或老闆可使用此命令。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        # 重新註冊持久化 View
        bot.add_view(ProductSelectView())
        bot.add_view(PriorityTicketView())
        bot.add_view(VipPriorityTicketView())
        bot.add_view(TicketReasonView())
        bot.add_view(VipTicketReasonView())
        bot.add_view(CloseTicketView())
        bot.add_view(ClaimTicketView())
        bot.add_view(AdminTicketView())

        # 同步命令
        synced = await bot.tree.sync(guild=interaction.guild)
        global_synced = await bot.tree.sync()

        await interaction.followup.send(
            f"✅ **機器人狀態已重整！**\n"
            f"• 持久化 View 已重新載入\n"
            f"• 伺服器命令: {len(synced)} 個已同步\n"
            f"• 全域命令: {len(global_synced)} 個已同步\n"
            f"所有功能現在應該已經正常運作。",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ 重整失敗: {e}", ephemeral=True)


# ============================================================
# 啟動 Bot
# ============================================================

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ 請設置 DISCORD_TOKEN 環境變數！")
        print("在 .env 文件中設置: DISCORD_TOKEN=your_token_here")
        print("或設置環境變數: export DISCORD_TOKEN=your_token_here")
    else:
        bot.run(TOKEN)
