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
ai_active = True

# --- SYSTEM PROMPT ---
system_prompt = """
Tum ek professional aur friendly OTT, Adult, Games subscription seller ho.
Tum incoming users se dosti bhare human style me baat karte ho.
Hard-coded message nahi dete, sabko naturally reply karte ho.
Kisi ko unsolicited message nahi karte.
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

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
Tum ek smart aur friendly OTT subscription seller ho India me.
Tum sabhi major OTT platforms ka subscription sell karte ho:

Netflix, Amazon Prime Video, Disney+ Hotstar, SonyLIV, Zee5, Voot, ALT Balaji, MX Player, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, SunNxt, Hungama Play, ShemarooMe, Lionsgate Play, ManoramaMAX, DocuBay, Epic On, Chaupal, Planet Marathi, Klikk, Addatimes, NammaFlix, Tarang Plus, Aha, TVF Play, Vi Movies & TV, YouTube Premium, Telegram Premium, ChatGPT Subscription bhi bech rahe ho.

Plans:
- 1 Year Plan = ₹500 (Own Email/Number activation, Premium Plan, Max Screen Support, 1 Year Guarantee)
- 6 Months Plan = ₹350 (Random Email Activation, OTP login, same features but random email)
- Combo Offer = Any 4 OTTs 1 Year Plan = ₹1000 (Own Email/Number Activation, Max Screens support, Premium Plans)
- ChatGPT Premium 1 Year Plan = ₹1000

Movie handling:
- Agar user kisi movie ka naam le jaise "Animal", "Dunki", "Pathaan", to batana ki yeh movie kis OTT pe available hai
- Fir friendly bolna ki "OTT buy karlo bhai, full HD dekh paoge ❤️"
PC Games:
- Agar user koi game ka naam le (e.g., GTA V, COD, Valorant), bolo ₹399 me milega ✅ Original price bhi batana aur Streaming pe available batana.

Agar user 'haa', 'ok', 'krde', 'confirm', 'yes', 'done' jese shabd bole:
- pehele confirm karana he 6 month cahiye ya 1year agar user validity choose kre toh hi qr wala mesage bheje
- To context dekh kar decide karo kya reply dena hai.
- Agar lagta hai user payment confirm kar raha hai to "QR code generate ho raha hai bhai ❤️" type ka human funny reply do.
- Agar lagta hai normal casual baat hai to bas friendly dosti bhara normal reply do.
- Hardcoded kabhi kuch na bolo, context samajh ke smart reply do.
- agar costmore zyada force kre toh 50 rs ka discount de dena
- 

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Jab koi gali de to 3 warning ke baad mute kar dena aur reply ignore karna
- Owner agar /stopai bole to bot band karo aur /startai pe wapas chalu karo
- Full human funny comedy style reply dena, robotic mat lagna
- agar user bole ki usko koi or language me baat karna he toh usse age ki baat usilanguage me krna jab tak wo language chnge karne ko na bolea
- user ko bore bilkul nai krna aram se usko full convice krna ki wo buy kare
- jab ott ka price bata rahe ho us time 1 smart comparision dedo official price or hamare price me 
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

    # Owner Controls
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

        # Normal AI Conversation
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
