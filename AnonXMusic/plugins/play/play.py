from pyrogram import filters
from AnonXMusic import app, YouTube
from AnonXMusic.utils.stream.stream import stream
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.channelplay import get_channeplayCB
from config import BANNED_USERS

@app.on_message(filters.command(["play", "song"]) & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    query = " ".join(message.command[1:])

    if not query:
        return await message.reply_text("❌ Please provide a song name or link.")

    # Immediate feedback
    mystic = await message.reply_text("🔍 Searching your song...")

    try:
        # Try YouTube API first
        details, track_id = await YouTube.track(query)
    except Exception as e:
        # If API fails, fallback to yt_dlp / cookies
        try:
            details, track_id = await YouTube.track(query, use_api=False)
        except Exception as e2:
            return await mystic.edit_text(f"❌ Failed to process query:\n{e2}")

    if not details:
        return await mystic.edit_text("❌ No results found!")

    # Check if it’s a live stream
    if not details.get("duration_min"):
        await mystic.edit_text("» ʟɪᴠᴇ sᴛʀᴇᴀᴍ ᴅᴇᴛᴇᴄᴛᴇᴅ.\nAre you sure you want to play this live stream?")
        return

    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        await stream(
            _,
            mystic,
            user_id,
            details,
            chat_id,
            user_name,
            chat_id,
            video=True,  # Set False if you want audio only
            streamtype="song",
        )
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed to start streaming:\n{e}")
        
