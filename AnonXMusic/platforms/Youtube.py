import asyncio
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from googleapiclient.discovery import build

from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds

# Load YouTube API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube_api = build("youtube", "v3", developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

COOKIES_FILE = "cookies.txt"  # fallback for yt-dlp

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
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def api_search(self, query: str):
        """Search using YouTube API"""
        if not youtube_api:
            return None
        try:
            req = youtube_api.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=1
            )
            res = req.execute()
            item = res["items"][0]
            vidid = item["id"]["videoId"]
            title = item["snippet"]["title"]
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            return {"video_id": vidid, "title": title, "thumbnail": thumbnail}
        except Exception as e:
            print("YouTube API search failed:", e)
            return None

    async def yt_dlp_search(self, query: str):
        """Search using yt-dlp fallback"""
        try:
            ydl_opts = {
                "quiet": True,
                "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            return {
                "video_id": info["id"],
                "title": info["title"],
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail")
            }
        except Exception as e:
            print("yt-dlp search failed:", e)
            return None

    async def search(self, query: str):
        """API first, fallback to yt-dlp"""
        result = await self.api_search(query)
        if result:
            return result
        return await self.yt_dlp_search(query)

    async def details(self, link: str):
        """Get video details (title, duration, thumbnail)"""
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def download(self, link: str, video=False, songaudio=False, songvideo=False, format_id=None, title=None):
        """Download audio/video using yt-dlp"""
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_opts)
            info = x.extract_info(link, False)
            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(path):
                return path
            x.download([link])
            return path

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_opts)
            info = x.extract_info(link, False)
            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(path):
                return path
            x.download([link])
            return path

        def song_video_dl():
            fpath = f"downloads/{title}"
            ydl_opts = {
                "format": f"{format_id}+140",
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_opts)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_opts = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_opts)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"
        elif video:
            downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file
        
            
