import yt_dlp
import asyncio

class YouTubeAPI:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    async def search(self, query: str):
        """Search a song on YouTube and return first result"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            return info['entries'][0]
        return info

    async def get_stream(self, url: str):
        """Get audio stream URL from a YouTube link"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'url' in info:
            return info['url']
        elif 'entries' in info:
            return info['entries'][0]['url']
        else:
            return None

    async def is_live(self, url: str):
        """Check if YouTube link is live"""
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info.get('is_live', False)
