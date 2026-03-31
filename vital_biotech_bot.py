"""
Vital Biotech – Telegram Order Bot (Private DM Mode)
=====================================================
How it works:
  • The group chat is ANNOUNCEMENT ONLY — only admins can post.
  • A pinned message in the group contains a link: t.me/YOURBOTUSERNAME
  • Customers click the link → opens a private DM with this bot.
  • All ordering, pricing, and product questions happen in the DM.
  • Admin (Arran) gets a private notification for any unrecognised questions.

Requirements:
    pip install python-telegram-bot==20.7

Run:
    python vital_biotech_bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ─── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8655751882:AAF2OKfYbd1EMqLndCEZADTk8rzciWIEaoo"
ADMIN_ID  = 7948357828   # Arran's personal Telegram user ID

# ─── PRODUCT CATALOGUE ─────────────────────────────────────────────────────────
PRODUCTS = {
    "retatrutide":           {"name": "Retatrutide",           "size": "10mg Vial",                              "price": "$200", "emoji": "🔴", "use": "Fat loss, appetite control, lean muscle preservation"},
    "bpc-157":               {"name": "BPC-157",               "size": "10mg Vial",                              "price": "$90",  "emoji": "🔵", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "bpc157":                {"name": "BPC-157",               "size": "10mg Vial",                              "price": "$90",  "emoji": "🔵", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "bpc 157":               {"name": "BPC-157",               "size": "10mg Vial",                              "price": "$90",  "emoji": "🔵", "use": "Joint, tendon & ligament recovery, gut health, healing"},
    "ghk-cu":                {"name": "GHK-CU",                "size": "100mg Vial",                             "price": "$80",  "emoji": "🟠", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "ghk cu":                {"name": "GHK-CU",                "size": "100mg Vial",                             "price": "$80",  "emoji": "🟠", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "ghkcu":                 {"name": "GHK-CU",                "size": "100mg Vial",                             "price": "$80",  "emoji": "🟠", "use": "Skin health, hair quality, collagen production, anti-aging"},
    "melanotan":             {"name": "Melanotan 2",           "size": "10mg Vial",                              "price": "$60",  "emoji": "🟡", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "mt-2":                  {"name": "Melanotan 2",           "size": "10mg Vial",                              "price": "$60",  "emoji": "🟡", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "mt2":                   {"name": "Melanotan 2",           "size": "10mg Vial",                              "price": "$60",  "emoji": "🟡", "use": "Skin pigmentation, deeper & longer-lasting tan"},
    "tb-500":                {"name": "TB-500",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "tb500":                 {"name": "TB-500",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "tb 500":                {"name": "TB-500",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "Recovery, soft-tissue repair, inflammation, joints"},
    "cjc-1295":              {"name": "CJC-1295",              "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "cjc1295":               {"name": "CJC-1295",              "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "cjc 1295":              {"name": "CJC-1295",              "size": "10mg Vial",                              "price": "$100", "emoji": "🟢", "use": "GH support, recovery, sleep quality, muscle & fat-loss"},
    "ipamorelin":            {"name": "Ipamorelin",            "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Natural GH release, recovery, sleep, body composition"},
    "hgh":                   {"name": "HGH",                   "size": "150 IU Vial",                            "price": "$250", "emoji": "🔵", "use": "Lean muscle, fat loss, sleep & recovery, energy, anti-aging"},
    "human growth hormone":  {"name": "HGH",                   "size": "150 IU Vial",                            "price": "$250", "emoji": "🔵", "use": "Lean muscle, fat loss, sleep & recovery, energy, anti-aging"},
    "sermorelin":            {"name": "Sermorelin",            "size": "10mg Vial",                              "price": "$200", "emoji": "🟠", "use": "Natural GH release, sleep, fat-loss, muscle support"},
    "tesamorelin":           {"name": "Tesamorelin",           "size": "10mg Vial",                              "price": "$150", "emoji": "⚫️", "use": "Stubborn fat loss, GH pathways, body recomposition"},
    "igf-1":                 {"name": "IGF-1 LR3",             "size": "1mg Vial",                               "price": "$150", "emoji": "🔵", "use": "Muscle growth, recovery, strength, nutrient uptake"},
    "igf1":                  {"name": "IGF-1 LR3",             "size": "1mg Vial",                               "price": "$150", "emoji": "🔵", "use": "Muscle growth, recovery, strength, nutrient uptake"},
    "igf 1":                 {"name": "IGF-1 LR3",             "size": "1mg Vial",                               "price": "$150", "emoji": "🔵", "use": "Muscle growth, recovery, strength, nutrient uptake"},
    "tirzepatide":           {"name": "Tirzepatide",           "size": "10mg Vial",                              "price": "$150", "emoji": "🔵", "use": "Fat loss, appetite control, blood sugar regulation"},
    "semaglutide":           {"name": "Semaglutide",           "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Fat loss, appetite control, weight management"},
    "ozempic":               {"name": "Semaglutide",           "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Fat loss, appetite control, weight management"},
    "gh stack":              {"name": "GH Stack",              "size": "5mg CJC-1295 + 5mg Ipamorelin",          "price": "$100", "emoji": "🟣", "use": "GH release, recovery, sleep, body composition"},
    "growth hormone stack":  {"name": "GH Stack",              "size": "5mg CJC-1295 + 5mg Ipamorelin",          "price": "$100", "emoji": "🟣", "use": "GH release, recovery, sleep, body composition"},
    "glow stack":            {"name": "GLOW Stack",            "size": "50mg GHK-cU + 10mg BPC157 + 10mg TB500", "price": "$200", "emoji": "🟢", "use": "Skin glow, hair health, tissue repair, recovery"},
    "glow":                  {"name": "GLOW Stack",            "size": "50mg GHK-cU + 10mg BPC157 + 10mg TB500", "price": "$200", "emoji": "🟢", "use": "Skin glow, hair health, tissue repair, recovery"},
    "klow stack":            {"name": "KLOW Stack",            "size": "10mg KPV + 50mg GHK-cU + 10mg BPC157 + 10mg TB500", "price": "$250", "emoji": "🟣", "use": "Enhanced skin, hair, tissue repair & recovery"},
    "klow":                  {"name": "KLOW Stack",            "size": "10mg KPV + 50mg GHK-cU + 10mg BPC157 + 10mg TB500", "price": "$250", "emoji": "🟣", "use": "Enhanced skin, hair, tissue repair & recovery"},
    "wolverine stack":       {"name": "Wolverine Stack",       "size": "5mg BPC157 + 5mg TB500",                 "price": "$100", "emoji": "🟣", "use": "Fast recovery, injury repair, connective tissue support"},
    "wolverine":             {"name": "Wolverine Stack",       "size": "5mg BPC157 + 5mg TB500",                 "price": "$100", "emoji": "🟣", "use": "Fast recovery, injury repair, connective tissue support"},
    "sanitary wipes":        {"name": "Sanitary Wipes",        "size": "10 Pack",                                "price": "$5",   "emoji": "🟢", "use": "Cleaning vial tops, research hygiene prep"},
    "wipes":                 {"name": "Sanitary Wipes",        "size": "10 Pack",                                "price": "$5",   "emoji": "🟢", "use": "Cleaning vial tops, research hygiene prep"},
    "needles":               {"name": "Needles",               "size": "10 Pack (1ml)",                          "price": "$10",  "emoji": "⚪", "use": "Peptide research handling, accurate measurement"},
    "syringes":              {"name": "Needles",               "size": "10 Pack (1ml)",                          "price": "$10",  "emoji": "⚪", "use": "Peptide research handling, accurate measurement"},
    "bac water":             {"name": "BAC Water",             "size": "3ml Vial",                               "price": "$20",  "emoji": "🔵", "use": "Reconstituting peptides, accurate measurement"},
    "bacteriostatic":        {"name": "BAC Water",             "size": "3ml Vial",                               "price": "$20",  "emoji": "🔵", "use": "Reconstituting peptides, accurate measurement"},
    "semax":                 {"name": "Semax",                 "size": "10mg Vial",                              "price": "$100", "emoji": "🔵", "use": "Focus, mental clarity, memory, cognitive performance"},
    "selank":                {"name": "Selank",                "size": "11mg Vial",                              "price": "$100", "emoji": "🟢", "use": "Mood balance, stress reduction, calm focus"},
    "nad+":                  {"name": "NAD+",                  "size": "500mg Vial",                             "price": "$100", "emoji": "🟣", "use": "Energy, cellular health, longevity, anti-aging"},
    "nad":                   {"name": "NAD+",                  "size": "500mg Vial",                             "price": "$100", "emoji": "🟣", "use": "Energy, cellular health, longevity"},
    "mots-c":                {"name": "MOTS-C",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Fat loss, metabolism, energy, insulin sensitivity"},
    "motsc":                 {"name": "MOTS-C",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Fat loss, metabolism, energy, insulin sensitivity"},
    "mots c":                {"name": "MOTS-C",                "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Fat loss, metabolism, energy, insulin sensitivity"},
    "glutathione":           {"name": "Glutathione",           "size": "1500mg Vial",                            "price": "$100", "emoji": "🟠", "use": "Skin brightening, antioxidant, detox, immune support"},
    "epithalon":             {"name": "Epithalon",             "size": "50mg Vial",                              "price": "$100", "emoji": "🔴", "use": "Longevity, cellular repair, sleep quality, telomere health"},
    "hcg":                   {"name": "HCG",                   "size": "10,000 IU Vial",                         "price": "$150", "emoji": "🟢", "use": "Testosterone support, fertility, PCT, hormonal balance"},
    "ss-31":                 {"name": "SS-31",                 "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Mitochondrial health, energy, endurance, recovery, anti-aging"},
    "ss31":                  {"name": "SS-31",                 "size": "10mg Vial",                              "price": "$100", "emoji": "🟣", "use": "Mitochondrial health, energy, endurance, recovery"},
}

# ─── PRICELIST ─────────────────────────────────────────────────────────────────
PRICELIST = """🚨 *VITAL BIOTECH — FULL PRICELIST* 🚨

