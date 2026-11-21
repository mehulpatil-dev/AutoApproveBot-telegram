<h1 align="center">🤖 Telegram Auto Approve Bot</h1>

<p align="center">
  <img src="https://telegra.ph/file/f394c45e5f2f147a37090.jpg" width="180" alt="Bot Logo">
</p>

<h3 align="center">⚡ An Advanced Telegram Join Request Auto Approval Bot</h3>

<p align="center">
  Automate your Telegram group and channel join requests with ease!
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Pyrogram-orange?style=for-the-badge" alt="Pyrogram">
  <img src="https://img.shields.io/badge/Database-MongoDB-green?style=for-the-badge&logo=mongodb" alt="MongoDB">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status">
</p>

---

## ✨ About The Project

Telegram Auto Approve Bot is a powerful and feature-rich Telegram bot designed to automatically approve incoming join requests in groups and channels.

Built using Python, Pyrogram, and MongoDB, this project comes with an advanced session management system, mass approval functionality, broadcast features, customizable approval timers, and channel statistics.

Whether you manage a single Telegram community or multiple channels, this bot helps simplify your administration tasks.

---

## 🚀 Features

- ⚡ **Automatic Join Approval** – Automatically approves incoming join requests.
- ⏱️ **Custom Approval Timer** – Set a delay before approving requests.
- 👋 **Welcome Messages** – Send personalized welcome messages and animations.
- 📢 **Broadcast System** – Broadcast messages to registered bot users.
- 👥 **Mass Approval** – Process pending join requests using an authorized userbot session.
- 🔐 **Multi-Session Management** – Login, save, activate, and remove multiple userbot sessions.
- 📊 **Channel Statistics** – Track approved users and view daily join statistics.
- 🔔 **Admin Notifications** – Receive notifications about approvals, errors, and bot activities.
- 🛡️ **Force Subscription** – Optionally require users to join a specified channel.
- 📈 **Bot Statistics** – Check registered users, groups, and broadcast status.
- 🗄️ **MongoDB Database** – Store users, groups, timers, and channel statistics.
- 🔄 **Background Tasks** – Run broadcasts without blocking other bot handlers.

---

## 🛠️ Technologies Used

| Technology    | Purpose                          |
|---------------|----------------------------------|
| Python        | Main programming language        |
| Pyrogram      | Telegram MTProto framework       |
| Pyromod       | Interactive Telegram bot features|
| MongoDB       | Database management              |
| AsyncIO       | Asynchronous task processing     |
| Python-Dotenv | Environment configuration        |

---

## 📋 Bot Commands

### 👤 General Commands

| Command  | Description          |
|----------|----------------------|
| `/start` | Start the bot        |
| `/help`  | Display help information |

### ⚙️ Admin Commands

| Command            | Description                          |
|--------------------|--------------------------------------|
| `/stats`           | View bot statistics                  |
| `/fbroadcast`      | Broadcast a replied message          |
| `/settimer`        | Check approval timer status          |
| `/settimer on 300` | Enable a 300-second approval delay   |
| `/settimer off`    | Disable approval delay               |
| `/join`            | Make the userbot join a chat         |
| `/massapprove`     | Approve pending join requests        |
| `/cancelmass`      | Cancel mass approval                 |
| `/login`           | Add a userbot session                |
| `/cancellogin`     | Cancel an ongoing login              |
| `/logout`          | Remove a saved session               |
| `/viewsessions`    | View saved sessions                  |
| `/managesessions`  | Manage active sessions               |
| `/channelshow`     | View channel statistics              |

### Mass Approval Example

```bash
/massapprove -100xxxxxxxxxx
```

With a custom delay:

```bash
/massapprove -100xxxxxxxxxx 2
```

### Session Management Example

```bash
/login main
/viewsessions
/managesessions
/logout main
```

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mehulpatil-dev/AutoApproveBot-telegram.git
```

### 2. Enter the Project Directory

```bash
cd YOUR_REPOSITORY
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project directory:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_id
MONGO=your_mongodb_connection_string
CHANNEL=your_channel_username
FSUB=False
```

> ⚠️ **Keep your credentials private.** Never upload your `.env` file or session strings to GitHub. Add `.env` to your `.gitignore`.

### 5. Run The Bot

```bash
python main.py
```

🎉 Congratulations! Your bot should now be running.

---

## 🔧 Configuration

The bot requires the following configuration variables:

| Variable    | Description                              |
|-------------|------------------------------------------|
| `API_ID`    | Telegram API ID                          |
| `API_HASH`  | Telegram API Hash                        |
| `BOT_TOKEN` | Telegram bot token                       |
| `OWNER_ID`  | Telegram user ID of the owner            |
| `MONGO`     | MongoDB connection URI                   |
| `CHANNEL`   | Force-subscription channel username      |
| `FSUB`      | Enable or disable force subscription (`True` / `False`) |

Where to get them:

- **Telegram API credentials:** [my.telegram.org](https://my.telegram.org)
- **Bot token:** [@BotFather](https://t.me/BotFather)
- **MongoDB database:** [mongodb.com](https://www.mongodb.com/)

---

## 🔑 Required Telegram Permissions

For proper functionality:

1. Add the bot to your group or channel.
2. Promote the bot to administrator.
3. Give it permission to invite users.
4. Enable join requests through your Telegram invite link settings.
5. For mass approval, configure an authorized userbot session and grant it the necessary administrator permissions.

---

## 📁 Project Structure

```text
.
├── main.py
├── new_bot.py
├── bot.py
├── config.py
├── requirements.txt
│
└── plugins/
    ├── __init__.py
    ├── database.py
    ├── session_manager.py
    └── strings.py
```

> Your actual repository may contain additional files.

---

## 🗄️ Database Structure

The bot uses MongoDB to maintain the following collections:

| Collection      | Purpose                      |
|-----------------|------------------------------|
| `users`         | Registered Telegram users    |
| `groups`        | Registered groups            |
| `timer`         | Approval timer configuration |
| `channel_stats` | Channel join statistics      |

---

## ⚠️ Important Notes

- Keep your bot token, API credentials, MongoDB URI, and userbot session strings private.
- Do not share your userbot session with anyone.
- Use the bot only in groups and channels you administer or are authorized to manage.
- Telegram API flood limits may affect mass approval and broadcast operations.
- Ensure your bot has the required administrator permissions.
- Back up your MongoDB database regularly.

---

## ❤️ Support & Updates

If you like this project:

- ⭐ Give this repository a star.
- 🍴 Fork the repository.
- 🐛 Report bugs through GitHub Issues.
- 💡 Suggest new features.

---

## 👨‍💻 Developer

<p align="center">
  <b>Made with ❤️ using Python and Pyrogram by Mehul</b>
</p>

<p align="center">
  <i>Automate your Telegram community management! 🚀</i>
</p>

<p align="center">
  ⭐ Don't forget to star this repository if you find it useful!
</p>
