import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from googleapiclient.discovery import build
from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds

# Helper for shell commands
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
        return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self, api_key: str = None):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=self.api_key) if self.api_key else None

    async def search(self, query: str, max_results: int = 1):
        """Search YouTube via API or yt-dlp fallback"""
        # Use API if available
        if self.youtube:
            try:
                res = self.youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    maxResults=max_results
                ).execute()
                items = res.get("items", [])
                if not items:
                    return None
                video = items[0]
                videoId = video["id"]["videoId"]
                title = video["snippet"]["title"]
                thumb = video["snippet"]["thumbnails"]["high"]["url"]
                return {"title": title, "videoId": videoId, "thumb": thumb}
            except Exception:
                pass  # fallback to yt-dlp

        # yt-dlp fallback
        cmd = f"yt-dlp ytsearch1:{query} --skip-download --print-json"
        result = await shell_cmd(cmd)
        try:
            import json
            info = json.loads(result.splitlines()[0])
            return {
                "title": info["title"],
                "videoId": info["id"],
                "thumb": info["thumbnail"]
            }
        except Exception:
            return None

    async def get_url(self, videoId: str):
        """Return full YouTube URL from videoId"""
        return f"{self.base}{videoId}"

    async def get_details(self, videoId: str):
        """Return title, duration, thumbnail, and live status"""
        url = await self.get_url(videoId)
        ytdl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title")
            duration = info.get("duration", 0)
            thumb = info.get("thumbnail")
            is_live = info.get("is_live", False)
            return {"title": title, "duration": duration, "thumb": thumb, "is_live": is_live}

    async def download(self, videoId: str, audio_only=True):
        """Download audio/video file"""
        url = await self.get_url(videoId)
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return f"downloads/{info['id']}.mp3"

        def video_dl():
            ydl_opts = {
                "format": "bestvideo+bestaudio",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return f"downloads/{info['id']}.{info['ext']}"

        if audio_only:
            return await loop.run_in_executor(None, audio_dl)
        return await loop.run_in_executor(None, video_dl)
        
