# bot.py
import os
import time
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message
from generator import text_to_frames, image_prompt_to_frames, frames_to_video, cleanup_dir

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# create client
app = Client("ai_video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Optional admin restriction (comma separated)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

def is_allowed(user_id):
    return (not ADMIN_IDS) or (user_id in ADMIN_IDS)

@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply_text(
        "👋 *AI Text→Video Bot (High Quality mode available)*\n\n"
        "Commands:\n"
        "• `/gen_text <prompt>`  — Text → short animated video\n"
        "• Reply to an image with `/gen_img2vid <prompt>`  — Image + prompt → animated video\n\n"
        "⚠️ Note: This runs on CPU (Koyeb free). High quality takes time. Processing time will be shown when done.",
        quote=True
    )

@app.on_message(filters.command("gen_text") & filters.private)
async def gen_text(_, m: Message):
    user = m.from_user
    if not is_allowed(user.id):
        return await m.reply_text("❌ You are not authorized to use this bot.")
    args = m.text.split(" ", 1)
    if len(args) < 2 or not args[1].strip():
        return await m.reply_text("Usage: `/gen_text Prompt here`")
    prompt = args[1].strip()
    tmp = f"tmp_{uuid.uuid4().hex}"
    os.makedirs(tmp, exist_ok=True)

    status = await m.reply_text("⏳ Rendering (High Quality). This may take several minutes on CPU...")
    try:
        start_ts = time.time()
        # High-quality parameters (you can tune)
        frames = text_to_frames(prompt, tmp, num_frames=12, width=720, height=720, steps=40)
        out_mp4 = os.path.join(tmp, "output.mp4")
        frames_to_video(frames, out_mp4, fps=12)
        elapsed = time.time() - start_ts
        mins, secs = divmod(int(elapsed), 60)
        await status.delete()
        await m.reply_video(out_mp4, caption=f"✅ Done in {mins}m {secs}s\nPrompt: `{prompt}`", quote=True)
    except Exception as e:
        await status.edit(f"❌ Error: {e}")
    finally:
        cleanup_dir(tmp)

@app.on_message(filters.command("gen_img2vid") & filters.private)
async def gen_img2vid(_, m: Message):
    user = m.from_user
    if not is_allowed(user.id):
        return await m.reply_text("❌ You are not authorized to use this bot.")
    # must be reply to image
    if not m.reply_to_message or not (m.reply_to_message.photo or m.reply_to_message.document):
        return await m.reply_text("Reply to an image with `/gen_img2vid <prompt>`")
    args = m.text.split(" ", 1)
    prompt = args[1].strip() if len(args) > 1 else "animated version"
    tmp = f"tmp_{uuid.uuid4().hex}"
    os.makedirs(tmp, exist_ok=True)

    status = await m.reply_text("🖼️ Processing image and rendering... This may take several minutes.")
    try:
        start_ts = time.time()
        in_path = os.path.join(tmp, "input.jpg")
        await m.reply_to_message.download(in_path)
        frames = image_prompt_to_frames(in_path, prompt, tmp, num_frames=10, strength=0.65, steps=35)
        out_mp4 = os.path.join(tmp, "output.mp4")
        frames_to_video(frames, out_mp4, fps=12)
        elapsed = time.time() - start_ts
        mins, secs = divmod(int(elapsed), 60)
        await status.delete()
        await m.reply_video(out_mp4, caption=f"✅ Done in {mins}m {secs}s\nPrompt: `{prompt}`", quote=True)
    except Exception as e:
        await status.edit(f"❌ Error: {e}")
    finally:
        cleanup_dir(tmp)

if __name__ == "__main__":
    app.run()
