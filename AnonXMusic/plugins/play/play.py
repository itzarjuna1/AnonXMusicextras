from pyrogram import filters
from AnonXMusic import app
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS

# Import YouTubeAPI safely inside the handler
@app.on_message(filters.command(["play", "p"]) & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    from AnonXMusic.platforms.Youtube import YouTubeAPI
    YouTube = YouTubeAPI()

    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text("❌ Please provide a song name or link.")

    msg = await message.reply_text("🔎 Searching for your song...")
    try:
        details, track_id = await YouTube.track(query, return_details=True)
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to process your query: {str(e)}")

    # Check if it's live
    stream_type = "live" if details["live"] else "audio"

    # Call your stream function
    try:
        await stream(
            _,
            msg,
            message.from_user.id,
            details,
            message.chat.id,
            message.from_user.first_name,
            message.chat.id,
            video=None,
            streamtype=stream_type,
            forceplay=None
        )
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to play: {str(e)}")
