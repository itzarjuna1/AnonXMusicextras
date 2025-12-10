from pyrogram import filters
from AnonXMusic import YouTube, app
from AnonXMusic.utils.channelplay import get_channeplayCB
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS


@app.on_callback_query(filters.regex("LiveStream") & ~BANNED_USERS)
@languageCB
async def play_live_stream(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return

    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return

    video = True if mode == "v" else None
    user_name = CallbackQuery.from_user.first_name

    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass

    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    # Use new safe API method
    try:
        url = await YouTube.get_url_from_message(CallbackQuery.message)
        if not url:
            return await mystic.edit_text("❌ No YouTube link found.")
        details, track_id = await YouTube.track(url, True)
    except Exception as e:
        return await mystic.edit_text(_["play_3"])

    ffplay = True if fplay == "f" else None

    # Live stream detection
    if not details["duration_min"] or details["duration_min"].upper() == "LIVE":
        try:
            await stream(
                _,
                mystic,
                int(user_id),
                details,
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                streamtype="live",
                forceplay=ffplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
    else:
        # Normal song playback
        try:
            await stream(
                _,
                mystic,
                int(user_id),
                details,
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                forceplay=ffplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)

    await mystic.delete()


# Optional: For regular /play command
@app.on_message(filters.command("play") & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    query = message.text.split(None, 1)
    if len(query) < 2:
        return await message.reply_text("❌ Please provide a song name or link.")
    song_query = query[1]

    mystic = await message.reply_text(_["play_1"])
    try:
        details, track_id = await YouTube.track(song_query)
        if not details["duration_min"] or details["duration_min"].upper() == "LIVE":
            await stream(
                _,
                mystic,
                message.from_user.id,
                details,
                message.chat.id,
                message.from_user.first_name,
                message.chat.id,
                video=True,
                streamtype="live",
            )
        else:
            await stream(
                _,
                mystic,
                message.from_user.id,
                details,
                message.chat.id,
                message.from_user.first_name,
                message.chat.id,
                video=False,
            )
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed to process your query: {e}")

    await mystic.delete()
        
