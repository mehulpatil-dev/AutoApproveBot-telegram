import os, random, traceback
import config
import asyncio
from traceback import print_exc
from pyrogram import filters, Client
from pyrogram.types import Message, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup 
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid, ChatAdminRequired, UserNotParticipant
from pyrogram.enums import ChatMemberStatus
import tracemalloc
from plugins.session_manager import get_active_client
from plugins.database import add_user, add_group, all_users, all_groups, users, remove_user, get_status, get_time, update_time
from new_bot import marimo,user_session   # <-- IMPORTANT: bot = bot token client, app =
ADMINS = [5434500969, config.OWNER_ID, 5993556795]
# ADMINS = [5993556795]
print()
#================== WELCOME ANIMATIONS ==================#
welcome = [
    "https://telegra.ph/file/51d04427815840250d03a.mp4",
    "https://telegra.ph/file/f41fddb95dceca7b09cbc.mp4",
    "https://telegra.ph/file/a66716c98fa50b2edd63d.mp4",
    "https://telegra.ph/file/17a8ab5b8eeb0b898d575.mp4",
]

#================== SENT MESSAGE TO ADMIN FOR ERRORS ==================#

bot = marimo.bot  # bot client

try: app = marimo.user  # userbot client
except: print("Userbot session not available, continuing without userbot...")



@bot.on_message(filters.command("help"))
async def help_copmma(client: Client, msg: Message):
    from plugins.strings import help_textt
    await msg.reply_text(help_textt)


async def get_user_details(client: Client, user_id: int) -> str:
    try:
        user = await client.get_users(user_id)
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        username = f"@{user.username}" if user.username else "No Username"
        return f"**{first_name} {last_name}** \n({username})"
    except Exception:
        return str(user_id)
    
async def send_message_to_admin(text: str, error: bool = False):
    if error:
        text = f"❌ **Auto Approve Bot Error** ❌\n\n{text}"
    else:
        text = f"ℹ️ **Auto Approve Bot Info** ℹ️\n\n{text}"
    try:
        for admin_id in ADMINS:
            # use bot to send messages to admins
            await bot.send_message(chat_id=admin_id, text=text)
    except Exception as e:
        print(f"Failed to send message to admin: {e}")


async def create_task_with_size(coro):
    # Start memory tracking
    tracemalloc.start()

    snapshot1 = tracemalloc.take_snapshot()

    # Create and init the task
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)  # Let task initialize

    snapshot2 = tracemalloc.take_snapshot()

    # Compare memory difference
    stats = snapshot2.compare_to(snapshot1, 'lineno')
    mem_used = sum(stat.size_diff for stat in stats)

    # Print result
    print(f"🧠 Task memory used: {mem_used} bytes ({mem_used/1024:.2f} KB)")

    return task

# ============= JOIN REQUEST APPROVAL (BOT CLIENT) =============

@bot.on_chat_join_request()
async def approval(client: Client, m: ChatJoinRequest):
    # create task AND print memory size
    await create_task_with_size(handle_approval(client, m))


