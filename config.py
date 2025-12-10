import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# Required vars with fallback/defaults
API_ID = int(getenv("API_ID", "35279715"))  # Default dummy, replace in .env
API_HASH = getenv("API_HASH", "b4c339216397b5941d88c8617d2dc12b")
BOT_TOKEN = getenv("BOT_TOKEN", "")

MONGO_DB_URI = getenv("MONGO_DB_URI", "mongodb+srv://knight4563:knight4563@cluster0.a5br0se.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", "60"))
LOGGER_ID = int(getenv("LOGGER_ID", "-1003468243393"))
OWNER_ID = int(getenv("OWNER_ID", "7852340648"))

HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/itzarjuna1/AnonXMusicextras")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "master")
GIT_TOKEN = getenv("GIT_TOKEN")

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/dark_musictm")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/dark_musicsupport")

AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "False").lower() == "true"

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "25"))

TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "104857600"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "1073741824"))

STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2")
STRING3 = getenv("STRING_SESSION3")
STRING4 = getenv("STRING_SESSION4")
STRING5 = getenv("STRING_SESSION5")

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# Image URLs
DEFAULT_IMG = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
START_IMG_URL = getenv("START_IMG_URL", "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg")
PLAYLIST_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
STATS_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
TELEGRAM_AUDIO_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
TELEGRAM_VIDEO_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
STREAM_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
SOUNCLOUD_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
YOUTUBE_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://graph.org/file/88c43dfc225cf46db1792-007008bbe37f49cf84.jpg"

# Time helper
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# URL validation
if SUPPORT_CHANNEL and not re.match(r"^(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - SUPPORT_CHANNEL must start with http(s)://")

if SUPPORT_CHAT and not re.match(r"^(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - SUPPORT_CHAT must start with http(s)://")
