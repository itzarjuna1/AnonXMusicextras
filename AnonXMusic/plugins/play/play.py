from pyrogram import filters
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.stream.stream import stream
from config import BANNED_USERS


@app.on_message(filters.command(["play", "p"]) & ~BANNED_USERS)
@languageCB
async def play_song(client, message, _):
    # Import inside function to avoid circular imports
    from AnonXMusic import YouTube

    if len(message.command) < 2:
        return await message.reply_text(_("Please provide a song name or link!"))

    query = " ".join(message.command[1:]).strip()
    user_name = message.from_user.first_name
    user_id = message.from_user.id

    mystic = await message.reply_text(_("🔎 Searching for your song..."))

    try:
        # Fetch song details
        details, track_id = await YouTube.track(query)
    except Exception as e:
        return await mystic.edit_text(f"❌ Failed to process your query: {e}")

    # Live stream check
    if details.get("is_live"):
        return await mystic.edit_text("❌ Cannot play live streams.")

    try:
        await stream(
            _,
            mystic,
            user_id,
            details,
            message.chat.id,
            user_name,
            message.chat.id,
            video=False,
            streamtype="audio",
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _("An error occurred: {}").format(ex_type)
        return await mystic.edit_text(err)
