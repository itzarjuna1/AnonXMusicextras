import asyncio
import os
import re
from typing import Union
import yt_dlp
from youtubesearchpython.__future__ import VideosSearch
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.api_key = YOUTUBE_API_KEY
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    async def search_youtube(self, query):
        """Search using API; fallback to yt-dlp if fails"""
        try:
            res = self.youtube.search().list(
                q=query, part="snippet", maxResults=1, type="video"
            ).execute()
            items = res.get("items", [])
            if not items:
                return []
            item = items[0]
            return [{
                "title": item["snippet"]["title"],
                "id": item["id"]["videoId"],
                "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "duration": None,  # will fill with yt-dlp
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
            }]
        except Exception:
            # fallback to yt-dlp search
            try:
                results = []
                search = VideosSearch(query, limit=1)
                for r in (await search.next())["result"]:
                    results.append({
                        "title": r["title"],
                        "id": r["id"],
                        "link": r["link"],
                        "duration": r["duration"],
                        "thumbnail": r["thumbnails"][0]["url"].split("?")[0]
                    })
                return results
            except Exception:
                return []

    async def track(self, query: str, videoid: Union[bool, str] = None):
        try:
            results = await self.search_youtube(query)
            if not results:
                raise Exception("No results")
            result = results[0]
            details = {
                "title": result.get("title", "Unknown Title"),
                "link": result.get("link", ""),
                "vidid": result.get("id", ""),
                "duration_min": result.get("duration", "0:00"),
                "thumb": result.get("thumbnail", ""),
            }
            return details, details["vidid"]
        except Exception:
            return {
                "title": "Unknown Title",
                "link": "",
                "vidid": "",
                "duration_min": "0:00",
                "thumb": "",
            }, ""