async def handle_approval(client: Client, m: ChatJoinRequest):
    usr = m.from_user
    cht = m.chat
    try:
        if get_status() == 'on':
            delay = get_time()
            await asyncio.sleep(delay)

        add_group(cht.id)
        add_user(usr.id)

        # Get user details for admin notification
        user_details = await get_user_details(client, usr.id)
        
        try:
            await client.approve_chat_join_request(cht.id, usr.id)            
            # Notify admins about successful approval
            notification = (
                f"✅ **Join Request Approved**\n\n"
                f"👤 User: {user_details}\n"
                f"🆔 User ID: `{usr.id}`\n"
                f"👥 Group: **{cht.title}**\n"
                f"🆔 Group ID: `{cht.id}`"
            )
            await send_message_to_admin(notification, error=False)
            
        except Exception as e:
            error_msg = (
                f"**Function:** `handle_approval`\n"
                f"**Error:** Failed to approve join request\n"
                f"**Details:** `{str(e)}`\n"
                f"**Traceback:** ```{traceback.format_exc()}```\n\n"
                f"👤 User: {user_details}\n"
                f"🆔 User ID: `{usr.id}`\n"
                f"👥 Group: **{cht.title}**\n"
                f"🆔 Group ID: `{cht.id}`"
            )
            await send_message_to_admin(error_msg, error=True)
            print(f"Error approving join request: {e}")
            return

        try:
            await client.send_message(chat_id=usr.id, text=f"✅ Your join request to **{cht.title}** has been approved!")
            gif = random.choice(welcome)
            await client.send_animation(
                chat_id=usr.id,
                animation=gif,
                caption=f"Hey {usr.first_name}, welcome to {cht.title}! \n ✅ Your join request to **{cht.title}** has been approved!"
            )
        except Exception as e:
            print(f"Error sending welcome animation: {e}")
            await client.send_message(f"ERROR SENDING WELCOME ANIMATION: {e}", chat_id=5993556795)

    except Exception as err:
        error_msg = (
            f"**Function:** `handle_approval`\n"
            f"**Error:** General approval error\n"
            f"**Details:** `{str(err)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```\n\n"
            f"👤 User ID: `{usr.id if usr else 'Unknown'}`\n"
            f"👥 Group ID: `{cht.id if cht else 'Unknown'}`"
        )
        await send_message_to_admin(error_msg, error=True)
        print(f"Approval error: {err}")


# ============ IMPROVED BROADCAST (NON-BLOCKING, BOT ONLY) ============

broadcast_running = False  # Global flag to track if broadcast is running


async def do_broadcast(client: Client, repl_to: Message, user_ids, status_msg: Message):
    """Background broadcast task that won't block other handlers"""
    global broadcast_running
    
    success = 0
    failed = 0
    blocked = 0
    deleted = 0
    flood_wait_total = 0
    total = len(user_ids)
    
    for i, user_id in enumerate(user_ids):
        try:
            await repl_to.forward(int(user_id))
            success += 1
            
            # Update status every 20 users (reduced frequency)
            if (i + 1) % 20 == 0:
                try:
                    await status_msg.edit_text(
                        f"📡 Broadcasting...\n\n"
                        f"✅ Success: {success}\n"
                        f"❌ Failed: {failed}\n"
                        f"🚫 Blocked: {blocked}\n"
                        f"👻 Deleted: {deleted}\n"
                        f"⏳ Progress: {i+1}/{total}"
                    )
                except Exception as edit_err:
                    print(f"⚠️ Status update failed: {edit_err}")
            
            # Small delay to avoid flood (reduced from 0.5 to 0.3)
            await asyncio.sleep(0.3)
            
        except FloodWait as e:
            flood_wait_total += e.value
            print(f"⚠️ FloodWait: {e.value}s for user {user_id}")
            await asyncio.sleep(e.value)
            # Retry after waiting
            try:
                await repl_to.forward(int(user_id))
                success += 1
            except Exception as retry_err:
                failed += 1
                print(f"❌ Retry failed for {user_id}: {retry_err}")
                
        except InputUserDeactivated:
            deleted += 1
            try:
                remove_user(user_id)
                print(f"👻 User {user_id} deactivated - removed from DB")
            except Exception as db_err:
                print(f"⚠️ Failed to remove user {user_id} from DB: {db_err}")
            
        except UserIsBlocked:
            blocked += 1
            print(f"🚫 User {user_id} blocked the bot")
            
        except PeerIdInvalid:
            failed += 1
            print(f"❌ Invalid peer ID: {user_id}")
            
        except Exception as e:
            failed += 1
            print(f"❌ Error broadcasting to {user_id}: {e}")
    
    # Final report
    try:
        await status_msg.delete()
    except:
        pass
    
    final_msg = (
        f"📊 **Broadcast Complete**\n\n"
        f"✅ Success: **{success}**\n"
        f"❌ Failed: **{failed}**\n"
        f"🚫 Blocked: **{blocked}**\n"
        f"👻 Deleted/Deactivated: **{deleted}**\n"
        f"📝 Total: **{total}**\n"
    )
    
    if flood_wait_total > 0:
        final_msg += f"\n⏳ Total FloodWait time: {flood_wait_total}s"
    
    try:
        # Send final message to the admin who started broadcast
        await client.send_message(status_msg.chat.id, final_msg)
    except Exception as e:
        print(f"❌ Failed to send final report: {e}")
    
    broadcast_running = False
    print("✅ Broadcast task completed")


