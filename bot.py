from pyrogram import Client, filters
import asyncio
import os

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "25649636"))
API_HASH = os.environ.get("API_HASH", "43af470d1c625e603733268b3c2f7b8f")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8463032760:AAHbdPDVDlLwbLVNZpKPG41fSlnbIRSS4Vc")

SOURCE_CHANNEL = "-1003748804419"  # सोर्स चैनल - बॉट को यहाँ Admin बनाओ

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


async def queue_worker():
    """Queue se messages lo, 10 min gap par alag-alag channel me forward karo"""
    global forward_count
    while True:
        try:
            msg = await message_queue.get()
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


# Channel posts - 2 handlers: channel + non-channel (group bhi ho sakta hai)
# Zaroori: Bot ko SOURCE_CHANNEL me ADMIN banao, warna post receive nahi hoga!
@app.on_message(filters.chat(SOURCE_CHANNEL) & (filters.photo | filters.video))
async def on_new_post(client, message):
    """जब source channel me naya photo/video post aayega"""
    await message_queue.put(message)
    print(f"📥 New post queued (queue size: {message_queue.qsize()})")


async def main():
    print("🤖 Starting bot - sirf UPCOMING posts forward honge...")
    asyncio.create_task(queue_worker())
    print("✅ Bot ready. Source channel me naya post aane par forward hoga.")
    print("⚠️  Agar kaam nahi kar raha: Bot ko @terafdbo me ADMIN add karo!")
    from pyrogram import idle
    await idle()


if __name__ == "__main__":
    app.run(main())

