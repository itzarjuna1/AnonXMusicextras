import os
import re
import asyncio
from typing import Union
import yt_dlp
from googleapiclient.discovery import build
from pyrogram.types import Message
from config import YOUTUBE_API_KEY
from AnonXMusic.utils.formatters import time_to_seconds


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://www.youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

    async def track(self, query: str, videoid: bool = False):
        """
        Returns track details using YouTube API first, then fallback to yt-dlp.
        """
        if videoid:
            query = self.base + query
        # Try YouTube API first
        if self.youtube:
            try:
                search_response = self.youtube.search().list(
                    q=query, part="snippet", maxResults=1, type="video"
                ).execute()
                item = search_response["items"][0]
                vidid = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                duration_min = None  # We'll fetch real duration with yt-dlp
                # Get duration with yt-dlp
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--skip-download",
                    "-j",
                    f"https://www.youtube.com/watch?v={vidid}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                import json
                info = json.loads(stdout.decode())
                duration_min = info.get("duration") or None
                duration_sec = int(duration_min) if duration_min else 0
                yturl = f"https://www.youtube.com/watch?v={vidid}"
                return {
                    "title": title,
                    "link": yturl,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }, vidid
            except Exception:
                pass  # fallback

        # Fallback to yt-dlp search
        loop = asyncio.get_running_loop()
        def ytdlp_search():
            ydl_opts = {"quiet": True, "format": "bestaudio"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
                return result
        try:
            info = await loop.run_in_executor(None, ytdlp_search)
            vidid = info["id"]
            title = info["title"]
            thumbnail = info["thumbnail"]
            duration_min = info["duration"]
            yturl = f"https://www.youtube.com/watch?v={vidid}"
            return {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }, vidid
        except Exception as e:
            return None, None

    async def video(self, link: str):
        """
        Returns direct video/audio URL using yt-dlp.
        """
        loop = asyncio.get_running_loop()
        def ytdl_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "nocheckcertificate": True,
                "geo_bypass": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                url = info["url"]
                return url
        try:
            return await loop.run_in_executor(None, ytdl_dl)
        except Exception:
            return None
            
