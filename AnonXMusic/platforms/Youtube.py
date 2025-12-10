import yt_dlp
import asyncio

class YouTubeAPI:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    async def track(self, query, return_details=False):
        """
        Search and get video details from YouTube.
        Supports normal videos and live streams.
        """
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "extract_flat": "in_playlist"
        }

        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]

        info = await self.loop.run_in_executor(None, run_ydl)

        if not info:
            raise Exception("No results found.")

        details = {
            "title": info.get("title"),
            "url": info.get("url"),
            "duration": info.get("duration"),
            "live": info.get("is_live"),
            "webpage_url": info.get("webpage_url")
        }

        if return_details:
            return details, info.get("id")
        return details
