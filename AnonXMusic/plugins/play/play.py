from pyrogram import filters
from pyrogram.types import Message

from AnonXMusic import app, YouTube
from AnonXMusic.utils.channelplay import get_channeplayCB
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS


@app.on_message(filters.command(["play", "song"]) & ~BANNED_USERS)
@languageCB
async def play_song(client, message: Message, _):
    query = " ".join(message.command[1:]) if len(message.command) > 1 else None
    if not query:
        return await message.reply_text("❌ Please provide a song name or URL to play.")

    mystic = await message.reply_text(_["play_0"])  # "Processing your query..."

    try:
        # Try YouTube API first
        details, vidid = await YouTube.track(query, videoid=False)
    except Exception:
        try:
            # Fallback: use yt-dlp search
            details, vidid = await YouTube.track(query, videoid=False, use_ytapi=False)
        except Exception as e:
            return await mystic.edit_text(f"❌ Failed to process your query: {str(e)}")

    # Check for live stream properly
    is_live = details.get("is_live", False)
    duration = details.get("duration_sec", 0)

    if is_live or duration == 0:
        return await mystic.edit_text("❌ Live stream detected. Cannot play automatically.")

    # Normal song
    chat_id = message.chat.id
    user_name = message.from_user.first_name

    try:
        await stream(
            _,
            mystic,
            message.from_user.id,
            details,
            chat_id,
            user_name,
            chat_id,
            video=False,
            streamtype="audio",
        )
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed to start stream: {str(e)}")