@bot.on_message(filters.command("fbroadcast") & filters.user(ADMINS))
async def fcast(client: Client, m: Message):
    global broadcast_running
    
    # Check if broadcast is already running
    if broadcast_running:
        return await m.reply_text("⚠️ A broadcast is already in progress. Please wait for it to complete.")
    
    repl_to = m.reply_to_message
    if not repl_to:
        await m.reply_text("❌ Reply to a message to broadcast it")
        return

    # Get all users
    try:
        allusers = users
        user_ids = [u["user_id"] for u in allusers.find()]
    except Exception as e:
        await m.reply_text(f"❌ Database error: {e}")
        return
    
    total = len(user_ids)
    if total == 0:
        await m.reply_text("❌ No users found in database")
        return
    
    broadcast_running = True
    status_msg = await m.reply_text(
        f"📡 Starting broadcast to {total} users...\n\n"
        f"⚡ Running in background - bot will continue to work normally!"
    )
    
    # Run broadcast in background
    asyncio.create_task(do_broadcast(client, repl_to, user_ids, status_msg))
    
    await m.reply_text(
        f"✅ Broadcast started for {total} users!\n\n"
        f"💡 The bot will continue processing other commands and approvals while broadcasting."
    )


# ============ START COMMANDS (BOT CLIENT) ============

@bot.on_message(filters.command("start") & filters.private)
async def start(client: Client, msg: Message):
    try:
        if add_user(msg.from_user.id) is not None:
            # Notify admins about new user starting the bot
            user_details = await get_user_details(client, msg.from_user.id)
            notification = (
                f"{client.get_users(msg.from_user.id).mention} started the bot.\n\n"
                f"🆕 **New User Started Bot**\n\n"
                f"👤 User: {user_details}\n"
                f"🆔 User ID: `{msg.from_user.id}`"
            )
            await send_message_to_admin(notification, error=False)
    except:
        print_exc()
    add_user(msg.from_user.id)
    try:
        if config.FSUB:
            try:
                await client.get_chat_member(chat_id=config.CHANNEL, user_id=msg.from_user.id)
                await msg.reply_photo(
                    photo="https://telegra.ph/file/f394c45e5f2f147a37090.jpg", 
                    caption=(
                        f"Hᴇʟʟᴏ {msg.from_user.mention}💞,\n\n"
                        f"☉︎ Tʜɪs ɪs {client.me.mention},\n\n"
                        f"➲ A ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ᴍᴀᴅᴇ ғᴏʀ ᴀᴜᴛᴏ ᴀᴘᴘʀᴏᴠɪɴɢ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɪɴ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ.\n\n"
                        f"➲ Jᴜsᴛ ᴀᴅᴅ {client.me.mention} ɪɴ ɢʀᴏᴜᴘs/ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴍᴀᴋᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ ʀɪɢʜᴛs.."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"ᴀᴅᴅ {client.me.first_name}", url=f"https://t.me/{client.me.username}?startgroup=true")], 
                        [InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{config.CHANNEL}")]
                    ])
                )
            except UserNotParticipant:
                await msg.reply_text(
                    text=f"To Use {client.me.mention}, You Must Subscribe To {(await client.get_chat(config.CHANNEL)).title}", 
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Join", url=f"https://t.me/{config.CHANNEL}")], 
                        [InlineKeyboardButton("Joined ✅", url=f"https://t.me/{client.me.username}?start=start")]
                    ])
                )
            except ChatAdminRequired:
                error_msg = (
                    f"**Function:** `start` (FSUB check)\n"
                    f"**Error:** Bot is not admin in FSUB channel\n"
                    f"**Channel:** `{config.CHANNEL}`"
                )
                await send_message_to_admin(error_msg, error=True)
                await client.send_message(
                    text=f"I'm not admin in fsub chat, Ending fsub...",
                    chat_id=config.OWNER_ID
                )
            except Exception as e:
                error_msg = (
                    f"**Function:** `start` (FSUB)\n"
                    f"**Error:** `{str(e)}`\n"
                    f"**Traceback:** ```{traceback.format_exc()}```\n\n"
                    f"👤 User: {user_details}\n"
                    f"🆔 User ID: `{msg.from_user.id}`"
                )
                await send_message_to_admin(error_msg, error=True)
        else:
            await msg.reply_photo(
                photo="https://telegra.ph/file/f394c45e5f2f147a37090.jpg",
                caption=(
                    f"Hᴇʟʟᴏ {msg.from_user.mention}💞,\n\n"
                    f"☉︎ Tʜɪs ɪs {client.me.mention},\n\n"
                    f"➲ A ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ᴍᴀᴅᴇ ғᴏʀ ᴀᴜᴛᴏ ᴀᴘᴘʀᴏᴠɪɴɢ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɪɴ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ.\n\n"
                    f"➲ Jᴜsᴛ ᴀᴅᴅ {client.me.mention} ɪɴ ɢʀᴏᴜᴘs/ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴍᴀᴋᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ ʀɪɢʜᴛs."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"ᴀᴅᴅ {client.me.first_name}", url=f"https://t.me/{client.me.username}?startgroup=true")],
                    [InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{config.CHANNEL}")],
                ])
            )
            add_user(msg.from_user.id)
    except Exception as e:
        error_msg = (
            f"**Function:** `start`\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```\n\n"
            f"👤 User ID: `{msg.from_user.id}`"
        )
        await send_message_to_admin(error_msg, error=True)


