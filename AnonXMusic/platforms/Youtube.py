import os
import yt_dlp
import asyncio
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
import aiohttp

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", None)
COOKIES_FILE = "cookies.txt"


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="

    # ---------------------------
    #   OLD METHOD FOR BOT COMPATIBILITY
    # ---------------------------
    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)
        text = ""
        offset = None
        length = None
        for msg in messages:
            if offset:
                break
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        text = msg.text or msg.caption
                        offset, length = entity.offset, entity.length
                        break
            elif msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset : offset + length]

    # ---------------------------
    #   SEARCH FUNCTION (YT API + fallback)
    # ---------------------------
    async def search(self, query: str):
        # Try YT API first
        if YOUTUBE_API_KEY:
            result = await self.yt_api_search(query)
            if result:
                return result

        # Fallback
        return await self.yt_dlp_search(query)

    async def yt_api_search(self, query: str):
        try:
            api_url = (
                "https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&type=video&maxResults=1&q={query}&key={YOUTUBE_API_KEY}"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    data = await resp.json()
            if "items" not in data or len(data["items"]) == 0:
                return None
            video = data["items"][0]
            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]
            thumbnail = video["snippet"]["thumbnails"]["high"]["url"]

            details_url = (
                "https://www.googleapis.com/youtube/v3/videos"
                f"?part=contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(details_url) as resp:
                    details = await resp.json()

            duration = details["items"][0]["contentDetails"]["duration"]

            return {
                "video_id": video_id,
                "title": title,
                "duration": duration,
                "thumbnail": thumbnail,
            }
        except Exception:
            return None

    async def yt_dlp_search(self, query: str):
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
                "thumbnail": info["thumbnail"],
            }
        except Exception:
            return None

    # ---------------------------
    #   GET STREAM URL
    # ---------------------------
    async def stream(self, video_id: str):
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
            