*💉 PEPTIDES*
🔴 Retatrutide (10mg) — $200
🔵 BPC-157 (10mg) — $90
🟠 GHK-CU (100mg) — $80
🟡 Melanotan 2 / MT-2 (10mg) — $60
🟢 TB-500 (10mg) — $100
🟢 CJC-1295 (10mg) — $100
🟣 Ipamorelin (10mg) — $100
🟠 Sermorelin (10mg) — $200
⚫️ Tesamorelin (10mg) — $150
🔵 IGF-1 LR3 (1mg) — $150
🔵 HGH (150 IU) — $250
🔵 Tirzepatide (10mg) — $150
🟣 Semaglutide (10mg) — $100
🔵 Semax (10mg) — $100
🟢 Selank (11mg) — $100
🟣 NAD+ (500mg) — $100
🟣 MOTS-C (10mg) — $100
🟠 Glutathione (1500mg) — $100
🔴 Epithalon (50mg) — $100
🟢 HCG (10,000 IU) — $150
🟣 SS-31 (10mg) — $100

*📦 STACKS*
🟣 GH Stack (CJC-1295 + Ipamorelin) — $100
🟢 GLOW Stack (GHK-cU + BPC157 + TB500) — $200
🟣 KLOW Stack (KPV + GHK-cU + BPC157 + TB500) — $250
🟣 Wolverine Stack (BPC157 + TB500) — $100

