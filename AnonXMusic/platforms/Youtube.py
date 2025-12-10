import os
import yt_dlp
import aiohttp

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", None)
COOKIES_FILE = "cookies.txt"  # keep your cookies file here


# -------------------------------
#  YT API SEARCH (PRIMARY METHOD)
# -------------------------------
async def yt_api_search(query):
    if not YOUTUBE_API_KEY:
        return None

    api_url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&maxResults=1&q={query}&key={YOUTUBE_API_KEY}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()

        if "items" not in data or len(data["items"]) == 0:
            return None

        video = data["items"][0]
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        thumbnail = video["snippet"]["thumbnails"]["high"]["url"]

        # Get video details
        details_url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(details_url) as resp:
                details = await resp.json()

        if "items" not in details:
            return None

        duration = details["items"][0]["contentDetails"]["duration"]

        return {
            "video_id": video_id,
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail
        }

    except Exception:
        return None  # API failed → fallback


# ---------------------------------
#  YT-DLP SEARCH (FALLBACK METHOD)
# ---------------------------------
async def yt_dlp_search(query):
    try:
        ydl_opts = {
            "quiet": True,
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            "format": "bestaudio/best",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]

        return {
            "video_id": info["id"],
            "title": info["title"],
            "duration": info["duration"],
            "thumbnail": info["thumbnail"]
        }

    except Exception:
        return None


# -------------------------------
#  COMBINED SEARCH FUNCTION
# -------------------------------
async def search_youtube(query):
    # 1️⃣ try API key
    if YOUTUBE_API_KEY:
        api_result = await yt_api_search(query)
        if api_result:
            return api_result

    # 2️⃣ fallback to cookies / ytdlp
    return await yt_dlp_search(query)


# ------------------------------------
#  GET ACTUAL STREAM URL USING YT-DLP
# ------------------------------------
async def fetch_stream(video_id):
    try:
        ydl_opts = {
            "quiet": True,
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            "format": "bestaudio/best",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)
        return info["url"]

    except Exception:
        return None
        
