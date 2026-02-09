from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
import asyncio
import os
import signal

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "25649636"))
API_HASH = os.environ.get("API_HASH", "43af470d1c625e603733268b3c2f7b8f")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8463032760:AAHbdPDVDlLwbLVNZpKPG41fSlnbIRSS4Vc")

SOURCE_CHANNEL = -1003748804419  # सोर्स चैनल - बॉट को यहाँ Admin बनाओ

TARGET_CHANNELS = [
    "-1003553400713",
    "-1003245056110",
    "-1003676653101"
]

POST_DELAY = 10      # 600 sec = 10 min
MAX_POSTS = 4         # 0 = unlimited | 10 = sirf 10 posts
# ============================================

app = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Queue: naye post yahan add honge, 10 min gap par process
message_queue = asyncio.Queue()
forward_count = 0
stop_event = asyncio.Event()

# Heroku SIGTERM - pehle se handler set (R12 fix)
def handle_sigterm(signum, frame):
    print("🛑 SIGTERM received, shutting down...")
    stop_event.set()
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, handle_sigterm)


async def queue_worker():
    """Queue se messages lo, 10 min gap par alag-alag channel me forward karo"""
    global forward_count
    while not stop_event.is_set():
        try:
            try:
                msg = await asyncio.wait_for(message_queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                continue
            if msg is None:
                break

            if MAX_POSTS and forward_count >= MAX_POSTS:
                print("✅ Max posts reached. No more forwarding.")
                continue

            channel_index = forward_count % len(TARGET_CHANNELS)
            target = TARGET_CHANNELS[channel_index]

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
        except asyncio.CancelledError:
            break


@app.on_message(filters.chat(SOURCE_CHANNEL) & (filters.photo | filters.video))
async def on_new_post(client, message):
    """जब source channel me naya photo/video post aayega"""
    media_type = "photo" if message.photo else "video"
    print(f"📥 POST AAYA! Source channel me naya {media_type} post received (msg_id: {message.id})")
    await message_queue.put(message)
    print(f"   Queue me add ho gaya. Abhi queue size: {message_queue.qsize()}")


async def check_bot_admin():
    try:
        bot = await app.get_me()
        me = await app.get_chat_member(SOURCE_CHANNEL, bot.id)

        if me.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            print(f"✅ Bot {SOURCE_CHANNEL} me ADMIN hai")
            return True
        else:
            print(f"❌ Bot admin nahi hai")
            print(f"   Status: {me.status}")
            return False

    except Exception as e:
        print(f"❌ Admin check failed: {e}")
        print("➡️ Confirm karo:")
        print("   1. Bot source channel me ADMIN hai")
        print("   2. Channel username / ID sahi hai")
        return False



async def main():
    print("🤖 Starting bot - sirf UPCOMING posts forward honge...")

    # Pehle admin check - agar nahi hai to exit
    is_admin = await check_bot_admin()
    if not is_admin:
        print("🛑 Bot start nahi hoga. Pehle admin banao.")
        return

    worker_task = asyncio.create_task(queue_worker())
    print("✅ Bot ready. Source channel me post aate hi log me 'POST AAYA!' dikhega.")
    from pyrogram import idle
    idle_task = asyncio.create_task(idle())
    await stop_event.wait()
    print("🛑 Stopping...")
    idle_task.cancel()
    worker_task.cancel()
    try:
        await idle_task
    except asyncio.CancelledError:
        pass
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await app.stop()
    print("✅ Stopped cleanly.")


if __name__ == "__main__":
    app.run(main())




