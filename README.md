<h1 align="center"><b>Friday</b></h1>
<p align="center"><img src="Main/assets/images/logo.png" width="1155px"><br></p>

<p align="center">
  <b>A high-performance, modular Telegram UserBot and Assistant Bot engine built on Telethon & modern asynchronous Python.</b><br>
  <i>Adapted from <a href="https://github.com/Altruix/Altruix">Altruix</a></i>
</p>

<p align="center">
  <a href="https://github.com/DevsExpo/Friday"><img src="https://img.shields.io/badge/Friday-v2.0-007ACC.svg?style=flat-square&logo=telegram" alt="Friday Version"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/LonamiWebs/Telethon"><img src="https://img.shields.io/badge/Telethon-Async-blue.svg?style=flat-square" alt="Telethon"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-green.svg?style=flat-square" alt="License"></a>
  <a href="https://t.me/FridayUB"><img src="https://img.shields.io/badge/Channel-@FridayUB-red.svg?style=flat-square&logo=telegram" alt="Channel"></a>
  <a href="https://t.me/FridayChat"><img src="https://img.shields.io/badge/Community-@FridayChat-blue.svg?style=flat-square&logo=telegram" alt="Support Chat"></a>
</p>

---

## ⚡ Highlights & Capabilities

* **Dual-Engine Operation**: Seamlessly pairs **Telethon StringSessions** (Userbot) with an interactive **Telegram Bot Token** (Assistant Bot) under a single unified process.
* **FPM v3 (Friday Package Manager)**: Hot-install, update, and segregate third-party plugin suites directly from GitHub repositories without touching core code.
* **Universal Database**: Zero-config local SQLite persistence (`friday.db`) out of the box, with seamless high-throughput MongoDB and PostgreSQL support.
* **Multi-Session Multi-Client**: Run and manage multiple user sessions concurrently from a single instance.

---

## 🚀 Quick Start & Workflow

Getting Friday up and running requires only a few minimal credentials and takes under 2 minutes.

### 📋 Minimum Required Credentials

To start Friday, you only need **two things**:

