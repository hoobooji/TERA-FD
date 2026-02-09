from pyrogram import Client
import asyncio
import os

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "25649636"))
API_HASH = os.environ.get("API_HASH", "43af470d1c625e603733268b3c2f7b8f")
# User Client ke liye SESSION_STRING chahiye (Bot nahi!)
# session_maker.py chala kar banao, phir Heroku Config Var me add karo
SESSION_STRING = os.environ.get("SESSION_STRING", "")

SOURCE_CHANNEL = "@terafdbo"  # एक सोर्स चैनल

TARGET_CHANNELS = [
    "-1003553400713",
    "-1003245056110",
    "-1003676653101"
]

POST_DELAY = 600      # 600 sec = 10 min | 1200 = 20 min
MAX_POSTS = 10        # max 10 posts
# ============================================

# User Client (Bot nahi) - get_chat_history sirf User se kaam karta hai
app = Client(
    "forward_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

last_message_id = 0
forward_count = 0


async def post_job():
    """एक सोर्स से पोस्ट लेकर अलग-अलग चैनल में भेजता है (round-robin)"""
    global last_message_id, forward_count

    if forward_count >= MAX_POSTS:
        print("✅ 10 posts forwarded. Stopping.")
        return "stop"

    async for msg in app.get_chat_history(
        SOURCE_CHANNEL,
        offset_id=last_message_id,
        limit=1
    ):
        last_message_id = msg.id

        # हर पोस्ट अलग चैनल में (round-robin: 1→ch1, 2→ch2, 3→ch3, 4→ch1...)
        channel_index = forward_count % len(TARGET_CHANNELS)
        target = TARGET_CHANNELS[channel_index]

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
            print("⏭ Skipped non-media message")
            return "skipped"

        forward_count += 1
        print(f"➡️ Forwarded {forward_count}/{MAX_POSTS} to {target}")
        return "forwarded"

    print("⚠️ No more messages found")
    return "stop"


async def main():
    if not SESSION_STRING:
        print("❌ ERROR: SESSION_STRING missing!")
        print("   Bot get_chat_history use nahi kar sakta. User Client chahiye.")
        print("   Run: python session_maker.py")
        print("   Phir Heroku Config Vars me SESSION_STRING add karo.")
        return
    print("🤖 Starting bot (User Client)...")
    await app.start()

    while True:
        status = await post_job()
        if status == "stop":
            break
        # सिर्फ successful forward के बाद 10 min wait
        if status == "forwarded":
            await asyncio.sleep(POST_DELAY)

    await app.stop()
    print("🛑 Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
