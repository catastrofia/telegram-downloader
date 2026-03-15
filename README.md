# 📡 Telegram Media Downloader

Download media (videos, photos, audio, documents) from Telegram channels with flexible naming, filtering, and resume support.

---

## ✨ Features

- **Multi-media support** — download videos, photos, audio, and documents
- **Flexible filtering** — select specific media types or grab everything
- **Multiple naming strategies** — sequential numbering, original filenames, or custom patterns
- **Progress bars** — dual progress display (queue + per-file) via `tqdm`
- **Two-pass approach** — scan first, then download (no surprises)
- **Resume support** — automatically skips already-downloaded files
- **Dry-run mode** — preview what would be downloaded without writing files
- **Secure credentials** — API keys stored in `.env`, never committed to git
- **Fast downloads** — optional `cryptg` C-based crypto acceleration

---

## 📋 Prerequisites

- **Python 3.9+**
- **Telegram API credentials** — get yours at [my.telegram.org/apps](https://my.telegram.org/apps)

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Telegram_downloader.git
cd Telegram_downloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env and fill in your API_ID and API_HASH

# 4. First run — authenticates with Telegram (one-time phone/code prompt)
python telegram_media_downloader.py -c my_channel --dry-run
```

Your `.env` file should look like:

```ini
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=telegram_media_session
DOWNLOAD_DIR=downloads
```

---

## 📖 Usage

### Basic Usage

```bash
# Download all media from a channel (by name)
python telegram_media_downloader.py -c my_channel

# Download from a channel by numeric ID
python telegram_media_downloader.py -c -1001234567890
```

### Filter by Media Type

```bash
# Video only
python telegram_media_downloader.py -c my_channel -t video

# Photos and videos
python telegram_media_downloader.py -c my_channel -t photo video

# Audio only
python telegram_media_downloader.py -c my_channel -t audio
```

Available types: `video`, `photo`, `audio`, `document`, `all` (default).

### File Naming

```bash
# Sequential numbering (default): 001.mp4, 002.jpg, ...
python telegram_media_downloader.py -c my_channel -n sequential

# Sequential with prefix: vacation_001.mp4, vacation_002.jpg, ...
python telegram_media_downloader.py -c my_channel -n sequential --prefix vacation

# Original filenames from Telegram
python telegram_media_downloader.py -c my_channel -n original

# Custom pattern with {n} placeholder: clip_001.mp4, clip_002.jpg, ...
python telegram_media_downloader.py -c my_channel -n custom --pattern "clip_{n}"
```

### Other Options

```bash
# Custom output directory
python telegram_media_downloader.py -c my_channel -o ./my_downloads

# Limit number of files
python telegram_media_downloader.py -c my_channel --limit 50

# Dry run — scan and list files without downloading
python telegram_media_downloader.py -c my_channel --dry-run

# Skip confirmation prompt
python telegram_media_downloader.py -c my_channel -y

# Change zero-padding width (default: 3 → 001, 002, ...)
python telegram_media_downloader.py -c my_channel --padding 4
```

### Finding Channel IDs

Use the included utility to list all your channels and groups with their IDs:

```bash
python channel_id_finder.py
```

Output:

```
Chat Name                                               Channel ID
---------------------------------------------------------------------------
My Favorite Channel                                     -1001234567890
Photography Group                                       -1009876543210
---------------------------------------------------------------------------

Use these IDs with: python telegram_media_downloader.py --channel <ID>
```

---

## 🔧 All CLI Options

| Option | Short | Default | Description |
|---|---|---|---|
| `--channel` | `-c` | *(required)* | Channel name or numeric ID |
| `--type` | `-t` | `all` | Media types to download: `video`, `photo`, `audio`, `document`, `all` |
| `--output` | `-o` | `downloads` | Download directory (overrides `.env` `DOWNLOAD_DIR`) |
| `--naming` | `-n` | `sequential` | Naming strategy: `original`, `sequential`, `custom` |
| `--prefix` | | *(none)* | Prefix for sequential naming (e.g. `vacation`) |
| `--pattern` | | *(none)* | Custom pattern with `{n}` placeholder (e.g. `clip_{n}`) |
| `--padding` | | `3` | Zero-padding width for file numbering |
| `--limit` | | *(none)* | Maximum number of files to download |
| `--dry-run` | | `false` | Scan only — list files without downloading |
| `--yes` | `-y` | `false` | Skip download confirmation prompt |
| `--env` | | `.env` | Path to `.env` configuration file |

---

## 📁 Project Structure

```
Telegram_downloader/
├── telegram_media_downloader.py  # Main CLI entry point
├── channel_id_finder.py          # Utility: list channels with IDs
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for API credentials
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── src/                          # Core modules
│   ├── __init__.py
│   ├── config.py                 # .env loading and validation
│   ├── media.py                  # Media type detection and filtering
│   ├── naming.py                 # File naming strategies
│   └── downloader.py             # Download engine with progress bars
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_config.py            # Tests for config loading
│   ├── test_media.py             # Tests for media classification
│   ├── test_naming.py            # Tests for naming strategies
│   └── test_downloader.py        # Tests for download engine
└── docs/
    └── plans/                    # Development planning documents
```

---

## ⚡ Speed Optimization

Install `cryptg` for significantly faster downloads:

```bash
pip install cryptg
```

`cryptg` provides a C-based implementation of Telegram's MTProto encryption, replacing the slower pure-Python fallback. The downloader automatically detects and uses it when available — you'll see a confirmation message at startup:

```
✅ cryptg (C-based crypto) is installed. Maximum speed potential.
```

If not installed, you'll see a warning with install instructions. The downloader still works without it, just slower.

---

## 🔍 Troubleshooting

| Problem | Solution |
|---|---|
| `API_ID is required` | Create a `.env` file from `.env.example` and fill in your credentials from [my.telegram.org/apps](https://my.telegram.org/apps) |
| `API_ID must be a numeric integer` | Ensure `API_ID` in `.env` is a number, not a string (no quotes needed) |
| `Could not find channel` | Verify the channel name/ID. Use `python channel_id_finder.py` to list available channels |
| `Failed to connect to Telegram` | Check your internet connection and verify `API_ID`/`API_HASH` are correct |
| Phone number / code prompt on every run | This is normal on first run. The session is saved to a `.session` file for future use |
| `cryptg NOT found` warning | Optional — run `pip install cryptg` for faster downloads |
| Downloads are slow | Install `cryptg` (see Speed Optimization above) |
| Files already exist / skipped | Resume support — already-downloaded files are skipped automatically. Delete them to re-download |
| Permission denied on download directory | Ensure you have write access to the output directory, or use `--output` to specify a different one |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