1. **`API_ID` & `API_HASH`**:
   - Go to [my.telegram.org](https://my.telegram.org).
   - Log in with your phone number and navigate to **API development tools**.
   - Create a new app (you can enter any app title and short name) to obtain your **API ID** (integer) and **API Hash** (32-character hex string).

2. **`BOT_TOKEN`**:
   - Open Telegram and search for [@BotFather](https://t.me/BotFather).
   - Send `/newbot`, choose a display name, and a unique username ending in `bot` (e.g. `MyFridayAssistant_bot`).
   - Copy the HTTP API token provided by BotFather (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

> ⭐ **Recommended: MongoDB (`DB_URI`)**  
> While Friday defaults to embedded SQLite (`friday.db`) for zero-config local testing, **MongoDB Atlas (Cloud)** is strongly recommended for production, Docker, and cloud hosts (Render, Railway, Heroku, VPS). A cloud database ensures your StringSessions, custom settings, filters, and PM permits survive serverless container restarts and redeployments. Free tier clusters are available at [mongodb.com/atlas](https://www.mongodb.com/atlas).

---

### 🤖 100% In-Telegram Setup via Assistant Bot (Easiest Method)

You do **not** need to manually generate or paste a `SESSIONS` string beforehand. Friday features a **Training Wheels Protocol (TWP)** that lets you configure everything directly inside Telegram:

1. **Start Friday** with just `API_ID`, `API_HASH`, and `BOT_TOKEN` (and optionally `DB_URI`) in your `.env` or container environment.
2. **Open your Assistant Bot in Telegram** and send `/start`.
3. **Step 1: Database Setup**:
   - Tap **☁️ MongoDB Atlas (Cloud)** (or SQLite / PostgreSQL).
   - Paste your MongoDB connection string when prompted. Friday tests the connection, sets up namespaces, and switches live without a restart.
4. **Step 2: Account Login (Userbot Activation)**:
   - Tap **📱 Quick Login (with Secure NumPad)**.
   - Enter your phone number when prompted.
   - Enter your Telegram login code using the interactive numeric keypad buttons directly in Telegram. If you have Two-Step Verification (2FA), enter your password.
5. **Done!** Friday generates your StringSession, saves it securely to your database, and starts your userbot client immediately.

---

### 🛠 Alternative Setup Methods

#### Option A: Interactive CLI Setup Wizard
Run the terminal-based interactive wizard that prompts for credentials, generates StringSessions, and writes `.env` automatically:

```bash
# Clone the repository
git clone https://github.com/DevsExpo/Friday.git
cd Friday

# Install dependencies
python -m pip install -e .

# Launch configuration wizard
python -m Main.scripts.wizard
```

#### Option B: Manual `.env` File
1. Copy the example configuration template:
   ```bash
   cp example.env .env
   ```
2. Open `.env` and fill in your minimal credentials:
   ```env
   API_ID=1234567
   API_HASH=abcdef0123456789abcdef0123456789
   BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   DB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"  # Recommended
   ```
3. Start Friday:
   - **Windows**: Double-click `start.bat` or run `py -3 -m Main`
   - **Linux / macOS**: Run `./start.sh` or `python3 -m Main`

---

## 👥 Multi-Session & Multi-Account Support

Friday is built from the ground up with **native multi-client parallelism**. You can run and manage multiple Telegram accounts simultaneously under a single Friday process:

- **Adding Multiple Accounts**: Simply add space-separated Telethon StringSessions to the `SESSIONS` variable in `.env`:
  ```env
  SESSIONS="1BJWap1wAccountOne... 1BJWap2xAccountTwo... 1BJWap3yAccountThree..."
  ```
- **Shared Ecosystem**: All connected accounts share the same database, custom command prefix, FPM package manager, and plugins.
- **Dynamic Session Management**: You can also add or view active accounts directly on the fly via the Assistant Bot's interactive menu (`/add`, `/session`, or `/panel`).

---

## 🎛 Interactive Settings Panel (`/settings` or `/panel`)

Friday includes a rich Telegram inline Control Center for both the Assistant Bot and Userbot:

- **Assistant Bot Command**: Send `/settings` or `/panel` in private to your assistant bot.
- **Userbot Command**: Send `.settings` or `.panel` in any chat.

### Control Center Capabilities:
* **🛡️ PM Security**: Toggle PM anti-spam / permit system on or off with 1 click.
* **📊 Progress Bar**: Switch between live ASCII progress bars and silent clean transfers to prevent Telegram flood limits.
* **➕ Account Manager**: View active sessions and connect new Telegram accounts on the fly.
* **🗄️ Database Inspector**: Real-time status for SQLite, MongoDB, or PostgreSQL.
* **🔄 Maintenance & Health**: Real-time CPU/RAM stats, latency checks, and 1-click live bot restarts.

---

## ⚙️ Configuration Reference

| Variable | Required? | Default | Description |
|---|:---:|---|---|
| `API_ID` | **Yes** | — | Telegram App API ID obtained from [my.telegram.org](https://my.telegram.org/apps). |
| `API_HASH` | **Yes** | — | Telegram App API Hash obtained from [my.telegram.org](https://my.telegram.org/apps). |
| `SESSIONS` | Optional | `[]` | One or more space-separated Telethon StringSessions for multi-account userbot (can also be registered live via the Assistant Bot). |
| `BOT_TOKEN` | **Yes** | `None` | Telegram Bot Token from [@BotFather](https://t.me/BotFather) for assistant & inline controls. |
| `OWNER_ID` | Optional | `None` | Telegram User ID of the primary owner (obtain via [@MissRose_Bot](https://t.me/MissRose_Bot) `/id`). |
| `DB_URI` | Optional | `sqlite:///friday.db` | Database connection URI. Supports SQLite (`sqlite:///friday.db`), MongoDB (`mongodb+srv://`), or PostgreSQL (`postgresql://`). |
| `DB_NAME` | Optional | `Friday` | Database collection namespace name. |
| `CMD_HANDLER` | Optional | `.` | Command prefix for userbot commands (e.g. `.help`, `.ping`). |
| `SUDO_CMD_HANDLER` | Optional | `!` | Command prefix for authorized sudo operators. |
| `SUDO_USERS` | Optional | `[]` | List of trusted user IDs permitted to invoke bot commands. |
| `LOG_CHAT_ID` | Optional | `None` | Private Telegram chat or channel ID where bot logs and tracebacks are relayed. |
| `LOAD_XTRA_PLUGINS` | Optional | `true` | Automatically clone and load plugins from `XTRA_PLUGINS_REPOS`. |
| `XTRA_PLUGINS_REPOS` | Optional | `DevsExpo/XtraPlugins` | Comma/space-separated repository URLs for external plugin suites. |

### Complete `.env` Template:
```env
# Core Telegram Credentials (Required)
API_ID=1234567
API_HASH=abcdef0123456789abcdef0123456789
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
SESSIONS="1BJWap1wBu..."
OWNER_ID=987654321

# Bot Prefixes & Handlers
CMD_HANDLER="."
SUDO_CMD_HANDLER="!"
SUDO_USERS=""

# Database Backend (Zero-config SQLite by default)
DB_URI="sqlite:///friday.db"
DB_NAME="Friday"

# Logging & Extra Plugins
LOG_CHAT_ID=
DEBUG=false
LOAD_XTRA_PLUGINS=true
XTRA_PLUGINS_REPOS="https://github.com/DevsExpo/XtraPlugins"
```

---

## 🗄️ Multi-Database Support (SQLite, MongoDB, & PostgreSQL)

Friday features a **Universal Database Layer** powered by `PyMongoInstructionParser`. You can write standard async MongoDB syntax (`find()`, `find_one()`, `insert_one()`, `update_one()`, `delete_many()`, `$set`, `$inc`, `$push`) and Friday automatically routes and translates queries to your chosen backend:

| Backend | `DB_URI` Format | Best For | Prerequisites |
|---|---|---|---|
| **SQLite (SQL)** *(Default)* | `sqlite:///friday.db` *(or leave empty)* | Single-server / VPS deployments & local testing | Built-in (zero-config, works out of the box) |
| **MongoDB (NoSQL)** | `mongodb+srv://user:pass@cluster.mongodb.net/` | Scalable cloud database (MongoDB Atlas) | Running MongoDB cluster |
| **PostgreSQL (SQL)** | `postgresql://user:pass@host:5432/dbname` | High-concurrency production deployments (Supabase, Neon) | Running PostgreSQL instance |

### How It Works Under The Hood:
1. **Auto-Detection:** When Friday boots, `create_database(DB_URI)` detects the connection scheme.
2. **Transparent Query Translation:** For SQL databases (PostgreSQL & SQLite), `PyMongoInstructionParser` compiles MongoDB query dicts and update operators directly into optimized parameterized SQL statements (`SELECT data FROM table WHERE ...`), storing documents as indexed JSON objects.
3. **Async Cursor Parity:** Cursors across all backends implement standard async iteration (`async for item in col.find({...}):`), ensuring 100% plugin compatibility without writing backend-specific SQL.

---

## 📦 Friday Package Manager (FPM v3)

Friday features a built-in package manager that installs, segregates, and updates modular plugins dynamically from GitHub without modifying core code.

### Installing Plugins
```text
# Install a full plugin suite
.fpm_install https://github.com/username/my-plugin

# Install only specific segregated subcategories
.fpm_install https://github.com/username/XtraPlugins -sub media,utilities

# Persist package across bot restarts
.fpm_install -ios https://github.com/username/my-plugin
```

### Managing Subcategories & Packages
```text
# List all installed plugins and active subcategories
.fpm_list

# Inspect segregated subcategories of an installed plugin
.fpm_sub XtraPlugins

# Enable a specific subcategory on the fly
.fpm_enable XtraPlugins media

# Disable a subcategory without deleting files
.fpm_disable XtraPlugins shopping

# Update an installed plugin to its latest GitHub release
.fpm_update my-plugin

# Uninstall and purge a plugin
.fpm_uninstall my-plugin
```

### Diagnostics & Self-Healing
```text
# Run a full health audit of all plugins and Python dependencies
.fpm_doctor

# 1-click batch repair of any missing packages
.fpm_repair
```

> 📖 **Developer Guide**: For creating custom plugins, decorator specifications, subcategory manifests, and database models, read the [Full Plugin Developer Guide](docs/PLUGIN_GUIDE.md).

---

## 🗂 Project Structure

```text
Friday/
├── Main/
│   ├── core/                  # Core client, FPM v3, database engine, decorators, types
│   │   ├── client.py          # FridayClient engine & Telethon session orchestrator
│   │   ├── plugin_manager.py  # FPM v3 plugin lifecycle, subcategories & quarantine
│   │   ├── fpm_env_setup.py   # Pre-boot dependency verification & batch resolver
│   │   ├── database.py        # MongoDB & Local JSON storage abstractions
│   │   └── types/             # Telethon Message and Client enriched subclasses
│   ├── plugins/
│   │   ├── userbot/           # Built-in userbot commands (.ping, .eval, .fpm, etc.)
│   │   ├── bot/               # Built-in assistant bot commands (/start, /help, callbacks)
│   │   └── external/          # Dynamically installed FPM plugins & manifests
│   ├── internals/             # System utilities, settings, session manager
│   ├── localization/          # Multi-language string catalogs (en, hi, te, bn)
│   └── scripts/               # Session generator, cleanup, maintenance utilities
├── docs/                      # Architectural specifications & Plugin Developer Guide
├── requirements.txt           # Minimal core framework dependencies
├── external_requirements.txt  # Optional unified requirements for external plugin suites
└── example.env                # Template configuration file
```

---

## 👥 Credits & Acknowledgments

* **[Altruix](https://github.com/Altruix/Altruix)**: Framework architecture adapted from Altruix.
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

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.
