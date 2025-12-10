import asyncio
import os
import re
from typing import Union

import yt_dlp
from googleapiclient.discovery import build
from pyrogram.types import Message

from AnonXMusic.utils.formatters import time_to_seconds

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Ensure it's in your .env

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.youtube = None
        if YOUTUBE_API_KEY:
            self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def search(self, query: str):
        """Search YouTube for a query using API if available, else fallback to youtubesearchpython."""
        if self.youtube:
            res = self.youtube.search().list(q=query, part="snippet", type="video", maxResults=1).execute()
            items = res.get("items", [])
            if not items:
                return None
            item = items[0]
            vidid = item["id"]["videoId"]
            title = item["snippet"]["title"]
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            return {
                "title": title,
                "vidid": vidid,
                "link": f"https://www.youtube.com/watch?v={vidid}",
                "thumb": thumbnail,
            }
        else:
            # fallback using yt_dlp
            loop = asyncio.get_running_loop()
            def ytdl_search():
                ydl_opts = {"quiet": True, "default_search": "ytsearch1"}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    if "entries" in info:
                        info = info["entries"][0]
                    return {
                        "title": info["title"],
                        "vidid": info["id"],
                        "link": info["webpage_url"],
                        "thumb": info["thumbnail"],
                    }
            return await loop.run_in_executor(None, ytdl_search)

    async def track(self, query_or_link: str, is_link: bool = False):
        """Get track details by URL or search query."""
        if is_link:
            link = query_or_link
        else:
            search_result = await self.search(query_or_link)
            if not search_result:
                return None, None
            link = search_result["link"]

        # yt_dlp for video details
        loop = asyncio.get_running_loop()
        def ytdl_info():
            ydl_opts = {"quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
            duration_min = info.get("duration", 0)
            title = info.get("title")
            vidid = info.get("id")
            thumb = info.get("thumbnail")
            return {
                "title": title,
                "vidid": vidid,
                "link": link,
                "duration_min": duration_min,
                "thumb": thumb,
            }, vidid
        return await loop.run_in_executor(None, ytdl_info)
        
