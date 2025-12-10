# AnonXMusic/plugins/play/play.py
from pyrogram import filters
from AnonXMusic import YouTube, app
from AnonXMusic.utils.channelplay import get_channeplayCB
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS

YouTube = YouTubeAPI()

@app.on_callback_query(filters.regex("LiveStream") & ~BANNED_USERS)
@languageCB
async def play_live_stream(client, CallbackQuery, _):
    data = CallbackQuery.data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = data.split("|")

    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer("❌ Not for you!", show_alert=True)

    chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    await CallbackQuery.message.delete()
    await CallbackQuery.answer()

    mystic = await CallbackQuery.message.reply_text(
        f"🎵 Loading {channel}" if channel else "🎵 Loading song..."
    )

    details, track_id = await YouTube.track(vidid, True)
    if not details:
        return await mystic.edit_text("❌ Cannot play live streams or unavailable videos.")

    ffplay = True if fplay == "f" else None
    video = True if mode == "v" else None

    try:
        await stream(
            _,
            mystic,
            int(user_id),
            details,
            chat_id,
            CallbackQuery.from_user.first_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="song",
            forceplay=ffplay,
        )
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed: {type(e).__name__}")
