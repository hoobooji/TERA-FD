from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus
import asyncio
import os
import signal

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "25649636"))
API_HASH = os.environ.get("API_HASH", "43af470d1c625e603733268b3c2f7b8f")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8463032760:AAHbdPDVDlLwbLVNZpKPG41fSlnbIRSS4Vc")

SOURCE_CHANNEL = -1003719599385   # SOURCE channel ID (bot must be admin)

TARGET_CHANNELS = [
    -1003553400713,
    -1003245056110,
    -1003676653101
]

POST_DELAY = 10      # seconds (Heroku test ke liye)
MAX_POSTS = 4        # 0 = unlimited
# ============================================

app = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

message_queue = asyncio.Queue()
forward_count = 0
stop_event = asyncio.Event()

# ================== HEROKU SIGTERM ==================
def handle_sigterm(signum, frame):
    print("🛑 SIGTERM received, shutting down...")
    stop_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)

# ================== QUEUE WORKER ==================
async def queue_worker():
    global forward_count
    while not stop_event.is_set():
        try:
            msg = await asyncio.wait_for(message_queue.get(), timeout=5)
        except asyncio.TimeoutError:
            continue

        if MAX_POSTS and forward_count >= MAX_POSTS:
            print("✅ Max posts reached.")
            continue

        target = TARGET_CHANNELS[forward_count % len(TARGET_CHANNELS)]

        try:
            if msg.photo:
                await app.send_photo(
                    target,
                    msg.photo.file_id,
                    caption=msg.caption or ""
                )
            elif msg.video:
                await app.send_video(
                    target,
                    msg.video.file_id,
                    caption=msg.caption or ""
                )
            else:
                print("⏭ Skipped non-media")
                continue

            forward_count += 1
            print(f"➡️ Forwarded {forward_count} to {target}")

        except Exception as e:
            print(f"❌ Forward error: {e}")

        await asyncio.sleep(POST_DELAY)

# ================== SOURCE LISTENER ==================
@app.on_message(filters.chat(SOURCE_CHANNEL) & (filters.photo | filters.video))
async def on_new_post(client, message):
    print(f"📥 New post received (msg_id: {message.id})")
    await message_queue.put(message)
    print(f"📦 Queue size: {message_queue.qsize()}")

# ================== ADMIN CHECK ==================
async def check_bot_admin():
    try:
        bot = await app.get_me()
        member = await app.get_chat_member(SOURCE_CHANNEL, bot.id)

        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            print("✅ Bot is ADMIN in source channel")
            return True
        else:
            print(f"❌ Bot status: {member.status}")
            return False

    except Exception as e:
        print(f"❌ Admin check failed: {e}")
        return False

# ================== MAIN ==================
async def main():
    print("🤖 Starting bot (only UPCOMING posts)...")

    # 🔥 MOST IMPORTANT FIX
    await app.start()

    is_admin = await check_bot_admin()
    if not is_admin:
        print("🛑 Bot start aborted. Make bot ADMIN first.")
        await app.stop()
        return

    worker_task = asyncio.create_task(queue_worker())
    print("✅ Bot READY. Waiting for new posts...")

    await stop_event.wait()

    print("🛑 Shutting down...")
    worker_task.cancel()
    await app.stop()
    print("✅ Bot stopped cleanly.")

# ================== RUN ==================
if __name__ == "__main__":
    app.run(main())

