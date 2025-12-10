from pyrogram import filters
from AnonXMusic import YouTube, app
from AnonXMusic.utils.channelplay import get_channeplayCB
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS

@app.on_message(filters.command("play") & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    query = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    if not query.strip():
        return await message.reply_text(_["play_4"])

    mystic = await message.reply_text(_["play_5"].format(query=query or "Unknown Song"))

    try:
        details, vidid = await YouTube.track(query)
    except Exception:
        return await mystic.edit_text(_["play_3"])

    # Safe handling of None values
    details["title"] = details.get("title") or "Unknown Title"
    details["duration_min"] = details.get("duration_min") or "0:00"
    details["thumb"] = details.get("thumb") or ""
    details["link"] = details.get("link") or ""

    if "live" in details["duration_min"].lower():
        return await mystic.edit_text("» ʟɪᴠᴇ sᴛʀᴇᴀᴍ ᴅᴇᴛᴇᴄᴛᴇᴅ.\n\nᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴɴᴀ ᴘʟᴀʏ ᴛʜɪs ʟɪᴠᴇ sᴛʀᴇᴀᴍ ?")

    try:
        chat_id, channel = await get_channeplayCB(_, None, message)
    except Exception:
        chat_id = message.chat.id
        channel = None

    user_name = message.from_user.first_name
    try:
        await stream(
            _,
            mystic,
            message.from_user.id,
            details,
            chat_id,
            user_name,
            message.chat.id,
            video=False,
            streamtype="song",
            forceplay=None,
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
        return await mystic.edit_text(err)
