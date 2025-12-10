import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds
from googleapiclient.discovery import build
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
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        if YOUTUBE_API_KEY:
            self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        else:
            self.youtube = None

    # Extract URL from message or reply
    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        return message.text[entity.offset : entity.offset + entity.length]
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def search(self, query: str, limit: int = 1):
        if self.youtube:
            # Using YouTube API
            try:
                request = self.youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    maxResults=limit
                )
                response = request.execute()
                results = []
                for item in response.get("items", []):
                    results.append({
                        "title": item["snippet"]["title"],
                        "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        "vidid": item["id"]["videoId"],
                        "duration_min": None,
                        "thumb": item["snippet"]["thumbnails"]["high"]["url"]
                    })
                return results
            except Exception:
                # fallback if API fails
                pass

        # Fallback to youtubesearchpython
        results = []
        search = VideosSearch(query, limit=limit)
        for r in (await search.next())["result"]:
            results.append({
                "title": r["title"],
                "link": r["link"],
                "vidid": r["id"],
                "duration_min": r.get("duration"),
                "thumb": r["thumbnails"][0]["url"].split("?")[0]
            })
        return results

    async def details(self, link: str):
        results = await self.search(link)
        if results:
            r = results[0]
            duration_sec = int(time_to_seconds(r["duration_min"])) if r["duration_min"] else 0
            return r["title"], r["duration_min"], duration_sec, r["thumb"], r["vidid"]
        return None, None, 0, None, None

    async def track(self, link: str):
        results = await self.search(link)
        if results:
            r = results[0]
            track_details = {
                "title": r["title"],
                "link": r["link"],
                "vidid": r["vidid"],
                "duration_min": r["duration_min"],
                "thumb": r["thumb"]
            }
            return track_details, r["vidid"]
        return None, None

    async def playlist(self, link, limit, user_id):
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            result = [x for x in result if x]
        except:
            result = []
        return result

    async def video(self, link: str):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def download(
        self,
        link: str,
        video: bool = False,
        songaudio: bool = False,
        songvideo: bool = False,
        format_id: str = None,
        title: str = None,
    ):
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            ydl.download([link])
            return xyz

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "no_warnings": True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            ydl.download([link])
            return xyz

        if songvideo:
            await loop.run_in_executor(None, video_dl)
            return f"downloads/{title}.mp4"
        elif songaudio:
            await loop.run_in_executor(None, audio_dl)
            return f"downloads/{title}.mp3"
        elif video:
            downloaded_file = await loop.run_in_executor(None, video_dl)
            return downloaded_file
        else:
            downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file
                
        
            
