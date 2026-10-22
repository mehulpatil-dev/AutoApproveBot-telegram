import os, json
import config
from pyrogram import filters, Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import (
    FloodWait,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
    PasswordHashInvalid,
)
from new_bot import marimo
from plugins.database import get_all_tracked_channels, get_channel_stats
 

bot = marimo.bot  # same bot client used everywhere else

ADMINS = [5434500969, config.OWNER_ID, 5993556795]

SESSIONS_FILE = "sessions.txt"   # session strings are stored here, mapped by name

# admin_id -> {"step", "client", "name", "phone", "phone_code_hash"}
PENDING = {}


# ============ STORAGE (sessions.txt) ============

def _default():
    return {"active": None, "sessions": {}}


def load_sessions():
    if not os.path.exists(SESSIONS_FILE):
        return _default()
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return _default()
        data = json.loads(content)
        data.setdefault("active", None)
        data.setdefault("sessions", {})
        return data
    except Exception:
        return _default()


def save_sessions(data):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def get_active_client():
    """Returns a not-yet-started Client built from the active saved session, or None."""
    data = load_sessions()
    active = data.get("active")
    if not active or active not in data["sessions"]:
        return None
    try:
        api_id = int(config.API_ID)
        api_hash = config.API_HASH
    except AttributeError:
        return None
    return Client(
        name=f"userbot_{active}",
        api_id=api_id,
        api_hash=api_hash,
        session_string=data["sessions"][active],
        in_memory=True,
    )


# ============ /login FLOW ============

@bot.on_message(filters.command("login") & filters.private & filters.user(ADMINS))
async def login_cmd(client: Client, m: Message):
    if len(m.command) < 2:
        return await m.reply_text(
            "❌ Usage: `/login <session_name>`\nExample: `/login main`", quote=True
        )
    name = m.command[1].strip()

    data = load_sessions()
    if name in data["sessions"]:
        return await m.reply_text(
            f"⚠️ A session named `{name}` already exists.\nUse a different name, or /logout `{name}` first."
        )
    if m.from_user.id in PENDING:
        return await m.reply_text("⚠️ You already have a login in progress. Send /cancellogin to abort it.")

    try:
        api_id = int(config.API_ID)
        api_hash = config.API_HASH
    except AttributeError:
        return await m.reply_text("❌ `API_ID` / `API_HASH` not found in config.py. Add them to use /login.")

    userbot = Client(name=f"login_{m.from_user.id}", api_id=api_id, api_hash=api_hash, in_memory=True)
    await userbot.connect()

    PENDING[m.from_user.id] = {"step": "phone", "client": userbot, "name": name}
    await m.reply_text(
        "📱 Send the phone number for this userbot session.\n"
        "Format: `+countrycode number`  e.g. `+919876543210`\n\n"
        "Send /cancellogin anytime to abort.",
        quote=True,
    )


@bot.on_message(filters.command("cancellogin") & filters.private & filters.user(ADMINS))
async def cancel_login(client: Client, m: Message):
    state = PENDING.pop(m.from_user.id, None)
    if not state:
        return await m.reply_text("⚠️ No login in progress.")
    try:
        await state["client"].disconnect()
    except Exception:
        pass
    await m.reply_text("❌ Login cancelled.")


def _pending_filter(_, __, m: Message):
    return bool(m.from_user) and m.from_user.id in PENDING and bool(m.text) and not m.text.startswith("/")


pending_filter = filters.create(_pending_filter)