*🧪 ACCESSORIES*
Sanitary Wipes (10 pack) — $5
Needles / Syringes (10 pack) — $10
BAC Water 3ml Vial — $20

To place your order, just tell me what you'd like! 👇"""

WELCOME_MESSAGE = """👋 Welcome to *Vital Biotech*!

Australia's best peptide service 🇦🇺

Here you can:
💰 Check product prices
📦 Place an order
💉 Get dosing & usage info
🚚 Ask about shipping

Use the buttons below to get started, or just type your question!"""

ORDER_INSTRUCTIONS = """📦 *How to Place an Order*

Simply tell me:
1️⃣ *What product(s) you want*
2️⃣ *How many vials*

Example: _"I'd like 2x Retatrutide and 1x BAC Water"_

Once you send your order I'll pass it straight to the team and someone will confirm your details and payment shortly! 💪"""

SHIPPING_INFO = """🚚 *Shipping & Delivery*

📍 We ship *Australia-wide* 🇦🇺
⏱ Delivery: *2–3 business days* once dispatched
📦 Lots of stock available — orders go out fast!

Once your order is confirmed, you'll receive tracking details."""

RECONST_INFO = """💉 *How to Use Your Peptides*

📎 *Reconstitution (mixing):*
• Mix with *BAC Water* — use a peptide calculator to find the right amount depending on your peptide
• Gently swirl (don't shake)
• Store in the fridge once mixed

💉 *Administration:*
• Use 1ml insulin needles
• Inject subcutaneously (into fat, e.g. stomach area)
• Dosing varies by peptide — ask us for specific guidance!

❓ Got a specific question? Just ask!"""

# ─── HELPERS ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def match_product(text: str):
    t = text.lower()
    for kw, prod in PRODUCTS.items():
        if kw in t:
            return prod
    return None

def contains(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Full Pricelist",     callback_data="pricelist")],
        [InlineKeyboardButton("📦 Place an Order",     callback_data="order"),
         InlineKeyboardButton("🚚 Shipping Info",      callback_data="shipping")],
        [InlineKeyboardButton("💉 How to Use Peptides", callback_data="howto")],
    ])

