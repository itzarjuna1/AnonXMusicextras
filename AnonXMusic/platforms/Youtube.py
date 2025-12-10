import asyncio
import os
import re
from typing import Union

import yt_dlp
from googleapiclient.discovery import build
from pyrogram.types import Message

from AnonXMusic.utils.formatters import time_to_seconds
from AnonXMusic.utils.database import is_on_off


class YouTubeAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if api_key:
            self.youtube = build("youtube", "v3", developerKey=api_key)
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link: str):
        return bool(re.search(self.regex, link))

    async def search(self, query: str, limit: int = 1):
        """Search using YT API, fallback to ytsearch if API fails"""
        try:
            if self.api_key:
                req = self.youtube.search().list(
                    q=query,
                    part="snippet",
                    type="video",
                    maxResults=limit,
                )
                res = req.execute()
                results = []
                for item in res.get("items", []):
                    vidid = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    duration_min = None  # duration needs a second API call
                    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                    results.append({
                        "title": title,
                        "vidid": vidid,
                        "duration_min": duration_min,
                        "thumb": thumbnail,
                        "link": self.base + vidid
                    })
                return results
        except Exception:
            pass  # fallback to yt_dlp search

        # Fallback using yt-dlp
        loop = asyncio.get_running_loop()
        def yt_search():
            ydl_opts = {"quiet": True}
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            results = []
            for video in info["entries"]:
                duration_min = time_to_seconds(str(video.get("duration") or "0:00"))
                results.append({
                    "title": video.get("title"),
                    "vidid": video.get("id"),
                    "duration_min": duration_min,
                    "thumb": video.get("thumbnail"),
                    "link": video.get("webpage_url")
                })
            return results

        return await loop.run_in_executor(None, yt_search)

    async def track(self, query_or_link: str):
        """Return single track details (title, vidid, duration, thumbnail, link)"""
        results = await self.search(query_or_link, limit=1)
        if results:
            track = results[0]
            # If duration is missing, fetch via yt-dlp
            if not track["duration_min"]:
                loop = asyncio.get_running_loop()
                def yt_info():
                    ydl_opts = {"quiet": True}
                    ydl = yt_dlp.YoutubeDL(ydl_opts)
                    info = ydl.extract_info(track["link"], download=False)
                    track["duration_min"] = int(info.get("duration") or 0)
                    return track
                track = await loop.run_in_executor(None, yt_info)
            return track, track["vidid"]
        return None, None

    async def download(self, link: str, songaudio=False, songvideo=False, format_id=None, title=None):
        """Download audio/video using yt-dlp"""
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=True)
            return os.path.join("downloads", f"{info['id']}.{info['ext']}")

        def video_dl():
            ydl_opts = {
                "format": "best[height<=?720]",
                "outtmpl": f"downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=True)
            return os.path.join("downloads", f"{info['id']}.{info['ext']}")

        if songaudio or not songvideo:
            return await loop.run_in_executor(None, audio_dl)
        return await loop.run_in_executor(None, video_dl)
        
