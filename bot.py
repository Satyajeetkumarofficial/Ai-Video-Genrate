import os
import time
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message
from generator import text_to_frames, image_prompt_to_frames, frames_to_video, cleanup_dir

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("ai_video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

def is_allowed(user_id): return (not ADMIN_IDS) or (user_id in ADMIN_IDS)

@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply_text(
        "👋 *AI Text → Video Bot (High Quality)*\n\n"
        "🪄 `/gen_text your prompt`\n"
        "🖼️ Reply kisi image par `/gen_img2vid prompt`\n\n"
        "⚙️ Quality high hai — CPU pe processing hogi, time lagega.\n"
        "⏳ Video bante waqt bot aapko timing dikhayega.",
        quote=True
    )

@app.on_message(filters.command("gen_text") & filters.private)
async def gen_text(_, m: Message):
    if not is_allowed(m.from_user.id):
        return await m.reply_text("❌ Permission denied.")
    args = m.text.split(" ", 1)
    if len(args) < 2:
        return await m.reply_text("Usage: `/gen_text prompt`")
    prompt = args[1].strip()
    tmp = f"tmp_{uuid.uuid4().hex}"
    os.makedirs(tmp, exist_ok=True)
    msg = await m.reply_text("🎨 Rendering video... please wait (High Quality Mode).")
    try:
        start = time.time()
        frames = text_to_frames(prompt, tmp, num_frames=12, width=720, height=720, steps=40)
        video_path = os.path.join(tmp, "video.mp4")
        frames_to_video(frames, video_path, fps=12)
        elapsed = time.time() - start
        mins, secs = divmod(int(elapsed), 60)
        await msg.delete()
        await m.reply_video(video_path, caption=f"✅ *Done in {mins}m {secs}s*\n🧠 Prompt: `{prompt}`", quote=True)
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")
    finally:
        cleanup_dir(tmp)

@app.on_message(filters.command("gen_img2vid") & filters.private)
async def gen_img2vid(_, m: Message):
    if not is_allowed(m.from_user.id):
        return await m.reply_text("❌ Permission denied.")
    if not m.reply_to_message or not (m.reply_to_message.photo or m.reply_to_message.document):
        return await m.reply_text("Reply to an image with `/gen_img2vid prompt`")
    args = m.text.split(" ", 1)
    prompt = args[1].strip() if len(args) > 1 else "animated version"
    tmp = f"tmp_{uuid.uuid4().hex}"
    os.makedirs(tmp, exist_ok=True)
    msg = await m.reply_text("🪄 Processing your image, please wait...")
    try:
        start = time.time()
        img_path = os.path.join(tmp, "input.jpg")
        await m.reply_to_message.download(img_path)
        frames = image_prompt_to_frames(img_path, prompt, tmp, num_frames=10, strength=0.65, steps=35)
        video_path = os.path.join(tmp, "output.mp4")
        frames_to_video(frames, video_path, fps=12)
        elapsed = time.time() - start
        mins, secs = divmod(int(elapsed), 60)
        await msg.delete()
        await m.reply_video(video_path, caption=f"✅ *Done in {mins}m {secs}s*\n🎨 Prompt: `{prompt}`", quote=True)
    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")
    finally:
        cleanup_dir(tmp)

if __name__ == "__main__":
    app.run()
