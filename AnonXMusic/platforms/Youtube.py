import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from googleapiclient.discovery import build
from AnonXMusic.utils.formatters import time_to_seconds
from AnonXMusic.utils.database import is_on_off
from config import YOUTUBE_API_KEY


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.youtube = None
        if YOUTUBE_API_KEY:
            self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    async def exists(self, link: str):
        return bool(re.search(self.regex, link))

    async def search_youtube(self, query: str):
        """Search via API first, then fallback to youtubesearchpython"""
        if self.youtube:
            try:
                res = (
                    self.youtube.search()
                    .list(q=query, part="snippet", maxResults=1, type="video")
                    .execute()
                )
                item = res["items"][0]
                vidid = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumb = item["snippet"]["thumbnails"]["high"]["url"]
                return {
                    "title": title,
                    "vidid": vidid,
                    "thumb": thumb,
                    "link": f"https://www.youtube.com/watch?v={vidid}",
                    "duration_min": None,  # API does not give duration here
                }
            except Exception:
                pass

        # fallback
        results = VideosSearch(query, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            thumb = result["thumbnails"][0]["url"].split("?")[0]
            link = result["link"]
            return {
                "title": title,
                "vidid": vidid,
                "thumb": thumb,
                "link": link,
                "duration_min": duration_min,
            }

    async def track(self, query: str, videoid: Union[bool, str] = None):
        """Return track details and video ID"""
        if videoid:
            query = self.base + query
        try:
            details = await self.search_youtube(query)
            return details, details["vidid"]
        except Exception:
            return None, None

    async def video(self, link: str):
        """Return direct video URL"""
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def formats(self, link: str):
        """Return available formats"""
        ydl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        with ydl:
            r = ydl.extract_info(link, download=False)
            formats_available = []
            for fmt in r.get("formats", []):
                try:
                    formats_available.append(
                        {
                            "format": fmt.get("format"),
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "format_note": fmt.get("format_note"),
                            "filesize": fmt.get("filesize"),
                        }
                    )
                except Exception:
                    continue
            return formats_available, link

    async def download(self, link: str, title: str = None, video: bool = False):
        """Download audio/video"""
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            filepath = f"downloads/{info['id']}.{info['ext']}"
            if os.path.exists(filepath):
                return filepath
            ydl.download([link])
            return filepath

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            filepath = f"downloads/{info['id']}.{info['ext']}"
            if os.path.exists(filepath):
                return filepath
            ydl.download([link])
            return filepath

        if video:
            return await loop.run_in_executor(None, video_dl)
        else:
            return await loop.run_in_executor(None, audio_dl)
