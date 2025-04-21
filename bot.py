import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai.api_key = os.getenv("OPENAI_API_KEY")
admin_id = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

session_name = "userbot"

client = TelegramClient(session_name, api_id, api_hash)


# --- MEMORY VARIABLES ---
user_context = {}
user_confirm_pending = {}
ai_active = True

# --- SYSTEM PROMPT for GPT ---
system_prompt = """
Tum ek professional aur friendly OTT, Adult, Games subscription seller ho.
Tum incoming users se dosti bhare human style me baat karte ho.
Hard-coded message nahi dete, sabko naturally reply karte ho.
Kisi ko unsolicited message nahi karte.
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'paid', 'payment ho gaya', 'payment done', 'payment hogaya']

# --- TYPING SIMULATION ---
async def send_typing(event):
    try:
        await event.client(functions.messages.SetTypingRequest(
            peer=event.chat_id,
            action=types.SendMessageTypingAction()
        ))
        await asyncio.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"Typing error: {e}")

# --- KEEP ONLINE ---
async def keep_online():
    while True:
        try:
            await client(functions.account.UpdateStatusRequest(offline=False))
        except Exception as e:
            print(f"Online error: {e}")
        await asyncio.sleep(60)

# --- MESSAGE HANDLER ---
@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    # OWNER CONTROL
    if sender_id == admin_id:
        if user_message == '/stopai':
            ai_active = False
            await event.respond("✅ AI replies stopped.")
            return
        if user_message == '/startai':
            ai_active = True
            await event.respond("✅ AI replies resumed.")
            return

    # IF AI OFF
    if not ai_active:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        # Confirm message system
        if any(word in user_message for word in confirm_words):
            if sender_id in user_confirm_pending:
                plan = user_confirm_pending[sender_id]

                user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

                post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
💰 Amount: {plan['price']}
🎯 Subscription: {plan['subscription_name']}
⏳ Validity: {plan['validity']}
"""

                await client.send_message(
                    GROUP_ID,
                    post_text,
                    parse_mode='html'
                )
                del user_confirm_pending[sender_id]

                await event.respond("✅ Payment Confirmed! QR code generate ho raha hai 📲")
                return

        # Normal ChatGPT Conversation
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5,
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        print(f"Error: {e}")
        await event.respond("Bhai thoda error aagaya 😔 Try later.")

# --- START CLIENT ---
client.start()
client.loop.create_task(keep_online())
client.run_until_disconnected()
