import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from googleapiclient.discovery import build

from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds
from config import YOUTUBE_API_KEY


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
        self.api_key = YOUTUBE_API_KEY
        if self.api_key:
            self.youtube = build("youtube", "v3", developerKey=self.api_key)
        else:
            self.youtube = None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # Try YouTube API first
        if self.youtube:
            try:
                video_id = link.split("watch?v=")[-1]
                response = self.youtube.videos().list(
                    part="snippet,contentDetails",
                    id=video_id
                ).execute()
                item = response["items"][0]
                title = item["snippet"]["title"]
                duration = item["contentDetails"]["duration"]
                duration_sec = time_to_seconds(duration)
                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
                vidid = video_id
                yturl = link
                return {
                    "title": title,
                    "link": yturl,
                    "vidid": vidid,
                    "duration_min": duration,
                    "thumb": thumbnail,
                }, vidid
            except:
                pass  # fallback to yt-dlp

        # Fallback using yt_dlp
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            yturl = result["link"]
        return {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, vidid

    async def download(self, link, format_id=None, title=None, songaudio=False, songvideo=False):
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return f"downloads/{info['id']}.{info['ext']}"

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return f"downloads/{info['id']}.{info['ext']}"

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_opts = {
                "format": str(format_id),  # fixed int.upper() issue
                "outtmpl": fpath,
                "quiet": True,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        def song_video_dl():
            formats = f"{str(format_id)}+140"
            fpath = f"downloads/{title}.mp4"
            ydl_opts = {
                "format": formats,
                "outtmpl": fpath,
                "quiet": True,
                "merge_output_format": "mp4",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        if songvideo:
            return await loop.run_in_executor(None, song_video_dl)
        elif songaudio:
            return await loop.run_in_executor(None, song_audio_dl)
        else:
            return await loop.run_in_executor(None, audio_dl)
            