# ─── COMMAND HANDLERS ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def pricelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PRICELIST, parse_mode="Markdown")

async def order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ORDER_INSTRUCTIONS, parse_mode="Markdown")

# ─── BUTTON HANDLER ────────────────────────────────────────────────────────────
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

# ─── MESSAGE HANDLER ───────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text
    user = msg.from_user
    chat_type = msg.chat.type

    # Only handle private DMs
    if chat_type != "private":
        return

    product = match_product(text)

    # ── Forward every message to admin ────────────────────────────────────────
    user_tag = f"@{user.username}" if user.username else f"ID: {user.id}"
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💬 *Incoming Message*\n\n"
                f"👤 {user.full_name} ({user_tag})\n"
                f"📩 _{text}_"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Could not forward message to admin: {e}")

    # ── Pricelist ──────────────────────────────────────────────────────────────
    if contains(text, ["pricelist", "price list", "full list", "all products",
                        "what do you have", "what do you sell", "full price",
                        "all prices", "products"]):
        await msg.reply_text(PRICELIST, parse_mode="Markdown")

    # ── Specific product price ─────────────────────────────────────────────────
    elif product and contains(text, ["price", "cost", "how much", "$", "pricing"]):
        await msg.reply_text(
            f"{product['emoji']} *{product['name']}*\n"
            f"📦 Size: {product['size']}\n"
            f"💵 Price: {product['price']}\n"
            f"📋 {product['use']}\n\n"
            f"Want to order? Just say how many vials you'd like! 👇",
            parse_mode="Markdown"
        )

    # ── General price question ─────────────────────────────────────────────────
    elif contains(text, ["price", "cost", "how much", "pricing", "pricelist"]):
        await msg.reply_text(PRICELIST, parse_mode="Markdown")

    # ── Shipping ───────────────────────────────────────────────────────────────
    elif contains(text, ["ship", "deliver", "delivery", "postage", "how long",
                          "arrive", "tracking", "dispatch", "express", "days"]):
        await msg.reply_text(SHIPPING_INFO, parse_mode="Markdown")

    # ── Howto / dosing ─────────────────────────────────────────────────────────
    elif contains(text, ["mix", "reconstitut", "how to inject", "how to use",
                          "dose", "dosing", "inject", "needle", "syringe",
                          "storage", "store", "fridge", "refrigerat",
                          "how many units", "how many ml", "how to"]):
        await msg.reply_text(RECONST_INFO, parse_mode="Markdown")

    # ── Order intent ───────────────────────────────────────────────────────────
    elif contains(text, ["order", "buy", "purchase", "i want", "i'd like",
                          "can i get", "get some", "want some", "interested"]):
        # Forward order to admin
        order_text = (
            f"🛒 *New Order Request!*\n\n"
            f"👤 From: {user.full_name}"
            + (f" (@{user.username})" if user.username else f" (ID: {user.id})")
            + f"\n\n📩 Message:\n_{text}_"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=order_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Could not notify admin of order: {e}")

        await msg.reply_text(
            "✅ *Order received!*\n\n"
            "The team will be in touch shortly to confirm your order and payment details. "
            "We ship Australia-wide in 2–3 business days 🇦🇺📦\n\n"
            "Any questions in the meantime? Just ask!",
            parse_mode="Markdown"
        )

    # ── Product info (no order/price keyword, just product name) ──────────────
    elif product:
        await msg.reply_text(
            f"{product['emoji']} *{product['name']}*\n"
            f"📦 {product['size']} — {product['price']}\n"
            f"📋 {product['use']}\n\n"
            f"Would you like to order some? Just let me know how many vials! 👇",
            parse_mode="Markdown"
        )

    # ── Unrecognised — notify admin ────────────────────────────────────────────
    else:
        user_tag = f"@{user.username}" if user.username else f"ID: {user.id}"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ *Unrecognised DM — reply needed!*\n\n"
                    f"👤 {user.full_name} ({user_tag})\n"
                    f"📩 Message:\n_{text}_"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Could not notify admin: {e}")

        await msg.reply_text(
            "Thanks for your message! 👋\n\n"
            "A member of the team will get back to you shortly.\n\n"
            "In the meantime, here's what I can help with:",
            reply_markup=main_menu_keyboard()
        )

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("pricelist", pricelist_cmd))
    app.add_handler(CommandHandler("order",     order_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Vital Biotech DM bot is live...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