@bot.on_message(filters.private & filters.user(ADMINS) & pending_filter)
async def login_flow(client: Client, m: Message):
    state = PENDING.get(m.from_user.id)
    if not state:
        return
    step = state["step"]
    userbot: Client = state["client"]

    if step == "phone":
        phone = m.text.strip()
        try:
            sent = await userbot.send_code(phone)
        except FloodWait as e:
            return await m.reply_text(f"⏳ FloodWait: try again in {e.value}s.")
        except PhoneNumberInvalid:
            return await m.reply_text("❌ Invalid phone number. Try again with the country code, e.g. `+91...`.")
        except Exception as e:
            del PENDING[m.from_user.id]
            await userbot.disconnect()
            return await m.reply_text(f"❌ Failed to send code: `{e}`")

        state["phone"] = phone
        state["phone_code_hash"] = sent.phone_code_hash
        state["step"] = "code"
        await m.reply_text(
            "🔑 Enter the login code you received.\n"
            "⚠️ Telegram invalidates codes sent as-is through a bot — insert a letter between the "
            "digits before sending, e.g. if the code is `12345` send `1a2a3a4a5a`.",
            quote=True,
        )
        return

    if step == "code":
        code = "".join(ch for ch in m.text.strip() if ch.isdigit())
        try:
            await userbot.sign_in(state["phone"], state["phone_code_hash"], code)
        except SessionPasswordNeeded:
            state["step"] = "password"
            return await m.reply_text("🔒 Two-step verification is enabled. Send your password.", quote=True)
        except (PhoneCodeInvalid, PhoneCodeExpired) as e:
            del PENDING[m.from_user.id]
            await userbot.disconnect()
            return await m.reply_text(f"❌ Invalid/expired code: `{e}`. Start again with /login.", quote=True)
        except Exception as e:
            del PENDING[m.from_user.id]
            await userbot.disconnect()
            return await m.reply_text(f"❌ Login failed: `{e}`", quote=True)

        return await _finish_login(m, state)

    if step == "password":
        try:
            await userbot.check_password(m.text.strip())
        except PasswordHashInvalid:
            return await m.reply_text("❌ Wrong password, try again.", quote=True)
        except Exception as e:
            del PENDING[m.from_user.id]
            await userbot.disconnect()
            return await m.reply_text(f"❌ Login failed: `{e}`", quote=True)

        return await _finish_login(m, state)


async def _finish_login(m: Message, state: dict):
    userbot: Client = state["client"]
    name = state["name"]

    session_string = await userbot.export_session_string()
    await userbot.disconnect()

    data = load_sessions()
    data["sessions"][name] = session_string
    made_active = False
    if not data.get("active"):
        data["active"] = name
        made_active = True
    save_sessions(data)

    PENDING.pop(m.from_user.id, None)
    await m.reply_text(
        f"✅ Session `{name}` saved successfully" + (" and set as active." if made_active else "."),
        quote=True,
    )


# ============ /logout, /viewsessions ============

