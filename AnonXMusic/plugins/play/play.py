from pyrogram import filters
from AnonXMusic import app, YouTube
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS

@languageCB
@app.on_message(filters.command("play") & ~BANNED_USERS)
async def play(client, message, _):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text(_["play_4"])  # "Please provide a song name."

    mystic = await message.reply_text(_["play_5"].format(query))  # "Searching..."
    try:
        details, vidid = await YouTube.track(query)
        if not details:
            return await mystic.edit_text(_["play_3"])  # "Song not found."
        video = False if details["duration_min"] else True
        await stream(
            _,
            mystic,
            message.from_user.id,
            details,
            message.chat.id,
            message.from_user.first_name,
            message.chat.id,
            video,
        )
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed to process your query: {str(e)}")
        