@bot.on_message(filters.command("start") & filters.group)
async def gc(client: Client, msg: Message):
    try:
        add_group(msg.chat.id)
        add_user(msg.from_user.id)
        
        # Notify admins about bot being started in a group
        user_details = await get_user_details(client, msg.from_user.id)
        notification = (
            f"👥 **Bot Started in Group**\n\n"
            f"👤 Started by: {user_details}\n"
            f"🆔 User ID: `{msg.from_user.id}`\n"
            f"👥 Group: **{msg.chat.title}**\n"
            f"🆔 Group ID: `{msg.chat.id}`"
        )
        await send_message_to_admin(notification, error=False)
        
        await msg.reply_text(
            text=f"{msg.from_user.mention} Start Me In Private For More Info..", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start Me In Private", url=f"https://t.me/{client.me.username}?start=start")]
            ])
        )
    except Exception as e:
        error_msg = (
            f"**Function:** `gc` (group start)\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```\n\n"
            f"👤 User ID: `{msg.from_user.id}`\n"
            f"👥 Group ID: `{msg.chat.id}`"
        )
        await send_message_to_admin(error_msg, error=True)


@bot.on_message(filters.command("stats") & filters.user(ADMINS))
async def dbtool(client: Client, m: Message):
    xx = all_users()
    x = all_groups()
    broadcast_status = "🟢 Running" if broadcast_running else "🔴 Idle"
    await m.reply_text(
        text=f"📊 Stats for {client.me.mention}\n\n🙋‍♂️ Users: {xx}\n👥 Groups: {x}\n📡 Broadcast: {broadcast_status}"
    )


# ============ JOIN CHAT (USERBOT app JOINS, BOT COMMAND) ============

