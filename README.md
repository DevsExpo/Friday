<h1 align="center"><b>Friday</b></h1>
<p align="center"><img src="Main/assets/images/logo.png" width="1155px" alt="Friday Logo"><br></p>

<p align="center">
  <b>A modern, high-performance, modular Telegram Userbot and Assistant Bot framework powered by Telethon & asynchronous Python.</b><br>
  <i>Built with base architecture from <a href="https://github.com/Altruix/Altruix">Altruix</a>.</i>
</p>

<p align="center">
  <a href="https://github.com/DevsExpo/Friday"><img src="https://img.shields.io/badge/Friday-v2.0-007ACC.svg?style=flat-square&logo=telegram" alt="Friday Version"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/LonamiWebs/Telethon"><img src="https://img.shields.io/badge/Telethon-Async-blue.svg?style=flat-square" alt="Telethon"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPLv3-green.svg?style=flat-square" alt="License"></a>
  <a href="https://t.me/FridayReborn"><img src="https://img.shields.io/badge/Community-@FridayReborn-blue.svg?style=flat-square&logo=telegram" alt="Support Chat"></a>
</p>

---

## ⚡ The Simplest Setup: 3 Bare-Minimum Variables

Setting up Friday is ridiculously easy. You **do not** need to pre-generate complex string sessions, deal with confusing terminal login scripts, or configure complicated external cloud databases.

To get started, you only need **three bare-minimum variables**:

```env
API_ID=1234567
API_HASH=abcdef0123456789abcdef0123456789
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

* **No String Session Required in `.env`**: Don't have a Telethon string session yet? Leave `SESSIONS` empty!
* **No Database Required in `.env` (Zero-Config, but Cloud DB Recommended)**: Leave `DB_URI` empty, and Friday automatically falls back to an embedded, zero-config local SQLite database (`sqlite:///friday.db`).
  > 💡 **Recommendation**: While `DB_URI` is not required for local/VPS machines, providing a persistent external database (such as **MongoDB Atlas** or **PostgreSQL / Supabase**) is **strongly recommended** for cloud, containerized, or ephemeral hosts (Docker, Heroku, Render, Koyeb, Railway) so your sessions, filters, and settings survive container redeployments and restarts.
* **Everything else can be configured directly from Telegram via the Assistant Bot!**

---

## 🤖 The Assistant Bot: Interactive GUI & Setup Wizard

Friday is built on a **Dual-Engine Architecture** where an interactive **Assistant Bot** (`BOT_TOKEN`) and the **Telethon Userbot** run side-by-side in a single unified asynchronous process. They share the same event loop, memory cache, database layer, and configuration.

When you boot Friday with just the 3 bare-minimum variables, it activates the **Training Wheels Protocol (TWP)**:

### 1. Zero-Friction Telegram Onboarding
1. Run `python -m Main` with your `API_ID`, `API_HASH`, and `BOT_TOKEN`.
2. Open Telegram and send `/start` to your Assistant Bot.
3. Friday automatically locks ownership to you to prevent hijacking.
4. An interactive setup wizard guides you step-by-step:
   * **Step 1 (Database)**: Choose the built-in **SQLite** storage with one tap, or easily plug in **MongoDB Atlas** or **PostgreSQL / Supabase** by sending the connection URI.
   * **Step 2 (Account Login)**:
     * **📱 Quick Login with Secure NumPad**: Enter your phone number directly in Telegram. When Telegram delivers your login code, use the bot's interactive inline NumPad to enter the digits safely (bypassing Telegram's automatic code cancellation when reading plain-text messages).
     * **📋 Paste Existing Session**: If you already have a Telethon `StringSession`, just paste it into the bot.
5. The Assistant Bot validates your credentials, encrypts and stores the session directly into your chosen database, and dynamically attaches the userbot client on the fly—**no server restarts needed!**

---

## 🤝 Assistant Bot & Userbot Synergy

The Assistant Bot is not just a helper—it acts as a 24/7 interactive control center and visual heads-up display for your userbot:

* **🎛️ Interactive Control Panel (`/panel`, `/settings`, `.panel`)**:
  * Real-time server resource monitoring (CPU, RAM, Process Uptime, Telegram Data Center).
  * 1-tap toggles for **PM Security** and **Upload Progress Bar**.
  * Multi-account inspector to review active sessions, check DC locations, or safely log out.
  * Direct restart and ping diagnostics.
* **🛡️ PM Security Inline Sentinel**:
  * When a stranger sends you a direct message, your userbot holds them in check while your Assistant Bot sends an inline notification to your private control room with 1-tap **Approve**, **Disapprove**, and **Block** buttons.
* **📖 Interactive Command Browser (`/help` or `.help`)**:
  * Browse every installed plugin by category with snappy inline pagination, dynamic parameter guides, and copyable examples.
