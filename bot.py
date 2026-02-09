from pyrogram import Client
import asyncio
import random

# ================== CONFIG ==================
API_ID = 25649636
API_HASH = "43af470d1c625e603733268b3c2f7b8f"
BOT_TOKEN = "8463032760:AAHbdPDVDlLwbLVNZpKPG41fSlnbIRSS4Vc"

SOURCE_CHANNEL = -1003748804419  # source channel ID

TARGET_CHANNELS = [
    "-1003553400713",
    "-1003245056110",
    "-1003676653101"
]

POST_DELAY = 600      # 600 = 10 min | 1200 = 20 min
MAX_POSTS = 10        # 🔥 only 10 posts
# ============================================

app = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

last_message_id = 0
forward_count = 0


async def post_job():
    global last_message_id, forward_count

    if forward_count >= MAX_POSTS:
        print("✅ 10 posts forwarded. Bot stopping.")
        return False

    async for msg in app.get_chat_history(
        SOURCE_CHANNEL,
        offset_id=last_message_id,
        limit=1
    ):
        last_message_id = msg.id
        target = random.choice(TARGET_CHANNELS)

        try:
            if msg.photo:
                await app.send_photo(
                    target,
                    photo=msg.photo.file_id,
                    caption=msg.caption or ""
                )

            elif msg.video:
                await app.send_video(
                    target,
                    video=msg.video.file_id,
                    caption=msg.caption or ""
                )

            else:
                print("⏭ Skipped non-media message")
                return True

            forward_count += 1
            print(f"➡️ Forwarded {forward_count}/{MAX_POSTS} to {target}")
            return True

        except Exception as e:
            print(f"❌ Error while sending: {e}")
            return True

    print("⚠️ No more messages in source channel")
    return False


async def main():
    print("🤖 Bot started...")
    while True:
        status = await post_job()
        if not status:
            break
        await asyncio.sleep(POST_DELAY)

    print("🛑 Bot finished work.")


app.run(main())


app.run(main())

