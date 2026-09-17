"""
TRX Signal Bot — Telegram (Color Buttons + Kaiyo Strategy)

Features:
- Auto-posts predictions every minute
- Color buttons: PENDING → WIN / LOSE
- Kaiyo Strategy Engine (5 logics)
- Auto-reverse on loss
- Logic switching on loss
- Simple clean messages (no emojis)
- 10 Results Summary with Canvas Image

Run:
    pip install requests telebot pillow
    python trx_bot.py
"""

import os
import time
import requests
import threading
import logging
import sys
from collections import deque
from typing import Optional, Dict, Any, List, Tuple
from io import BytesIO

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont

# ==================================================
# LOGGING SETUP
# ==================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("trx-signal-bot")

# ==================================================
# TELEGRAM CONFIG
# ==================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004326600232").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it in Railway Variables.")

# ==================================================
# API SETUP
# ==================================================
DOMAIN = "draw.ar-lottery01.com"
API_URL = f"https://{DOMAIN}/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json?ts={{}}"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": f"https://{DOMAIN}",
    "Referer": f"https://{DOMAIN}/"
})

# ==================================================
# BOT INSTANCE
# ==================================================
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

# ==================================================
# CUSTOM EMOJI IDs
# ==================================================
# Paste your Telegram Custom Emoji IDs between the quotes.
# Example: PREDICTION_EMOJI_ID = "1234567890123456789"
TOP_EMOJI_IDS = [
    "6203904539075022241",
    "6204116920912842527",
    "6203945598962372140",
    "6203840986443944067",
    "6203736262256364808",
    "6204068731379782085",
    "6203817789325579475",
]

SEPARATOR_EMOJI_ID = "6267119710278522544"
MATCH_EMOJI_ID = "6266950140674708467"
BUY_EMOJI_ID = "6267008582294705964"
RESULT_EMOJI_ID = "6264785189394717307"
JUSTIN_STRATEGY_EMOJI_ID = "6267291337171670780"
SUMMARY_EMOJI_ID = ""

def custom_emoji(emoji: str, emoji_id: str) -> str:
    """Return a Telegram HTML custom-emoji entity when an ID is set."""
    if emoji_id.strip():
        return f'<tg-emoji emoji-id="{emoji_id.strip()}">{emoji}</tg-emoji>'
    return emoji

