import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai

# --- Load from Railway Environment Variables ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai.api_key = os.getenv("OPENAI_API_KEY")
admin_id = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

session_name = "userbot"

client = TelegramClient(session_name, api_id, api_hash)

# --- MEMORY ---
user_context = {}
user_confirm_pending = {}
user_selected_product = {}
ai_active = True

# --- SYSTEM PROMPT ---
system_prompt = """
Tum ek professional aur friendly OTT, Adult, Games subscription seller ho.
Tum incoming users se dosti bhare human style me baat karte ho.
Hard-coded message nahi dete, sabko naturally reply karte ho.
Kisi ko unsolicited message nahi karte.

Services:
- OTT: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, YouTube Premium, Telegram Premium etc.
- Adult Sites: (poora list available on request), 6 months ₹300, 1 year ₹500
- PC BGMI Hacks: Titan, Falcone, Vision, Lethal, Sharpshooter, rooted & non-rooted available
- iOS Hacks: Shoot360, WinIOS, iOSZero

Pricing:
- OTT 1 Year ₹500 (Own Email)
- OTT 6 Months ₹350 (Random Email)
- Combo 4 OTT 1 Year ₹1000
- Hack Week ₹800 / Month ₹1300
- ChatGPT Premium 1 Year ₹1000

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- user ko 4 ott choose krne ka option bhi dena 
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Jab koi gali de to 3 warning ke baad mute kar dena aur reply ignore karna
- Owner agar /stopai bole to bot band karo aur /startai pe wapas chalu karo
- Full human funny comedy style reply dena, robotic mat lagna
- agar user bole ki usko koi or language me baat karna he toh usse age ki baat usilanguage me krna jab tak wo language chnge karne ko na bolea
- user ko bore bilkul nai krna aram se usko full convice krna ki wo buy kare
- jab ott ka price bata rahe ho us time 1 smart comparision dedo official price or hamare price me 
- user ko thoda bhi shak nai hona cahiyee ki tum ai ya bot ho tumhra naam suraj he
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'paid', 'payment ho gaya', 'payment done', 'payment hogaya']

# --- Typing Simulation ---
async def send_typing(event):
    try:
        await event.client(functions.messages.SetTypingRequest(
            peer=event.chat_id,
            action=types.SendMessageTypingAction()
        ))
        await asyncio.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"Typing error: {e}")

# --- Keep Always Online ---
async def keep_online():
    while True:
        try:
            await client(functions.account.UpdateStatusRequest(offline=False))
        except Exception as e:
            print(f"Online error: {e}")
        await asyncio.sleep(60)

# --- Message Handler ---
@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    if sender_id == admin_id:
        if user_message == '/stopai':
            ai_active = False
            await event.respond("✅ AI replies stopped.")
            return
        if user_message == '/startai':
            ai_active = True
            await event.respond("✅ AI replies resumed.")
            return

    if not ai_active:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        # Confirm Handling
        if any(word in user_message for word in confirm_words):
            if sender_id in user_confirm_pending:
                plan = user_confirm_pending[sender_id]
                user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

                post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Subscription: {plan['product']}
💰 Amount: {plan['price']}
⏳ Validity: {plan['validity']}
"""
                await client.send_message(
                    GROUP_ID,
                    post_text,
                    parse_mode='html'
                )
                await event.respond("✅ Payment Confirmed! QR code generate ho raha hai 📲")
                del user_confirm_pending[sender_id]
                return

        # Product detection from user message
        products = ["netflix", "prime", "hotstar", "sony", "zee5", "voot", "mx player", "ullu", "hoichoi", "eros", "jio", "discovery", "shemaroo", "alt", "sun", "aha", "youtube", "telegram", "chatgpt", "adult", "hack", "bgmi", "falcone", "vision", "lethal", "titan", "shoot360", "win", "ioszero"]
        matched = [p for p in products if p in user_message]

        if matched and sender_id not in user_confirm_pending:
            selected_product = matched[0].capitalize()
            user_selected_product[sender_id] = selected_product
            await event.respond(f"✅ {selected_product} ke liye kitni validity chahiye bhai? 6 months ya 1 year?")
            return

        # Validity handling
        if "6 month" in user_message or "6 months" in user_message:
            if sender_id in user_selected_product:
                product = user_selected_product[sender_id]
                price = "₹350" if product.lower() in ["netflix", "prime", "hotstar", "sony", "zee5", "youtube", "telegram"] else "₹300"
                user_confirm_pending[sender_id] = {
                    "product": product,
                    "validity": "6 Months",
                    "price": price
                }
                await event.respond("✅ 6 Months selected bhai! Confirm karo (haa/ok/krde).")
                return

        if "1 year" in user_message or "12 months" in user_message:
            if sender_id in user_selected_product:
                product = user_selected_product[sender_id]
                price = "₹500" if product.lower() in ["netflix", "prime", "hotstar", "sony", "zee5", "youtube", "telegram"] else "₹500"
                user_confirm_pending[sender_id] = {
                    "product": product,
                    "validity": "1 Year",
                    "price": price
                }
                await event.respond("✅ 1 Year selected bhai! Confirm karo (haa/ok/krde).")
                return

        # Normal AI conversation
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

# --- Start Client ---
client.start()
client.loop.create_task(keep_online())
client.run_until_disconnected()