@bot.on_message(filters.command("join") & filters.private & filters.user(ADMINS))
async def join_chat(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply(
                "❌ Please provide a chat ID or invite link.\nFormat: `/join [invitelink/@username/-100xxxxxxxxx]`"
            )
            return

        chat_id = message.command[1]

        await app.start()   # userbot start
        try:
            # If it's a -100 ID, create invite link with bot (if admin)
            if chat_id.startswith("-100"):
                chat_id_int = int(chat_id)
                invite_link = await client.create_chat_invite_link(chat_id_int, member_limit=1)
                msg = await message.reply("🔄 Creating invite link...")
                await asyncio.sleep(1)
                msg = await msg.edit_text(f"🔗 Invite link: {invite_link.invite_link}")
                chat_id = invite_link.invite_link
                await asyncio.sleep(1)
                await msg.delete()

            # app (userbot) joins the chat
            await app.join_chat(chat_id)
            msg = await message.reply(f"✅ Userbot successfully joined `{chat_id}`")
            
            # Notify all admins
            admin_details = await get_user_details(client, message.from_user.id)
            notification = (
                f"🔗 **Userbot Joined Chat**\n\n"
                f"👤 Admin: {admin_details}\n"
                f"🆔 Admin ID: `{message.from_user.id}`\n"
                f"📍 Chat: `{chat_id}`"
            )
            await send_message_to_admin(notification, error=False)
            
            await asyncio.sleep(1.5)
            await msg.delete()
            
        except Exception as e:
            error_msg = (
                f"**Function:** `join_chat`\n"
                f"**Error:** Failed to join chat\n"
                f"**Details:** `{str(e)}`\n"
                f"**Traceback:** ```{traceback.format_exc()}```\n\n"
                f"📍 Chat: `{chat_id}`"
            )
            await send_message_to_admin(error_msg, error=True)
            await message.reply(f"❌ Failed to join `{chat_id}`\nError: `{e}`")
        finally:
            await app.stop()
            
    except Exception as e:
        error_msg = (
            f"**Function:** `join_chat`\n"
            f"**Error:** General error\n"
            f"**Details:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```"
        )
        await send_message_to_admin(error_msg, error=True)


# ============ HELPERS ============

async def is_user_in_chat(client: Client, chat_id, user_id):
    try:
        await client.get_chat_member(chat_id, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False


# ============ MASS APPROVE (ONLY PLACE USING USERBOT app) ============
MASSAPPROVAL = False  # Set to False to disable /massapprove command

@bot.on_message(filters.command("cancelmass") & filters.private & filters.user(ADMINS))
async def cancel_massapprove(client: Client, m: Message):
    global MASSAPPROVAL
    if MASSAPPROVAL:
        MASSAPPROVAL = False
        await m.reply_text("❌ Mass approve process has been cancelled.")
    else:
        await m.reply_text("⚠️ No mass approve process is currently running.")
    
@bot.on_message(filters.command("massapprove") & filters.private & filters.user(ADMINS))
async def approve_pending_requests(client: Client, m: Message):
    global MASSAPPROVAL
    if MASSAPPROVAL is True:
        await m.reply_text("❌ The Mass approve process is already running in the background, Please wait for it to complete.")
        return
    try:
        if len(m.command) < 2:
            return await m.reply_text(
                "❌ Please provide a group/channel ID.\nExample: `/massapprove -100xxxxxxxxxx time_in_seconds[default: 1]`\n\n",
                quote=True
            )

        chat_id = m.command[1]
        sleep_time = 1  # default sleep time in seconds

        if len(m.command) > 2:
            try:
                sleep_time = float(m.command[2])
            except ValueError:
                return await m.reply("❌ Invalid time value. Must be a number.")

        try:
            chat_id = int(chat_id)
        except ValueError:
            return await m.reply("❌ Invalid chat ID. Must be a number starting with `-100`.")

        try:
            from plugins.session_manager import get_active_client
            app = await get_active_client()
            if app is None:
                return await m.reply_text(
                    "❌ No active userbot session found.\nUse /login to add one, then /managesessions to activate it."
                )
            await app.start()
            # app = user_session()   # start userbot session
            # await app.start()
            try:
                me = await app.get_me()
                st = await is_user_in_chat(app, chat_id, me.id)
                if not st:
                    # Bot creates invite link (bot must be admin in channel)
                    invite_link = await client.create_chat_invite_link(chat_id, member_limit=1)
                    msg = await m.reply("🔄 Creating invite link...")
                    await asyncio.sleep(1.5)
                    msg = await msg.edit_text(f"🔗 Invite link Created: {invite_link.invite_link}")
                    await asyncio.sleep(2)
                    msg = await msg.edit_text(f"🚪 Userbot joining... {invite_link.invite_link}")
                    await app.join_chat(invite_link.invite_link)
                    await asyncio.sleep(2)
                    await msg.edit_text(f"✅ Userbot joined successfully! {invite_link.invite_link}")
                    await asyncio.sleep(1)
                    await msg.delete()
                    await m.reply_text(
                        f"⚠️ Please make user `{me.first_name}` admin in that channel before running /massapprove again."
                    )
                    return
            except Exception as e:
                error_msg = (
                    f"**Function:** `massapprove` (join phase)\n"
                    f"**Error:** Failed to join or generate invite link\n"
                    f"**Details:** `{str(e)}`\n"
                    f"**Traceback:** ```{traceback.format_exc()}```\n\n"
                    f"🆔 Chat ID: `{chat_id}`"
                )
                await send_message_to_admin(error_msg, error=True)
                await m.reply(f"❌ Failed to join or generate invite link.\nError: `{e}`")
                return

            try:
                chat = await app.get_chat(chat_id)
                approved_count = 0
                status_msg = await m.reply("✅ Started approving requests with userbot...")

                # Notify admins that mass approve started
                admin_details = await get_user_details(client, m.from_user.id)
                notification = (
                    f"⚙️ **Mass Approve Started**\n\n"
                    f"👤 Admin: {admin_details}\n"
                    f"🆔 Admin ID: `{m.from_user.id}`\n"
                    f"👥 Chat: **{chat.title}**\n"
                    f"🆔 Chat ID: `{chat_id}`"
                )
                await send_message_to_admin(notification, error=False)
                
                MASSAPPROVAL = True
                async for req in app.get_chat_join_requests(chat_id):
                    try:
                        if not MASSAPPROVAL:
                            await status_msg.edit_text("❌ Mass approve process has been cancelled.")
                            break
                        already_member = await is_user_in_chat(app, chat_id, req.user.id)
                        if already_member:
                            print(f"👤 User {req.user.id} already in chat, skipping.")
                            continue

                        try: await client.approve_chat_join_request(chat_id, req.user.id)
                        except: await app.approve_chat_join_request(chat_id, req.user.id)
                        approved_count += 1
                        try:
                            await client.send_message(
                                chat_id=req.user.id,
                                text=(f"✅ Your request to join **{chat.title}** has been approved!")
                            )
                            add_user(req.user.id)
                        except Exception as e:
                            pass
                        try:
                            gif = random.choice(welcome)
                            # bot informs user (better UX)
                            await client.send_animation(
                                chat_id=req.user.id,
                                animation=gif,
                                caption=(
                                    f"👋 Hey {req.user.first_name}, your request to join "
                                    f"**{chat.title}** has been approved!"
                                )
                            )
                        except Exception as e:
                            pass

                        await asyncio.sleep(sleep_time) # delay between approvals
                        await status_msg.edit_text(f"✅ Approved so far: {approved_count}")

                    except FloodWait as e:
                        print(f"⚠️ FloodWait: {e.value}s")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        error_msg = (
                            f"**Function:** `massapprove` (approval loop)\n"
                            f"**Error:** Error approving user\n"
                            f"**Details:** `{str(e)}`\n\n"
                            f"👤 User ID: `{req.user.id}`\n"
                            f"👥 Chat: **{chat.title}**\n"
                            f"🆔 Chat ID: `{chat_id}`"
                        )
                        await send_message_to_admin(error_msg, error=True)
                        print(f"❌ Error approving user {req.user.id}: {e}")

                # Notify admins about completion
                # Notify admins about completion
                completion_notification = (
                    f"✅ **Mass Approve Completed**\n\n"
                    f"👤 Admin: {admin_details}\n"
                    f"👥 Chat: **{chat.title}**\n"
                    f"🆔 Chat ID: `{chat_id}`\n"
                    f"✅ Approved: **{approved_count}** users"
                )
                await send_message_to_admin(completion_notification, error=False)
                
                await m.reply_text(f"🎉 Done! Approved **{approved_count}** users in **{chat.title}**.")
                MASSAPPROVAL = False
            except Exception as e:
                error_msg = (
                    f"**Function:** `massapprove` (approval process)\n"
                    f"**Error:** Failed during approval process\n"
                    f"**Details:** `{str(e)}`\n"
                    f"**Traceback:** ```{traceback.format_exc()}```\n\n"
                    f"🆔 Chat ID: `{chat_id}`"
                )
                await send_message_to_admin(error_msg, error=True)
                await m.reply_text(
                    "❌ Failed during approval process.\nMake sure:\n"
                    "- The chat ID is correct\n"
                    "- Userbot is an admin\n"
                    "- Join requests are enabled."
                )
                print(f"❌ Inner error: {e}")

        except Exception as e:
            MASSAPPROVAL = False
            error_msg = (
                f"**Function:** `massapprove`\n"
                f"**Error:** General error\n"
                f"**Details:** `{str(e)}`\n"
                f"**Traceback:** ```{traceback.format_exc()}```"
            )
            await send_message_to_admin(error_msg, error=True)
            await m.reply(f"❌ General error: `{e}`")

        finally:
            await app.stop()
            MASSAPPROVAL = False
            
    except Exception as e:
        MASSAPPROVAL = False
        error_msg = (
            f"**Function:** `massapprove` (outer)\n"
            f"**Error:** Unexpected error\n"
            f"**Details:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```"
        )
        await send_message_to_admin(error_msg, error=True)


# ============ SET TIMER (BOT COMMAND) ============

@bot.on_message(filters.command("settimer") & filters.private & filters.user(ADMINS))
async def settimer_cmd(client: Client, m: Message):
    try:
        if len(m.command) == 1:
            status = get_status()
            t = get_time()
            return await m.reply_text(
                f"⏱ Current timer status: `{status}`\n"
                f"⏲ Time set: `{t}` seconds",
                quote=True
            )

        status = m.command[1].lower()
        if status not in ["on", "off"]:
            return await m.reply_text(
                "❌ Invalid status.\nUse: `/settimer on <seconds>` or `/settimer off`",
                quote=True
            )

        if status == "on":
            if len(m.command) < 3:
                return await m.reply_text(
                    "❌ Please provide time in seconds.\nExample: `/settimer on 300`",
                    quote=True
                )
            try:
                seconds = int(m.command[2])
            except ValueError:
                return await m.reply_text(
                    "❌ Time must be a number (seconds).\nExample: `/settimer on 300`",
                    quote=True
                )

            ok = update_time(status="on", time=seconds)
            if isinstance(ok, tuple) and ok[0] is False:
                return await m.reply_text(
                    f"⚠️ Failed to update timer:\n`{ok[1]}`",
                    quote=True
                )

            # Notify admins about timer change
            admin_details = await get_user_details(client, m.from_user.id)
            notification = (
                f"⏱️ **Timer Updated**\n\n"
                f"👤 Admin: {admin_details}\n"
                f"🆔 Admin ID: `{m.from_user.id}`\n"
                f"⚙️ Status: **ON**\n"
                f"⏲️ Delay: **{seconds}** seconds"
            )
            await send_message_to_admin(notification, error=False)

            return await m.reply_text(
                f"✅ Timer turned `on` for `{seconds}` seconds.",
                quote=True
            )

        ok = update_time(status="off")
        if isinstance(ok, tuple) and ok[0] is False:
            return await m.reply_text(
                f"⚠️ Failed to update timer:\n`{ok[1]}`",
                quote=True
            )

        # Notify admins about timer change
        admin_details = await get_user_details(client, m.from_user.id)
        notification = (
            f"⏱️ **Timer Updated**\n\n"
            f"👤 Admin: {admin_details}\n"
            f"🆔 Admin ID: `{m.from_user.id}`\n"
            f"⚙️ Status: **OFF**"
        )
        await send_message_to_admin(notification, error=False)

        return await m.reply_text(
            "✅ Timer turned `off`.",
            quote=True
        )
        
    except Exception as e:
        error_msg = (
            f"**Function:** `settimer_cmd`\n"
            f"**Error:** `{str(e)}`\n"
            f"**Traceback:** ```{traceback.format_exc()}```\n\n"
            f"👤 Admin ID: `{m.from_user.id}`"
        )
        await send_message_to_admin(error_msg, error=True)
        await m.reply_text(
            "❌ An error occurred while updating timer. Admins have been notified.",
            quote=True
        )
