import os
import re
import asyncio
from typing import Union
import yt_dlp
from googleapiclient.discovery import build
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from AnonXMusic.utils.formatters import time_to_seconds
from config import YOUTUBE_API_KEY

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.youtube_service = None
        if YOUTUBE_API_KEY:
            try:
                self.youtube_service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
            except:
                self.youtube_service = None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        return bool(re.search(self.regex, link))

    async def track(self, query: str, videoid: Union[bool, str] = None):
        """Returns dict with title, link, vidid, duration_min, thumb"""
        if self.youtube_service:
            try:
                # Search using YT API
                request = self.youtube_service.search().list(
                    part="snippet",
                    q=query,
                    maxResults=1,
                    type="video"
                )
                response = request.execute()
                if "items" not in response or not response["items"]:
                    raise Exception("No results found via API.")
                item = response["items"][0]
                vidid = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumb = item["snippet"]["thumbnails"]["high"]["url"]
                # Duration via videos().list
                dur_req = self.youtube_service.videos().list(
                    part="contentDetails",
                    id=vidid
                )
                dur_resp = dur_req.execute()
                duration_min = "0:00"
                if "items" in dur_resp and dur_resp["items"]:
                    iso_duration = dur_resp["items"][0]["contentDetails"]["duration"]
                    duration_sec = self.parse_duration(iso_duration)
                    mins = duration_sec // 60
                    secs = duration_sec % 60
                    duration_min = f"{mins}:{secs:02d}"
                return {
                    "title": title,
                    "link": self.base + vidid,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumb
                }, vidid
            except Exception:
                # fallback to yt-dlp search
                pass

        # fallback yt-dlp search
        results = VideosSearch(query, limit=1)
        result = (await results.next())["result"][0]
        vidid = result["id"]
        return {
            "title": result["title"],
            "link": result["link"],
            "vidid": vidid,
            "duration_min": result["duration"] or "0:00",
            "thumb": result["thumbnails"][0]["url"].split("?")[0]
        }, vidid

    def parse_duration(self, iso_duration: str):
        """Parse ISO 8601 duration string to seconds"""
        match = re.findall(r"(\d+)([HMS])", iso_duration)
        seconds = 0
        for val, unit in match:
            val = int(val)
            if unit == "H":
                seconds += val * 3600
            elif unit == "M":
                seconds += val * 60
            elif unit == "S":
                seconds += val
        return seconds

    async def video(self, link: str):
        """Returns direct stream link using yt-dlp"""
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "best[height<=?720][width<=?1280]", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()
            
