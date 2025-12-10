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

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.yt = None
        if YOUTUBE_API_KEY:
            self.yt = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def get_url_from_message(self, message: Message) -> Union[str, None]:
        """Extract URL from message or its reply"""
        if message.entities:
            for entity in message.entities:
                if entity.type == MessageEntityType.URL:
                    return message.text[entity.offset: entity.offset + entity.length]
        if message.caption_entities:
            for entity in message.caption_entities:
                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url
        if message.reply_to_message:
            return await self.get_url_from_message(message.reply_to_message)
        return None

    async def search(self, query: str):
        """Search YouTube using API first, fallback to yt-dlp"""
        if self.yt:
            try:
                req = self.yt.search().list(q=query, part="snippet", type="video", maxResults=1)
                res = req.execute()
                item = res["items"][0]
                return {
                    "title": item["snippet"]["title"],
                    "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "vidid": item["id"]["videoId"],
                    "duration_min": None,  # duration needs extra API call
                    "thumb": item["snippet"]["thumbnails"]["high"]["url"]
                }
            except Exception:
                pass  # fallback to yt-dlp

        # Fallback to yt-dlp search
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "ytsearch1:" + query,
            "-f",
            "bestaudio",
            "--get-id",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            vidid = stdout.decode().strip()
            return await self.track(vidid, videoid=True)
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        # yt-dlp extraction
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            duration_min = str(info.get("duration", 0))
            return {
                "title": info.get("title"),
                "link": link,
                "vidid": info.get("id"),
                "duration_min": duration_min,
                "thumb": info["thumbnails"][-1]["url"] if info.get("thumbnails") else None
            }

    async def download_audio(self, link: str, title: str):
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"downloads/{title}.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return f"downloads/{title}.mp3"

        return await loop.run_in_executor(None, audio_dl)

    async def download_video(self, link: str, title: str):
        loop = asyncio.get_running_loop()

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=720]+bestaudio/best)",
                "outtmpl": f"downloads/{title}.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return f"downloads/{title}.mp4"

        return await loop.run_in_executor(None, video_dl)
        
