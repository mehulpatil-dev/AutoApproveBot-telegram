help_textt= help_textt ="""🤖 **Auto Approve Bot Help Menu**

Here are all available commands:

━━━━━━━━━━━━━━━━━━━━
👤 **User Commands**
━━━━━━━━━━━━━━━━━━━━

`/start`
Start the bot and get information about how it works.

━━━━━━━━━━━━━━━━━━━━
👑 **Admin Commands**
━━━━━━━━━━━━━━━━━━━━

📊 **Statistics & Info**

`/stats`
View total users, groups, and broadcast status.

`/channelshow`
Show tracked channels and view join statistics.

━━━━━━━━━━━━━━━━━━━━
📡 **Broadcast Commands**

`/fbroadcast`
Broadcast a message to all users.
Usage: Reply to a message and send `/fbroadcast`

━━━━━━━━━━━━━━━━━━━━
⏱ **Timer Commands**

`/settimer`
View current timer status.

`/settimer on <seconds>`
Enable auto-approve delay timer.
Example: `/settimer on 300`

`/settimer off`
Disable auto-approve delay timer.

━━━━━━━━━━━━━━━━━━━━
👥 **Join & Approval Commands**

`/join <chat_id/invite_link>`
Make userbot join a group/channel.

Example:
`/join -100xxxxxxxxxx`
or
`/join https://t.me/invite_link`

━━━━━━━━━━━━━━━━━━━━
⚡ **Mass Approval Commands**

`/massapprove <chat_id> <delay>`
Approve all pending join requests using the active userbot session.

Example:
`/massapprove -100xxxxxxxxxx 1`

`/cancelmass`
Cancel running mass approval process.

━━━━━━━━━━━━━━━━━━━━
🔐 **Session Management Commands**

`/login <session_name>`
Log a userbot into a new session (phone number → code → 2FA if enabled).
Example: `/login main`

`/cancellogin`
Abort a login currently in progress.

`/logout <session_name>`
Delete a saved userbot session.
Example: `/logout main`

`/viewsessions`
List all saved userbot sessions and show which one is active.

`/managesessions`
Interactive buttons to set a session active or delete it.

━━━━━━━━━━━━━━━━━━━━
ℹ️ **Notes**

• Bot must be admin with invite permission
• A userbot session must be logged in and active (via /login + /managesessions) for /massapprove to work
• Broadcast runs in background
• Timer controls auto approval delay

━━━━━━━━━━━━━━━━━━━━
"""