* **📦 FPM (Friday Package Manager) Inline Explorer**:
  * Search, review descriptions, toggle subcategories, and manage plugins directly via Telegram inline keyboards.
* **🤫 Secret Whisper Engine (`@YourBot @username secret`)**:
  * Send end-to-end masked whisper messages in public groups that only the designated recipient can decrypt by clicking an inline button.
* **👥 Sudo Delegation Control**:
  * Add, remove, and manage trusted operators with restricted permission sets from inline buttons.

---

## 🚀 Quick Start Guide

### Step 1: Clone & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/DevsExpo/Friday.git
cd Friday

# Copy the environment file template
cp example.env .env

# Install dependencies in editable mode
python -m pip install -e .
```

### Step 2: Configure the 3 Essentials in `.env`
Edit `.env` using your favorite text editor:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_assistant_bot_token
```
*(Get `API_ID` & `API_HASH` from [my.telegram.org](https://my.telegram.org/apps) and `BOT_TOKEN` from [@BotFather](https://t.me/BotFather))*

### Step 3: Run Friday
```bash
python -m Main
```
Open Telegram, send `/start` to your bot, and follow the on-screen setup wizard!

---

## 🗄️ Multi-Database Architecture

Friday features a **Universal Database Layer** powered by `PyMongoInstructionParser`. You can write standard async MongoDB syntax (`find()`, `find_one()`, `insert_one()`, `update_one()`, `delete_many()`, `$set`, `$inc`, `$push`) and Friday automatically routes and translates queries to your chosen backend:

| Backend | `DB_URI` Format | Description | Prerequisites |
|---|---|---|---|
| **SQLite (Default)** | `sqlite:///friday.db` *(or blank)* | Embedded local SQL storage. Zero-config, perfect for VPS and local environments. | None (built-in) |
| **MongoDB (NoSQL)** | `mongodb+srv://user:pass@cluster.mongodb.net/` | Scalable cloud database for distributed setups. | MongoDB Atlas cluster |
| **PostgreSQL (SQL)** | `postgresql://user:pass@host:5432/dbname` | High-concurrency production deployments (Supabase, Neon). | PostgreSQL instance |

---

## 🛠️ Complete Feature & Command Reference

Every single plugin and module included in Friday is listed below:

### 1. ⚙️ Core & System Controls
| Command | Description |
|---|---|
| `.alive` / `.ialive` | Display real-time system status, active sessions count, uptime, and framework version. |
| `.ping` / `.lping` | Measure MTProto latency between your server and Telegram data centers with microsecond accuracy. |
| `.panel` / `.settings` / `/panel` | Open the full interactive GUI control center with system gauges and 1-tap toggles. |
| `.sethandler <prefix>` | Dynamically change userbot command prefix (e.g. `.`, `!`, `,`) without restart. |
| `.setsudohandler <prefix>` | Change the prefix for authorized sudo operators. |
| `.gethandler` / `.resethandler` | View active prefix or restore default (`.`). |
| `.addsudo` / `.rmsudo` / `.sudolist` | Grant or revoke delegated command access to trusted users with restricted permissions. |
| `.eval` / `.exec` / `.py` | Asynchronously execute and evaluate Python expressions with live output streaming. |
| `.bash` / `.sh` / `.terminal` | Run bash / shell terminal commands directly from Telegram. |
| `.restart` / `.reload` / `.shutdown` | Hot-reload all modules, restart the Friday process, or terminate gracefully. |
| `.update` | Fetch latest upstream Git updates and auto-reboot. |

### 2. 👥 Multi-Account & Session Management
| Command | Description |
|---|---|
| `.sessions` | List all active Telegram userbot accounts, names, IDs, and connection status. |
| `.add_session <session>` | Add another user account dynamically on the fly to run concurrent userbots. |
| `.rm_session <index>` | Safely disconnect an account and remove its credentials from the database. |
| `.switch_session <index>` | Switch the primary responding userbot client. |
| `.whoami` | Inspect active account profile, session details, and Telegram Data Center (DC) info. |

### 3. 🛡️ PM Security & Privacy Shield
| Command | Description |
|---|---|
| `.pmpermit <on/off>` | Enable or disable the incoming Direct Message (PM) antispam firewall. |
| `.allow` / `.disallow` | Manually permit or revoke a user's right to message your PM. |
| `.block` | Block and report a user directly from PM or chat reply. |
| `.setpmmsg <text/reply>` | Customize the automatic warning notice sent to unapproved PM contacts. |
| `.getpmmsg` / `.resetpmmsg` | View the active PM warning message or restore default template. |
| `.setpmlimit <number>` | Set maximum spam warning attempts allowed before auto-blocking. |
| `.getpmlimit` | Check current spam limit threshold. |
| *Inline PM Notification* | Assistant Bot pings you with inline **Approve / Disapprove / Block** buttons when strangers message you. |

### 4. 📦 Friday Package Manager (FPM) & Official [XtraPlugins](https://github.com/DevsExpo/XtraPlugins)

Friday features a built-in modular package manager that hot-installs, isolates, and updates external plugin suites directly from GitHub without modifying core code. It natively connects to the official [XtraPlugins](https://github.com/DevsExpo/XtraPlugins) repository.

| Command | Description |
|---|---|
| `.fpm_install <repo_url>` | Install complete third-party plugin suites (e.g. `.fpm_install https://github.com/DevsExpo/XtraPlugins`). |
| `.fpm_install <url> -sub <cats>` | Install only specific segregated plugin subcategories (e.g. `-sub media,utils`). |
| `.fpm_install -ios <repo_url>` | Persist installed packages permanently across reboots. |
| `.fpm_uninstall <plugin>` | Completely remove and purge an installed plugin suite. |
| `.fpm_update <plugin>` | Pull the latest updates for an installed plugin repository. |
| `.fpm_list` | List all installed plugins, active modules, and segregated subcategories. |
| `.fpm_enable <repo> <subcat>` | Dynamically activate a disabled subcategory on the fly. |
| `.fpm_disable <repo> <subcat>`| Deactivate a subcategory without deleting its source code. |
| `.fpm_doctor` | Run comprehensive health diagnostics on all installed plugins and dependencies. |
| `.fpm_repair` | 1-click automated batch resolver to install any missing plugin requirements. |
| `.fpm_quarantine` | Isolate malfunctioning or security-flagged plugins safely. |
| `.fpm_reload` | Hot-reload all external FPM plugins in memory. |

### 5. 👥 Group Administration & Moderation
| Command | Description |
|---|---|
| `.kick` / `.ban` / `.unban` | Kick or ban users from groups by reply or username/ID. |
| `.mute` / `.unmute` | Restrict users from sending messages in supergroups. |
| `.promote` / `.demote` | Grant custom administrator rights or demote admins. |
| `.zombies` | Scan for and clean deleted accounts (ghost/zombie accounts) in 1 tap. |
| `.adminlist` | List all administrators in the current group with custom titles and status. |
| `.purge` / `.purgeme` | Fast-purge messages up to the replied message, or delete only your own messages. |
| `.del` / `.edit <text>` | Delete or edit replied messages cleanly. |
| `.pin` / `.unpin` | Pin or unpin messages silently or with member notifications. |
| `.mentionall` / `.tagall` | Mention group members in small rate-controlled batches for urgent announcements. |
| `.cancel` | Abort an ongoing mention/tag sequence immediately. |
| `.join <link>` / `.leave` | Join public/private chats via invite link, or leave current group cleanly. |
| `.createchannel` / `.creategroup`| Create new public or private channels and groups instantly. |
| `.setchatphoto` / `.setchattitle` | Update group photo or title by reply or text. |

### 6. 🤖 Automation, Filters & Greetings
| Command | Description |
|---|---|
| `.filter <keyword> <reply>` | Set automated keyword auto-responders supporting formatted text, media, and buttons. |
| `.stop <keyword>` / `.stopall` | Stop specific triggers or clear all active chat filters. |
| `.filters` | List all active automated filters in the current chat. |
| `.setwelcome <reply>` | Set automated welcome greeting with dynamic `{mention}`, `{chat}`, and `{count}` tags. |
| `.getwelcome` / `.clearwelcome`| Inspect current welcome message or disable automated greetings. |
| `.addblacklist <word>` | Blacklist forbidden words/phrases; triggers auto-deletion of offending messages. |
| `.rmblacklist` / `.listblacklist` | Remove words or view all blacklisted patterns in chat. |
| `.clearblacklist` | Clear the entire blacklist for the chat. |
| `.react <emoji>` / `.autoreact`| Add emoji reactions to messages, or automatically react to target users. |

### 7. 🎨 Stickers, Media & Aesthetics
| Command | Description |
|---|---|
| `.kang` | "Kang" any photo, sticker, animated TGS, or video sticker into your personal sticker pack. |
| `.packinfo` | Inspect sticker pack metadata, author, and item count. |
| `.getsticker` | Convert any sticker into a downloadable high-resolution PNG image. |
| `.round` | Convert square videos into circular Telegram video notes. |
| `.carbon` | Generate beautiful source code images via Carbon (carbon.now.sh) from text or code files. |
| `.quotly` / `.q` | Turn replied messages into sleek Quotly stickers. |
| `.spoiler` | Format replied media or text behind a Telegram spoiler curtain. |

### 8. ☁️ Cloud, AI & Everyday Utilities
| Command | Description |
|---|---|
| `.tts <lang> <text>` | Convert text into natural speech voice notes using Google Text-to-Speech (TTS). |
| `.translate <lang> <text>` | Translate text across 100+ languages in real time. |
| `.reverse` | Perform reverse Google image search from replied photo or sticker. |
| `.qr <text>` / `.decodeqr` | Generate QR codes from text, or decode QR codes from replied images. |
| `.shorturl <url>` | Shorten lengthy URLs into clean redirect links. |
| `.google <query>` | Search Google and return top search results directly in chat. |
| `.paste` / `.pasty` / `.bin` | Upload text or script files to pastebins (Spacebin, Nekobin) with syntax highlighting. |
| `.download` / `.upload <path>` | Download Telegram media to local disk, or upload local files to chat with progress bar. |
| `.ls` / `.rm <path>` | List local files or delete files from the host server. |
| `.whois` / `.info` / `.id` | Deep inspection of user profiles: ID, Data Center (DC), common groups, bio, and badges. |

### 9. 📢 Broadcast & Stealth Messaging
| Command | Description |
|---|---|
| `.gcast <text/reply>` | Broadcast a message to all groups and supergroups you have joined. |
| `.pcast <text/reply>` | Broadcast a message to all open private conversations. |
| `.bcast <text/reply>` | General broadcast across your entire dialogue list with rate-limiting protection. |
| `.whisper <@user> <message>`| Send inline encrypted whisper messages that only the tagged recipient can open. |
| `.afk <reason>` | Enter Away-From-Keyboard mode with custom auto-reply for mentions and direct messages. |
| `.unafk` | Return from AFK mode and view an organized summary list of all mentions received while away. |

---

## 🗂 Project Structure

```text
Friday/
├── Main/
│   ├── core/                  # Core client, FPM, database engine, decorators, types
│   │   ├── client.py          # FridayClient orchestrator (Userbot + Assistant Bot)
│   │   ├── plugin_manager.py  # FPM plugin lifecycle, subcategories & quarantine
│   │   ├── fpm_env_setup.py   # Pre-boot dependency verification & batch resolver
│   │   ├── database.py        # Universal Database layer (SQLite, MongoDB, PostgreSQL)
│   │   └── types/             # Telethon Message and Client enriched subclasses
│   ├── plugins/
│   │   ├── userbot/           # 29 built-in userbot command suites (.ping, .eval, .fpm, etc.)
│   │   ├── bot/               # 10 built-in assistant bot interactive GUI modules (/start, /panel)
│   │   └── external/          # Dynamically installed FPM plugins & manifests
│   ├── internals/             # TWP setup wizard, interactive NumPad login, settings
│   ├── localization/          # Multi-language string catalogs (en, hi, te, bn)
│   ├── utils/                 # Centralized UI tokens, helpers, file utils, progress bar
│   └── scripts/               # Session generator, cleanup, maintenance utilities
├── docs/                      # Architectural specifications & Plugin Developer Guide
├── requirements.txt           # Minimal core framework dependencies
├── example.env                # Template configuration file
└── pyproject.toml             # Build system & pytest configuration
```

---

## 👥 Credits & Acknowledgments

* **Altruix**: Built from the base architecture of [Altruix](https://github.com/Altruix/Altruix).
* **XtraPlugins**: Official extended modular plugin ecosystem powered by [DevsExpo/XtraPlugins](https://github.com/DevsExpo/XtraPlugins).
* **Telethon**: Pure Python MTProto library created by [LonamiWebs](https://github.com/LonamiWebs/Telethon).
* **Friday Contributors**: Built and maintained with contributions from:
  * [EverythingSuckz](https://github.com/EverythingSuckz)
  * [DevsExpo](https://github.com/DevsExpo)
  * [BilakshanP](https://github.com/BilakshanP)
  * [Reeshuxd](https://github.com/Reeshuxd)
  * [Rohith-Sreedharan](https://github.com/Rohith-Sreedharan)
  * [StarkBotIndustries](https://github.com/StarkBotIndustries)
  * [sohag02](https://github.com/sohag02)
  * [SHRE-YANSH](https://github.com/SHRE-YANSH)
  * [lostb053](https://github.com/lostb053)
  * [Nksama](https://github.com/Nksama)
  * [Crackexy](https://github.com/Crackexy)
  * [anonyindian](https://github.com/anonyindian)
  * [N0BLEWOLF](https://github.com/N0BLEWOLF)
  * [ramanveerji](https://github.com/ramanveerji)
  * [swatv3nub](https://github.com/swatv3nub)

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPLv3). See the [LICENSE](LICENSE) file for details.
