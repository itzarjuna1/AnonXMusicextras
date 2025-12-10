from pyrogram import filters
from AnonXMusic import app
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS

@app.on_message(filters.command(["play", "p"]) & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    from AnonXMusic.platforms.Youtube import YouTubeAPI
    YouTube = YouTubeAPI()

    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text("❌ Please provide a song name or URL!")

    # Search or direct URL
    try:
        result = await YouTube.search(query)
        stream_url = await YouTube.get_stream(result['webpage_url'])
        is_live = await YouTube.is_live(result['webpage_url'])
    except Exception as e:
        return await message.reply_text(f"❌ Failed to process your query: {e}")

    if is_live:
        return await message.reply_text("❌ Live streams are not supported for play command!")

    # Send reply
    await message.reply_text(f"▶️ Playing: {result.get('title', 'Unknown')}\n🎵 Channel: {result.get('uploader', 'Unknown')}")

    # Call your stream function (assume your stream() supports it)
    await stream(
        _,
        message,
        message.from_user.id,
        result,
        message.chat.id,
        message.from_user.first_name,
        message.chat.id,
        video=False,
        streamtype="song",
        forceplay=False,
    )
