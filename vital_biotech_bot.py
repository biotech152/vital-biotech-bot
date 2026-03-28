"""
Vital Biotech – Telegram Order Bot (Private DM Mode)
=====================================================
Products: Retatrutide, BPC-157, GHK-CU, MT2, TB500, CJC-1295, Ipamorelin, HGH, Semax
Stock: Auto-decrements on confirmed orders. Admin restocks via /restock command.
Orders: Only confirmed when customer sends the full structured format.
"""

import logging
import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ─── CONFIG ───────────────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8655751882:AAF2OKfYbd1EMqLndCEZADTk8rzciWIEaoo"
ADMIN_ID  = 7948357828

STOCK_FILE = "stock.json"

# ─── PRODUCT CATALOGUE (9 active products) ──────────────────────────────────────────────
PRODUCTS = {
    "retatrutide":         {"name": "Retatrutide", "size": "10mg Vial",  "price": "$200", "emoji": "U0001f534", "use": "Fat loss, appetite control, lean muscle preservation"},
    "bpc-157":             {"name": "BPC-157",      "size": "10mg Vial",  "price": "$90",  "emoji": "U0001f535", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "bpc157":              {"name": "BPC-157",      "size": "10mg Vial",  "price": "$90",  "emoji": "U0001f535", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "bpc 157":             {"name": "BPC-157",      "size": "10mg Vial",  "price": "$90",  "emoji": "U0001f535", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "ghk-cu":              {"name": "GHK-CU",       "size": "100mg Vial", "price": "$80",  "emoji": "U0001f7e0", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "ghk cu":              {"name": "GHK-CU",       "size": "100mg Vial", "price": "$80",  "emoji": "U0001f7e0", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "ghkcu":               {"name": "GHK-CU",       "size": "100mg Vial", "price": "$80",  "emoji": "U0001f7e0", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "mt2":                 {"name": "MT2",           "size": "10mg Vial",  "price": "$60",  "emoji": "U0001f7e1", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "mt-2":                {"name": "MT2",           "size": "10mg Vial",  "price": "$60",  "emoji": "U0001f7e1", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "melanotan":           {"name": "MT2",           "size": "10mg Vial",  "price": "$60",  "emoji": "U0001f7e1", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "melanotan 2":         {"name": "MT2",           "size": "10mg Vial",  "price": "$60",  "emoji": "U0001f7e1", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "tb500":               {"name": "TB500",         "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "tb-500":              {"name": "TB500",         "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "tb 500":              {"name": "TB500",         "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "cjc-1295":            {"name": "CJC-1295",      "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "cjc1295":             {"name": "CJC-1295",      "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "cjc 1295":            {"name": "CJC-1295",      "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e2", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "ipamorelin":          {"name": "Ipamorelin",    "size": "10mg Vial",  "price": "$100", "emoji": "U0001f7e3", "use": "Natural GH release, recovery, sleep, body composition"},
    "hgh":                 {"name": "HGH",           "size": "150 IU Vial","price": "$250", "emoji": "U0001f535", "use": "Lean muscle, fat loss, sleep & recovery, energy, anti-aging"},
    "human growth hormone":{"name": "HGH",           "size": "150 IU Vial","price": "$250", "emoji": "U0001f535", "use": "Lean muscle, fat loss, sleep & recovery, energy, anti-aging"},
    "semax":               {"name": "Semax",         "size": "10mg Vial",  "price": "$100", "emoji": "U0001f535", "use": "Focus, mental clarity, memory, cognitive performance"},
}

CANONICAL_PRODUCTS = [
    "Retatrutide", "BPC-157", "GHK-CU", "MT2", "TB500",
    "CJC-1295", "Ipamorelin", "HGH", "Semax"
]

ALIAS_TO_CANONICAL = {
    "retatrutide": "Retatrutide",
    "bpc-157": "BPC-157", "bpc157": "BPC-157", "bpc 157": "BPC-157",
    "ghk-cu": "GHK-CU", "ghk cu": "GHK-CU", "ghkcu": "GHK-CU",
    "mt2": "MT2", "mt-2": "MT2", "melanotan": "MT2", "melanotan 2": "MT2",
    "tb500": "TB500", "tb-500": "TB500", "tb 500": "TB500",
    "cjc-1295": "CJC-1295", "cjc1295": "CJC-1295", "cjc 1295": "CJC-1295",
    "ipamorelin": "Ipamorelin",
    "hgh": "HGH", "human growth hormone": "HGH",
    "semax": "Semax",
}

# ─── STOCK MANAGEMENT ─────────────────────────────────────────────────────────────────────────────
def load_stock() -> dict:
    if os.path.exists(STOCK_FILE):
        try:
            with open(STOCK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {p: 0 for p in CANONICAL_PRODUCTS}

def save_stock(stock: dict):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock, f)

stock = load_stock()

def get_stock(name: str) -> int:
    return stock.get(name, 0)

def decrement_stock(name: str, qty: int) -> bool:
    if stock.get(name, 0) >= qty:
        stock[name] -= qty
        save_stock(stock)
        return True
    return False

# ─── MESSAGES ───────────────────────────────────────────────────────────────────────────────────
PRICELIST = """U0001f6a8 *VITAL BIOTECH — PRODUCTS & PRICING* U0001f6a8

U0001f534 Retatrutide (10mg Vial) — $200
U0001f535 BPC-157 (10mg Vial) — $90
U0001f7e0 GHK-CU (100mg Vial) — $80
U0001f7e1 MT2 / Melanotan 2 (10mg Vial) — $60
U0001f7e2 TB500 (10mg Vial) — $100
U0001f7e2 CJC-1295 (10mg Vial) — $100
U0001f7e3 Ipamorelin (10mg Vial) — $100
U0001f535 HGH (150 IU Vial) — $250
U0001f535 Semax (10mg Vial) — $100

To place an order tap U0001f4e6 *Place an Order* below U0001f447"""

WELCOME_MESSAGE = """U0001f44b Welcome to *Vital Biotech*!
Australia's premium peptide service U0001f1e6U0001f1fa

Here you can:
U0001f4b0 Check product prices
U0001f4e6 Place an order
U0001f489 Get dosing & usage info
U0001f69a Ask about shipping

Use the buttons below to get started, or just type your question!"""

ORDER_INSTRUCTIONS = """U0001f4e6 *How to Place an Order*

To place your order, send a message in *exactly* this format:

━━━━━━━━━━━━━━━━━━━━━━
NAME: Your Full Name
ADDRESS: Your Full Delivery Address
PRODUCT AND AMOUNT: e.g. BPC-157 x2, HGH x1
TOTAL ORDER COST: $000
━━━━━━━━━━━━━━━━━━━━━━

U0001f4cc *Example:*
NAME: John Smith
ADDRESS: 12 Example St, Sydney NSW 2000
PRODUCT AND AMOUNT: BPC-157 x2, Semax x1
TOTAL ORDER COST: $280

Send that through and we will take care of the rest! U0001f4aa"""

SHIPPING_INFO = """U0001f69a *Shipping & Delivery*

U0001f4cd We ship *Australia-wide* U0001f1e6U0001f1fa
⏱ Delivery: *2–3 business days* once dispatched
U0001f4e6 Orders go out fast!

Once your order is confirmed, you will receive tracking details."""

RECONST_INFO = """U0001f489 *How to Use Your Peptides*

U0001f4ce *Reconstitution (mixing):*
• Add *1ml of BAC Water* to your peptide vial
• Gently swirl (don't shake)
• Store in the fridge once mixed

U0001f489 *Administration:*
• Use 1ml insulin needles
• Inject subcutaneously (into fat, e.g. stomach area)
• Dosing varies by peptide — ask us for specific guidance!

❓ Got a specific question? Just ask!"""

# ─── LOGGING ──────────────────────────────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── HELPERS ──────────────────────────────────────────────────────────────────────────────────
def match_product(text: str):
    t = text.lower()
    for kw, prod in PRODUCTS.items():
        if kw in t:
            return prod
    return None

def get_canonical(text: str):
    t = text.lower()
    for kw, canon in ALIAS_TO_CANONICAL.items():
        if kw in t:
            return canon
    return None

def contains(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)

def is_structured_order(text: str) -> bool:
    t = text.lower()
    has_name    = "name:" in t
    has_address = "address:" in t
    has_product = ("product" in t and "amount" in t) or "product and amount" in t
    has_total   = "total" in t or ("cost" in t and "$" in t)
    return has_name and has_address and has_product and has_total

def parse_order_items(text: str) -> list:
    results = {}
    for kw, canon in ALIAS_TO_CANONICAL.items():
        p1 = rf"{re.escape(kw)}\s*[xX×]\s*(\d+)"
        p2 = rf"(\d+)\s*[xX×]\s*{re.escape(kw)}"
        m = re.search(p1, text, re.IGNORECASE) or re.search(p2, text, re.IGNORECASE)
        if m and canon not in results:
            results[canon] = int(m.group(1))
    return list(results.items())

def find_canonical_from_arg(arg: str):
    al = arg.lower()
    for kw, canon in ALIAS_TO_CANONICAL.items():
        if kw in al:
            return canon
    for c in CANONICAL_PRODUCTS:
        if c.lower() in al:
            return c
    return None

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("U0001f4b0 Full Pricelist", callback_data="pricelist")],
        [InlineKeyboardButton("U0001f4e6 Place an Order", callback_data="order"),
         InlineKeyboardButton("U0001f69a Shipping Info",  callback_data="shipping")],
        [InlineKeyboardButton("U0001f489 How to Use Peptides", callback_data="howto")],
    ])

# ─── ADMIN COMMANDS ───────────────────────────────────────────────────────────────────────────────
async def restock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /restock <product> <quantity>\nExample: /restock BPC-157 50")
        return
    qty_str     = context.args[-1]
    product_str = " ".join(context.args[:-1])
    if not qty_str.isdigit():
        await update.message.reply_text("Quantity must be a whole number.")
        return
    qty   = int(qty_str)
    canon = find_canonical_from_arg(product_str)
    if not canon:
        await update.message.reply_text(
            f"Product not recognised: '{product_str}'\n\nValid products:\n" +
            "\n".join(f"- {p}" for p in CANONICAL_PRODUCTS)
        )
        return
    stock[canon] = stock.get(canon, 0) + qty
    save_stock(stock)
    await update.message.reply_text(
        f"Stock updated! {canon}: {stock[canon]} units now in stock",
    )

async def checkstock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lines = ["U0001f4e6 Current Stock Levels\n"]
    for p in CANONICAL_PRODUCTS:
        qty    = stock.get(p, 0)
        status = f"✅ {qty} units" if qty > 0 else "❌ OUT OF STOCK"
        lines.append(f"- {p}: {status}")
    lines.append("\nUse /restock <product> <qty> to add stock.")
    lines.append("Use /soldout <product> to manually zero a product.")
    await update.message.reply_text("\n".join(lines))

async def soldout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /soldout <product>")
        return
    canon = find_canonical_from_arg(" ".join(context.args))
    if not canon:
        await update.message.reply_text(f"Product not recognised: '{' '.join(context.args)}'")
        return
    stock[canon] = 0
    save_stock(stock)
    await update.message.reply_text(f"{canon} marked as OUT OF STOCK.")

# ─── STANDARD COMMAND HANDLERS ────────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def pricelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PRICELIST, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ORDER_INSTRUCTIONS, parse_mode="Markdown")

# ─── BUTTON HANDLER ──────────────────────────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "pricelist":
        await query.message.reply_text(PRICELIST, parse_mode="Markdown")
    elif query.data == "order":
        await query.message.reply_text(ORDER_INSTRUCTIONS, parse_mode="Markdown")
    elif query.data == "shipping":
        await query.message.reply_text(SHIPPING_INFO, parse_mode="Markdown")
    elif query.data == "howto":
        await query.message.reply_text(RECONST_INFO, parse_mode="Markdown")

# ─── MESSAGE HANDLER ─────────────────────────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    text = msg.text
    user = msg.from_user
    if msg.chat.type != "private":
        return

    product = match_product(text)

    # 1. Pricelist request
    if contains(text, ["pricelist", "price list", "full list", "all products",
                       "what do you have", "what do you sell", "full price",
                       "all prices", "what products"]):
        await msg.reply_text(PRICELIST, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # 2. Structured order (all 4 fields present) - the ONLY path that confirms an order
    elif is_structured_order(text):
        order_items  = parse_order_items(text)
        out_of_stock = []
        for canon, qty in order_items:
            if get_stock(canon) < qty:
                avail = get_stock(canon)
                out_of_stock.append(f"{canon} (requested {qty}, only {avail} available)")
        if out_of_stock:
            await msg.reply_text(
                "⚠️ *Some items in your order are out of stock:*\n\n" +
                "\n".join(f"❌ {item}" for item in out_of_stock) +
                "\n\nPlease adjust your order or check back soon!",
                parse_mode="Markdown"
            )
            return
        for canon, qty in order_items:
            decrement_stock(canon, qty)
        user_tag   = f"@{user.username}" if user.username else f"ID: {user.id}"
        admin_note = (
            f"U0001f6d2 *NEW ORDER!*\n\n"
            f"U0001f464 {user.full_name} ({user_tag})\n\n"
            f"U0001f4cb *Order details:*\n{text}"
        )
        if order_items:
            admin_note += "\n\nU0001f4e6 *Stock auto-decremented:*"
            for canon, qty in order_items:
                admin_note += f"\n- {canon}: -{qty} (now {stock.get(canon, 0)} remaining)"
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_note, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Could not notify admin of order: {e}")
        await msg.reply_text(
            "✅ *Thank you for your order!*\n\n"
            "We will send you through payment information shortly U0001f4b3\n\n"
            "We ship Australia-wide in 2–3 business days U0001f1e6U0001f1faU0001f4e6",
            parse_mode="Markdown"
        )

    # 3. Order intent but no structured format yet - show instructions only
    elif contains(text, ["order", "buy", "purchase", "i want", "i'd like",
                         "can i get", "get some", "want some", "interested in buying",
                         "how do i order", "how to order", "place an order"]):
        if product:
            canon = get_canonical(text)
            if canon and get_stock(canon) == 0:
                await msg.reply_text(
                    f"⚠️ *{product['name']} is currently out of stock.*\n\n"
                    f"We'll have more arriving soon! Check back or ask about our other products.",
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard()
                )
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"ℹ️ Customer asked about *{canon}* but it's out of stock.\n"
                             f"U0001f464 {user.full_name} ({f'@{user.username}' if user.username else user.id})",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Could not notify admin: {e}")
                return
        await msg.reply_text(ORDER_INSTRUCTIONS, parse_mode="Markdown")

    # 4. Specific product price enquiry
    elif product and contains(text, ["price", "cost", "how much", "$", "pricing"]):
        canon = get_canonical(text)
        qty   = get_stock(canon) if canon else 0
        stock_line = f"\nU0001f4e6 Availability: {'✅ In stock' if qty > 0 else '❌ Currently out of stock'}"
        await msg.reply_text(
            f"{product['emoji']} *{product['name']}*\n"
            f"U0001f4e6 Size: {product['size']}\n"
            f"U0001f4b5 Price: {product['price']}\n"
            f"U0001f4cb {product['use']}"
            f"{stock_line}\n\n"
            f"To order, tap U0001f4e6 *Place an Order* below!",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # 5. General price question
    elif contains(text, ["price", "cost", "how much", "pricing"]):
        await msg.reply_text(PRICELIST, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # 6. Shipping
    elif contains(text, ["ship", "deliver", "delivery", "postage", "how long",
                         "arrive", "tracking", "dispatch", "express"]):
        await msg.reply_text(SHIPPING_INFO, parse_mode="Markdown")

    # 7. How to use / dosing
    elif contains(text, ["mix", "reconstitut", "how to inject", "how to use",
                         "dose", "dosing", "inject", "needle", "syringe",
                         "storage", "store", "fridge", "refrigerat", "how to"]):
        await msg.reply_text(RECONST_INFO, parse_mode="Markdown")

    # 8. Product name mentioned
    elif product:
        canon = get_canonical(text)
        qty   = get_stock(canon) if canon else 0
        stock_status = "✅ In stock" if qty > 0 else "❌ Currently out of stock"
        await msg.reply_text(
            f"{product['emoji']} *{product['name']}*\n"
            f"U0001f4e6 {product['size']} — {product['price']}\n"
            f"U0001f4cb {product['use']}\n"
            f"U0001f5c3 Availability: {stock_status}\n\n"
            f"Want to order? Tap U0001f4e6 *Place an Order* below!",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # 9. Unrecognised - forward to admin
    else:
        user_tag = f"@{user.username}" if user.username else f"ID: {user.id}"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ *Unrecognised message — reply needed!*\n\n"
                    f"U0001f464 {user.full_name} ({user_tag})\n"
                    f"U0001f4e9 Message:\n_{text}_"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Could not notify admin: {e}")
        await msg.reply_text(
            "Thanks for your message! U0001f44b\n\n"
            "A member of the team will get back to you shortly.\n\n"
            "In the meantime, here's what I can help with:",
            reply_markup=main_menu_keyboard()
        )

# ─── MAIN ────────────────────────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("restock",    restock_cmd))
    app.add_handler(CommandHandler("checkstock", checkstock_cmd))
    app.add_handler(CommandHandler("soldout",    soldout_cmd))
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("pricelist",  pricelist_cmd))
    app.add_handler(CommandHandler("order",      order_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("✅ Vital Biotech DM bot is live...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
