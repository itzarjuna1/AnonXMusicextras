import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from googleapiclient.discovery import build

from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        if YOUTUBE_API_KEY:
            self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # URL method for message extraction
    async def url(self, message: Message) -> str | None:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            text = msg.text or msg.caption
            if not text:
                continue

            # Check for URLs
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        return text[entity.offset : entity.offset + entity.length]

            # Check for text links
            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

        return None

    # Check if link is valid YouTube link
    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    # Get video details using YouTube API or fallback to yt-dlp
    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        if YOUTUBE_API_KEY:
            video_id = link.split("v=")[-1]
            res = self.youtube.videos().list(part="snippet,contentDetails", id=video_id).execute()
            items = res.get("items")
            if items:
                item = items[0]
                title = item["snippet"]["title"]
                duration_min = item["contentDetails"]["duration"]
                # convert ISO 8601 duration to seconds
                m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_min)
                hours, mins, secs = [int(x) if x else 0 for x in m.groups()]
                duration_sec = hours*3600 + mins*60 + secs
                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                vidid = item["id"]
                return title, duration_min, duration_sec, thumbnail, vidid

        # fallback yt-dlp
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-j",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        info = stdout.decode()
        if info:
            import json
            data = json.loads(info)
            title = data.get("title")
            duration_sec = data.get("duration", 0)
            duration_min = str(duration_sec // 60) + ":" + str(duration_sec % 60)
            thumbnail = data.get("thumbnail")
            vidid = data.get("id")
            return title, duration_min, duration_sec, thumbnail, vidid
        return None

    # Extract only title
    async def title(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[0] if details else None

    # Extract only duration
    async def duration(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[1] if details else None

    # Extract only thumbnail
    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        details = await self.details(link, videoid)
        return details[3] if details else None

    # Download audio/video
    async def download(self, link: str, video: bool = False):
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {"format": "bestaudio/best", "outtmpl": "downloads/%(id)s.%(ext)s", "quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, False)
                path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(path):
                    return path
                ydl.download([link])
                return path

        def video_dl():
            ydl_opts = {"format": "bestvideo+bestaudio", "outtmpl": "downloads/%(id)s.%(ext)s", "quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, False)
                path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(path):
                    return path
                ydl.download([link])
                return path

        return await loop.run_in_executor(None, video_dl if video else audio_dl)
        