@bot.on_message(filters.command("logout") & filters.private & filters.user(ADMINS))
async def logout_cmd(client: Client, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("❌ Usage: `/logout <session_name>`", quote=True)
    name = m.command[1].strip()

    data = load_sessions()
    if name not in data["sessions"]:
        return await m.reply_text(f"⚠️ No session named `{name}`.")

    del data["sessions"][name]
    if data.get("active") == name:
        data["active"] = next(iter(data["sessions"]), None)
    save_sessions(data)

    await m.reply_text(f"✅ Session `{name}` removed.")


@bot.on_message(filters.command("viewsessions") & filters.private & filters.user(ADMINS))
async def view_sessions(client: Client, m: Message):
    data = load_sessions()
    if not data["sessions"]:
        return await m.reply_text("📭 No userbot sessions saved. Use /login to add one.")

    lines = ["📋 **Saved Userbot Sessions**\n"]
    for name in data["sessions"]:
        mark = "✅" if data.get("active") == name else "▫️"
        lines.append(f"{mark} `{name}`")
    lines.append(f"\n🟢 Active: `{data.get('active') or 'None'}`")
    await m.reply_text("\n".join(lines))


# ============ /managesessions (inline buttons) ============

def _sessions_keyboard(data):
    buttons = []
    for name in data["sessions"]:
        mark = "✅ " if data.get("active") == name else ""
        buttons.append(
            [
                InlineKeyboardButton(f"{mark}{name}", callback_data=f"sess_active:{name}"),
                InlineKeyboardButton("🗑", callback_data=f"sess_del:{name}"),
            ]
        )
    return InlineKeyboardMarkup(buttons)


@bot.on_message(filters.command("managesessions") & filters.private & filters.user(ADMINS))
async def manage_sessions(client: Client, m: Message):
    data = load_sessions()
    if not data["sessions"]:
        return await m.reply_text("📭 No userbot sessions saved. Use /login to add one.")

    await m.reply_text(
        "⚙️ **Manage Userbot Sessions**\nTap a name to set it active, or 🗑 to delete it.",
        reply_markup=_sessions_keyboard(data),
    )


@bot.on_callback_query(filters.user(ADMINS) & filters.regex(r"^sess_(active|del):"))
async def sessions_callback(client: Client, cq: CallbackQuery):
    action, name = cq.data.split(":", 1)
    data = load_sessions()

    if name not in data["sessions"]:
        return await cq.answer("Session no longer exists.", show_alert=True)

    if action == "sess_active":
        data["active"] = name
        save_sessions(data)
        await cq.answer(f"✅ {name} set as active")
    else:
        del data["sessions"][name]
        if data.get("active") == name:
            data["active"] = next(iter(data["sessions"]), None)
        save_sessions(data)
        await cq.answer(f"🗑 {name} deleted")

    if not data["sessions"]:
        return await cq.message.edit_text("📭 No userbot sessions saved. Use /login to add one.")
    await cq.message.edit_reply_markup(_sessions_keyboard(data))



 
async def send_message_to_admin(text: str, error: bool = False):
    if error:
        text = f"❌ **Auto Approve Bot Error** ❌\n\n{text}"
    else:
        text = f"ℹ️ **Auto Approve Bot Info** ℹ️\n\n{text}"
    try:
        for admin_id in ADMINS:
            await bot.send_message(chat_id=admin_id, text=text)
    except Exception as e:
        print(f"Failed to send message to admin: {e}")
 
 
def _channels_message_and_keyboard(channels):
    channels.sort(key=lambda x: x.get('total_joins', 0), reverse=True)
 
    message_text = "📊 **Channel Statistics Dashboard**\n\n"
    message_text += "Select a channel to view detailed 7-day statistics:\n\n"
 
    keyboard = []
    for idx, channel in enumerate(channels, 1):
        chat_title = channel.get('chat_title', 'Unknown Channel')
        chat_id = channel.get('chat_id')
        total_joins = channel.get('total_joins', 0)
 
        display_title = chat_title[:27] + "..." if len(chat_title) > 30 else chat_title
 
        message_text += f"{idx}. **{display_title}**\n"
        message_text += f"   └ ID: `{chat_id}` | Total: {total_joins} users\n\n"
 
        keyboard.append([
            InlineKeyboardButton(
                f"📈 {idx}. {display_title} ({total_joins})",
                callback_data=f"chanstats_{chat_id}"
            )
        ])
 
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_channels")])
    return message_text, InlineKeyboardMarkup(keyboard)
 
 
@bot.on_message(filters.command("channelshow") & filters.user(ADMINS))
async def show_channels(client: Client, m: Message):
    try:
        channels = get_all_tracked_channels()
 
        if not channels:
            await m.reply_text(
                "📭 **No Channels Tracked Yet**\n\n"
                "No channels have been tracked yet. The bot will start tracking "
                "channels automatically when join requests are approved.",
                quote=True
            )
            return
 
        message_text, keyboard = _channels_message_and_keyboard(channels)
        await m.reply_text(message_text, reply_markup=keyboard, quote=True)
 
    except Exception as e:
        error_msg = (
            f"**Function:** `show_channels`\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```"
        )
        await send_message_to_admin(error_msg, error=True)
        await m.reply_text(
            "❌ An error occurred while fetching channel statistics. Admins have been notified.",
            quote=True
        )
 
 
@bot.on_callback_query(filters.user(ADMINS) & filters.regex(r"^chanstats_"))
async def show_channel_stats(client: Client, callback_query: CallbackQuery):
    try:
        chat_id = callback_query.data.split("_", 1)[1]
        stats = get_channel_stats(chat_id, days=7)
 
        if not stats:
            await callback_query.answer("❌ No statistics found for this channel", show_alert=True)
            return
 
        message_text = f"📊 **Channel Statistics**\n\n"
        message_text += f"📺 **Channel:** {stats['chat_title']}\n"
        message_text += f"🆔 **ID:** `{stats['chat_id']}`\n"
        message_text += f"👥 **Total Joins:** {stats['total_joins']}\n"
        message_text += f"📅 **Last 7 Days:** {stats['period_total']} joins\n\n"
        message_text += "📈 **Daily Breakdown (Last 7 Days):**\n\n"
 
        max_count = max([day['count'] for day in stats['daily_breakdown']], default=1)
 
        for day in stats['daily_breakdown']:
            date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            day_short = day['day_name'][:3]
            date_short = date_obj.strftime("%d %b")
            count = day['count']
 
            bar_length = int((count / max_count) * 10) if max_count > 0 else 0
            bar = "█" * bar_length + "░" * (10 - bar_length)
 
            message_text += f"`{day_short} {date_short}` {bar} **{count}**\n"
 
        avg_daily = stats['period_total'] / 7
        message_text += f"\n📊 **Average:** {avg_daily:.1f} joins/day"
 
        if len(stats['daily_breakdown']) >= 2:
            recent_avg = sum(d['count'] for d in stats['daily_breakdown'][-3:]) / 3
            older_avg = sum(d['count'] for d in stats['daily_breakdown'][:3]) / 3
            if recent_avg > older_avg * 1.2:
                message_text += "\n📈 **Trend:** Growing ⬆️"
            elif recent_avg < older_avg * 0.8:
                message_text += "\n📉 **Trend:** Declining ⬇️"
            else:
                message_text += "\n➡️ **Trend:** Stable"
 
        keyboard = [[
            InlineKeyboardButton("🔄 Refresh", callback_data=f"chanstats_{chat_id}"),
            InlineKeyboardButton("⬅️ Back", callback_data="refresh_channels")
        ]]
        try:
            await callback_query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
            await callback_query.answer()
        except Exception:
            await callback_query.answer("Refreshed 🐐")
 
    except Exception as e:
        error_msg = (
            f"**Function:** `show_channel_stats`\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```"
        )
        await send_message_to_admin(error_msg, error=True)
        await callback_query.answer("❌ Error loading statistics. Admins have been notified.", show_alert=True)
 
 
@bot.on_callback_query(filters.user(ADMINS) & filters.regex(r"^refresh_channels$"))
async def refresh_channels(client: Client, callback_query: CallbackQuery):
    try:
        channels = get_all_tracked_channels()
 
        if not channels:
            try:
                await callback_query.edit_message_text(
                    "📭 **No Channels Tracked Yet**\n\n"
                    "No channels have been tracked yet. The bot will start tracking "
                    "channels automatically when join requests are approved."
                )
            except Exception:
                pass
            await callback_query.answer("✅ Refreshed")
            return
 
        message_text, keyboard = _channels_message_and_keyboard(channels)
        try:
            await callback_query.edit_message_text(message_text, reply_markup=keyboard)
        except Exception:
            pass
        await callback_query.answer("✅ Refreshed")
 
    except Exception as e:
        error_msg = (
            f"**Function:** `refresh_channels`\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```"
        )
        await send_message_to_admin(error_msg, error=True)
        await callback_query.answer("❌ Error refreshing. Please try again.", show_alert=True)
 