# ==================================================
# 🎨 COLOR BUTTONS (Telegram Bot API 9.4+)
# ==================================================
def pending_keyboard() -> InlineKeyboardMarkup:
    """PENDING button with BLUE color"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        text="PENDING",
        callback_data="pending",
        style="primary"  # Blue
    ))
    return kb

def result_keyboard(won: bool) -> InlineKeyboardMarkup:
    """WIN or LOSE button"""
    if won:
        text = "WIN"
        style = "success"  # Green
    else:
        text = "LOSE"
        style = "danger"   # Red
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        text=text,
        callback_data="noop",
        style=style
    ))
    return kb

# ==================================================
# 🧠 Kaiyo STRATEGY ENGINE
# ==================================================
class GodTobiStrategyEngine:
    def __init__(self):
        self.history = deque(maxlen=500)
        self.logics = ["BLACK_LOGIC", "GOD_TOBI", "VIP_MATRIX", "TREND_FOLLOW", "TREND_FOLLOW_REVERSE"]
        
        self.vip_matrix = {
            (1, 1): "SMALL", (1, 2): "SMALL", (1, 3): "BIG", (1, 4): "SMALL", (1, 5): "BIG", (1, 6): "BIG", (1, 7): "BIG", (1, 8): "SMALL", (1, 9): "BIG",
            (2, 1): "BIG", (2, 2): "BIG", (2, 3): "BIG", (2, 4): "SMALL", (2, 5): "BIG", (2, 6): "SMALL", (2, 7): "BIG", (2, 8): "SMALL", (2, 9): "BIG",
            (3, 1): "BIG", (3, 2): "SMALL", (3, 3): "BIG", (3, 4): "BIG", (3, 5): "BIG", (3, 6): "SMALL", (3, 7): "SMALL", (3, 8): "SMALL", (3, 9): "BIG",
            (4, 1): "SMALL", (4, 2): "BIG", (4, 3): "SMALL", (4, 4): "SMALL", (4, 5): "SMALL", (4, 6): "BIG", (4, 7): "BIG", (4, 8): "SMALL", (4, 9): "SMALL",
            (5, 1): "BIG", (5, 2): "SMALL", (5, 3): "SMALL", (5, 4): "SMALL", (5, 5): "SMALL", (5, 6): "BIG", (5, 7): "SMALL", (5, 8): "SMALL", (5, 9): "BIG",
            (6, 1): "SMALL", (6, 2): "SMALL", (6, 3): "BIG", (6, 4): "SMALL", (6, 5): "BIG", (6, 6): "BIG", (6, 7): "BIG", (6, 8): "BIG", (6, 9): "BIG",
            (7, 1): "BIG", (7, 2): "SMALL", (7, 3): "BIG", (7, 4): "BIG", (7, 5): "SMALL", (7, 6): "BIG", (7, 7): "SMALL", (7, 8): "SMALL", (7, 9): "BIG",
            (8, 1): "SMALL", (8, 2): "BIG", (8, 3): "BIG", (8, 4): "SMALL", (8, 5): "SMALL", (8, 6): "BIG", (8, 7): "BIG", (8, 8): "BIG", (8, 9): "SMALL",
            (9, 1): "BIG", (9, 2): "SMALL", (9, 3): "SMALL", (9, 4): "BIG", (9, 5): "BIG", (9, 6): "BIG", (9, 7): "BIG", (9, 8): "BIG", (9, 9): "SMALL",
        }
        
    def add_result(self, period, number):
        num = int(number)
        result_type = 'BIG' if num >= 5 else 'SMALL'
        exists = False
        for h in self.history:
            if h.get('period') == period:
                exists = True
                break
        if not exists:
            self.history.appendleft({'period': period, 'number': num, 'type': result_type})

    def get_prediction(self, logic_name, period):
        if logic_name == "TREND_FOLLOW":
            return self.history[0]['type'] if len(self.history) > 0 else "BIG"
        elif logic_name == "TREND_FOLLOW_REVERSE":
            if len(self.history) == 0:
                return "BIG"
            return "SMALL" if self.history[0]['type'] == "BIG" else "BIG"
        elif logic_name == "BLACK_LOGIC":
            return "BIG" if len(self.history) % 2 == 0 else "SMALL"
        elif logic_name == "GOD_TOBI":
            return "BIG" if sum(h['number'] for h in list(self.history)[:3]) % 2 == 0 else "SMALL"
        elif logic_name == "VIP_MATRIX":
            if len(self.history) < 2: return "BIG"
            top = self.history[0]['number'] if self.history[0]['number'] != 0 else 5
            bottom = self.history[1]['number'] if self.history[1]['number'] != 0 else 5
            return self.vip_matrix.get((top, bottom), "BIG")
        return "BIG"

    def get_current_logic(self):
        return self.logics[0] if self.logics else "GOD_TOBI"

# ==================================================
# 📊 BOT STATE
# ==================================================
class BotState:
    def __init__(self):
        self.is_running = False
        self.pending_period = None
        self.pending_prediction = None
        self.last_sent_period = None
        self.current_msg_id = None
        self.wins = 0
        self.losses = 0
        self.loss_streak = 0
        self.is_reverse_mode = False
        self.current_logic_index = 0
        self.engine = GodTobiStrategyEngine()
        self.pending_messages: Dict[str, int] = {}
        self.results_history: List[Dict] = []  # Store last 10 results
        self.last_summary_sent = 0

state = BotState()

# ==================================================
# 📤 TELEGRAM FUNCTIONS
# ==================================================
def fetch_history_list():
    """Fetch the latest TRX history and log the real failure when the API is unavailable."""
    try:
        url = API_URL.format(int(time.time() * 1000))
        r = session.get(url, timeout=15)
        logger.info("History API HTTP status: %s", r.status_code)
        r.raise_for_status()

        data = r.json()
        if isinstance(data, dict):
            payload = data.get("data")
            if isinstance(payload, dict):
                history = payload.get("list")
                if isinstance(history, list):
                    logger.info("History API returned %d records", len(history))
                    return history

        logger.error("Unexpected History API response: %s", str(data)[:800])
    except requests.RequestException as e:
        logger.exception("History API request error: %s", e)
    except ValueError as e:
        logger.exception("History API JSON decode error: %s", e)
    except Exception as e:
        logger.exception("History API unexpected error: %s", e)

    return None

def safe_int_last_digit(val):
    try:
        s = str(val).strip()
        return int(s[-1]) if len(s) > 0 else None
    except:
        return None

def get_result_type(number: int) -> str:
    return "BIG" if number >= 5 else "SMALL"

def is_big(number: int) -> bool:
    return number >= 5

# ==================================================
# 🖼️ CANVAS IMAGE GENERATOR
# ==================================================
def generate_results_image(results: List[Dict]) -> BytesIO:
    """Generate canvas image with results table"""
    # Image settings
    width = 800
    height = 400 + (len(results) * 35)
    bg_color = (30, 30, 40)
    
    # Create image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_header = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
    
    # Title
    title = "TRX SIGNAL - LAST 10 RESULTS"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    draw.text(((width - title_width) // 2, 20), title, fill=(255, 215, 0), font=font_title)
    
    # Table headers
    headers = ["#", "PERIOD", "PREDICT", "RESULT", "STATUS"]
    x_positions = [30, 130, 330, 490, 610]
    y_start = 70
    
    # Header background
    draw.rectangle([20, y_start - 10, width - 20, y_start + 30], fill=(60, 60, 80))
    
    for i, header in enumerate(headers):
        draw.text((x_positions[i], y_start), header, fill=(255, 255, 255), font=font_header)
    
    # Table rows
    y = y_start + 40
    for idx, result in enumerate(results, 1):
        # Row background (alternating)
        if idx % 2 == 0:
            draw.rectangle([20, y - 5, width - 20, y + 25], fill=(40, 40, 55))
        
        # Data
        period = result.get('period', '')
        predict = result.get('prediction', '')
        actual = result.get('actual', '')
        status = result.get('status', '')
        
        # Period
        draw.text((x_positions[0], y), str(idx), fill=(200, 200, 200), font=font)
        draw.text((x_positions[1], y), str(period), fill=(200, 200, 200), font=font)
        
        # Prediction with color
        if predict == 'BIG':
            draw.text((x_positions[2], y), predict, fill=(255, 100, 100), font=font)
        else:
            draw.text((x_positions[2], y), predict, fill=(100, 200, 255), font=font)
        
        # Actual result
        if actual:
            actual_num = int(actual) if actual.isdigit() else 0
            if actual_num >= 5:
                draw.text((x_positions[3], y), f"{actual} (BIG)", fill=(255, 100, 100), font=font)
            else:
                draw.text((x_positions[3], y), f"{actual} (SMALL)", fill=(100, 200, 255), font=font)
        else:
            draw.text((x_positions[3], y), "-", fill=(150, 150, 150), font=font)
        
        # Status
        if status == 'WIN':
            draw.text((x_positions[4], y), "WIN", fill=(0, 255, 0), font=font)
        elif status == 'LOSE':
            draw.text((x_positions[4], y), "LOSE", fill=(255, 0, 0), font=font)
        else:
            draw.text((x_positions[4], y), "PENDING", fill=(255, 255, 0), font=font)
        
        y += 35
    
    # Stats summary
    wins = sum(1 for r in results if r.get('status') == 'WIN')
    losses = sum(1 for r in results if r.get('status') == 'LOSE')
    total = len([r for r in results if r.get('status') in ['WIN', 'LOSE']])
    win_rate = (wins / total * 100) if total > 0 else 0
    
    stats_y = y + 20
    stats_text = f"Stats: {wins}W / {losses}L | Win Rate: {win_rate:.1f}%"
    bbox = draw.textbbox((0, 0), stats_text, font=font)
    stats_width = bbox[2] - bbox[0]
    draw.text(((width - stats_width) // 2, stats_y), stats_text, fill=(200, 200, 200), font=font)
    
    # Save to bytes
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

# ==================================================
# 📝 MESSAGE FORMATTING (CUSTOM EMOJI SUPPORT)
# ==================================================
def format_top_line() -> str:
    first = "".join(
        custom_emoji("🔤", emoji_id)
        for emoji_id in TOP_EMOJI_IDS[:3]
    )
    second = "".join(
        custom_emoji("🔤", emoji_id)
        for emoji_id in TOP_EMOJI_IDS[3:]
    )
    return first + " " + second


def format_prediction(period: str, prediction: str) -> str:
    period = str(period)[-3:]

    sep = custom_emoji("🔣", SEPARATOR_EMOJI_ID)
    match = custom_emoji("🔥", MATCH_EMOJI_ID)
    buy = custom_emoji("✔️", BUY_EMOJI_ID)
    strategy = custom_emoji("✅", JUSTIN_STRATEGY_EMOJI_ID)

    return (
        f"{format_top_line()}\n\n"
        f"{match} MATCH {match}    {sep}    {period}\n\n"
        f"{buy} BUY {buy}    {sep}    {prediction}\n\n"
        f"{strategy} Justin Strategy {strategy}"
    )

def format_result(period: str, prediction: str, result_number: int) -> str:
    period = str(period)[-3:]
    result_type = get_result_type(result_number)

    sep = custom_emoji("🔣", SEPARATOR_EMOJI_ID)
    match = custom_emoji("🔥", MATCH_EMOJI_ID)
    buy = custom_emoji("✔️", BUY_EMOJI_ID)
    result = custom_emoji("⛳️", RESULT_EMOJI_ID)
    strategy = custom_emoji("✅", JUSTIN_STRATEGY_EMOJI_ID)

    return (
        f"{format_top_line()}\n\n"
        f"{match} MATCH {match}    {sep}    {period}\n\n"
        f"{buy} BUY {buy}    {sep}    {prediction}\n\n"
        f"{result} RESULT    {sep}    {result_number} ({result_type})\n\n"
        f"{strategy} Justin Strategy {strategy}"
    )

def send_prediction(period: str, prediction: str) -> Optional[int]:
    """Send prediction with PENDING button"""
    text = format_prediction(period, prediction)
    try:
        msg = bot.send_message(
            TELEGRAM_CHAT_ID,
            text,
            reply_markup=pending_keyboard(),
            parse_mode="HTML"
        )
        return msg.message_id
    except Exception as e:
        logger.error(f"Failed to send prediction: {e}")
        return None

def update_result(period: str, prediction: str, result_number: int, won: bool, msg_id: int):
    """Update prediction with WIN/LOSE button"""
    text = format_result(period, prediction, result_number)
    try:
        bot.edit_message_text(
            text,
            chat_id=TELEGRAM_CHAT_ID,
            message_id=msg_id,
            reply_markup=result_keyboard(won),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to update result: {e}")

def send_results_summary(results: List[Dict]):
    """Send results summary as image"""
    try:
        img_buffer = generate_results_image(results)
        caption = f"{custom_emoji('🌡️', SUMMARY_EMOJI_ID)} LAST 10 RESULTS SUMMARY"
        bot.send_photo(
            TELEGRAM_CHAT_ID,
            photo=img_buffer,
            caption=caption,
            parse_mode="HTML"
        )
        logger.info("Sent results summary image")
    except Exception as e:
        logger.error(f"Failed to send results summary: {e}")

# ==================================================
# 📊 COMMANDS
# ==================================================
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    total = state.wins + state.losses
    win_rate = (state.wins / total * 100) if total > 0 else 0
    logic_name = state.engine.logics[state.current_logic_index] if state.engine.logics else "Unknown"
    text = (
        f"TRX Signal Stats\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Wins      : {state.wins}\n"
        f"Losses    : {state.losses}\n"
        f"Win Rate  : {win_rate:.1f}%\n"
        f"Loss Streak: {state.loss_streak}x\n"
        f"Reverse   : {'ON' if state.is_reverse_mode else 'OFF'}\n"
        f"Logic     : {logic_name}\n"
        f"History   : {len(state.engine.history)} records\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    text = (
        f"Bot Status\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Running    : {'Yes' if state.is_running else 'No'}\n"
        f"Pending    : {state.pending_period or 'None'}\n"
        f"Prediction : {state.pending_prediction or 'None'}\n"
        f"Loss Streak: {state.loss_streak}x\n"
        f"Reverse    : {'ON' if state.is_reverse_mode else 'OFF'}\n"
        f"Logic Index: {state.current_logic_index + 1}/{len(state.engine.logics)}\n"
        f"History    : {len(state.engine.history)} records\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.reply_to(
        message,
        "TRX Signal Bot\n\n"
        "Auto-posts predictions every minute\n"
        "Color buttons: PENDING -> WIN / LOSE\n"
        "Kaiyo Strategy Engine (5 logics)\n"
        "Auto-reverse on loss\n"
        "Logic switching on loss\n\n"
        "Commands:\n"
        "/stats - View statistics\n"
        "/status - Check bot status",
        parse_mode="HTML"
    )

# ==================================================
# CALLBACK HANDLERS
# ==================================================
@bot.callback_query_handler(func=lambda call: call.data == "noop")
def on_noop(call):
    try:
        bot.answer_callback_query(call.id, "Result is locked in", show_alert=False)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "pending")
def on_pending(call):
    try:
        bot.answer_callback_query(call.id, "Waiting for result...", show_alert=False)
    except Exception:
        pass

# ==================================================
# 🔄 MAIN LOOP
# ==================================================
def bot_loop():
    """Main bot loop"""
    pending_period = None
    pending_prediction = None
    last_sent_period = None
    pending_msg_id = None
    loss_streak = 0
    is_reverse_mode = False
    current_logic_index = 0
    
    while state.is_running:
        try:
            history = fetch_history_list()
            if not history:
                logger.warning("No history received from API; retrying in 3 seconds.")
                time.sleep(3)
                continue
            
            # Initialize engine with history
            if not pending_period:
                for item in reversed(history[:20]):
                    iss = item.get("issueNumber", "")
                    num = safe_int_last_digit(item.get("number", ""))
                    if iss and num is not None:
                        state.engine.add_result(str(iss), num)
                
                latest_issue = history[0].get("issueNumber", "")
                pending_period = str(int(latest_issue) + 1)
                
                # Get prediction
                logic_name = state.engine.logics[current_logic_index]
                base_pred = state.engine.get_prediction(logic_name, pending_period)
                
                if is_reverse_mode:
                    pending_prediction = "SMALL" if base_pred == "BIG" else "BIG"
                else:
                    pending_prediction = base_pred
                
                if pending_period != last_sent_period:
                    msg_id = send_prediction(
                        pending_period,
                        pending_prediction
                    )
                    pending_msg_id = msg_id
                    last_sent_period = pending_period
                    logger.info(f"Sent: {pending_period} -> {pending_prediction}")

            else:
                # Check if pending period has result
                found_issue = None
                for item in history:
                    if str(item.get("issueNumber")) == str(pending_period):
                        found_issue = item
                        break
                
                if found_issue:
                    actual_num = safe_int_last_digit(found_issue.get("number", ""))
                    if actual_num is not None:
                        actual_result = "BIG" if actual_num >= 5 else "SMALL"
                        won = (pending_prediction == actual_result)
                        
                        # Update stats
                        if won:
                            state.wins += 1
                            loss_streak = 0
                        else:
                            state.losses += 1
                            loss_streak += 1
                            # Switch logic on loss
                            current_logic_index = (current_logic_index + 1) % len(state.engine.logics)
                            # Toggle reverse mode on loss
                            is_reverse_mode = not is_reverse_mode
                        
                        # Store result in history
                        result_data = {
                            'period': pending_period,
                            'prediction': pending_prediction,
                            'actual': str(actual_num),
                            'status': 'WIN' if won else 'LOSE'
                        }
                        state.results_history.append(result_data)
                        
                        # Keep only last 10
                        if len(state.results_history) > 10:
                            state.results_history.pop(0)
                        
                        # Send summary every 10 results
                        if len(state.results_history) >= 10:
                            send_results_summary(state.results_history)
                            state.results_history = []  # Reset after sending
                        
                        # Update result message
                        if pending_msg_id:
                            update_result(
                                pending_period,
                                pending_prediction,
                                actual_num,
                                won,
                                pending_msg_id
                            )
                            logger.info(f"{pending_period}: {'WIN' if won else 'LOSS'} (result={actual_num})")
                        
                        # Add to history
                        state.engine.add_result(pending_period, actual_num)
                        
                        # Prepare next prediction
                        latest_issue = history[0].get("issueNumber", "")
                        pending_period = str(int(latest_issue) + 1)
                        
                        logic_name = state.engine.logics[current_logic_index]
                        base_pred = state.engine.get_prediction(logic_name, pending_period)
                        
                        if is_reverse_mode:
                            pending_prediction = "SMALL" if base_pred == "BIG" else "BIG"
                        else:
                            pending_prediction = base_pred
                        
                        if pending_period != last_sent_period:
                            msg_id = send_prediction(
                                pending_period,
                                pending_prediction
                            )
                            pending_msg_id = msg_id
                            last_sent_period = pending_period
                            logger.info(f"Sent: {pending_period} -> {pending_prediction}")

        except Exception as e:
            logger.error(f"Bot loop error: {e}")
        
        time.sleep(3)

# ==================================================
# MAIN
# ==================================================
def main():
    print("=" * 55)
    print("   TRX SIGNAL BOT (Color Buttons + Results Image)")
    print("   Chat ID:", TELEGRAM_CHAT_ID)
    print("   Logic Engine: Kaiyo Strategy")
    print("=" * 55)
    
    state.is_running = True
    
    # Start bot loop in background
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    print("Bot started! Press Ctrl+C to stop.")
    print("Commands: /stats, /status")
    
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=25)
    except KeyboardInterrupt:
        print("\nShutting down...")
        state.is_running = False
        sys.exit(0)
    except Exception as e:
        logger.error(f"Polling error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        sys.exit(0)
