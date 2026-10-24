
import os
import telebot
import requests
from dotenv import load_dotenv

# ================= CONFIGURATION =================

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

if not API_TOKEN:
    raise ValueError("API_TOKEN .env file mein missing hai!")

if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_KEY .env file mein missing hai!")

bot = telebot.TeleBot(API_TOKEN)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ================= CUSTOM REPLIES =================

CUSTOM_REPLIES = {
    "hi": "Hello! 👋 Kaise hain aap?",
    "hello": "Hello! Main aapki kya madad kar sakta hoon?",
    "namaste": "नमस्ते! कैसे हैं आप? 🙏",
    "price": "Hamari pricing website par check karein: example.com/pricing",
    "contact": "Aap humse 9876543210 par contact kar sakte hain.",
    "help": "Main aapki kis cheez mein madad kar sakta hoon?",
    "bye": "Bye! Phir milte hain 👋",
    "thanks": "Welcome! 😊",
    "thank you": "You're welcome! 😊",
    "shivam": "Shivam abhi so rahe hain 😴",
}


# ================= CUSTOM REPLY FUNCTION =================

def get_custom_reply(user_message):
    msg = user_message.lower().strip()

    for keyword, reply in CUSTOM_REPLIES.items():
        if keyword in msg:
            return reply

    return None


# ================= AI REPLY FUNCTION =================

def get_ai_reply(user_message):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly and helpful Telegram assistant. "
                    "Reply in the same language as the user. "
                    "If the user writes in Hindi or Hinglish, "
                    "reply in Hindi or Hinglish. "
                    "Keep answers clear and conversational."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=40,
        )

        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [])

        if not choices:
            print("OpenRouter returned no choices:", data)
            return "Sorry, abhi AI response nahi mil paya. Dobara try karein."

        answer = choices[0].get("message", {}).get("content", "")

        if not isinstance(answer, str) or not answer.strip():
            return "Sorry, mujhe abhi proper response nahi mila."

        return answer.strip()

    except requests.exceptions.Timeout:
        print("Error: OpenRouter request timeout.")
        return "AI response mein der ho rahi hai. Thodi der baad try karein."

    except requests.exceptions.HTTPError as error:
        print("OpenRouter HTTP error:", error)
        print("API response:", response.text[:1000])

        if response.status_code == 401:
            return "AI API key invalid hai. Admin se contact karein."

        if response.status_code == 429:
            return "AI ki request limit poori ho gayi hai. Thodi der baad try karein."

        return "AI service mein problem hai. Thodi der baad try karein."

    except requests.exceptions.RequestException as error:
        print("Network error:", error)
        return "Internet ya AI service mein problem hai. Dobara try karein."

    except (ValueError, KeyError, IndexError, TypeError) as error:
        print("Response processing error:", error)
        return "AI response process nahi ho paya. Dobara try karein."


# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text"])
def handle_message(message):
    user_message = (message.text or "").strip()

    if not user_message:
        return

    first_name = message.from_user.first_name or "User"

    print(f"Message from {first_name}: {user_message}")

    try:
        bot.send_chat_action(message.chat.id, "typing")

        # First priority: custom replies
        custom_reply = get_custom_reply(user_message)

        if custom_reply:
            bot.reply_to(message, custom_reply)
            print("Custom reply sent successfully.")
            return

        # Otherwise: AI response
        ai_reply = get_ai_reply(user_message)

        # Telegram messages have a length limit.
        # Send long answers in smaller chunks.
        for start in range(0, len(ai_reply), 4000):
            bot.send_message(
                message.chat.id,
                ai_reply[start:start + 4000],
                reply_to_message_id=(
                    message.message_id if start == 0 else None
                ),
            )

        print("AI reply sent successfully.")

    except Exception as error:
        print("Telegram bot error:", error)


# ================= START BOT =================

if __name__ == "__main__":
    print("🤖 Telegram bot successfully start ho raha hai...")

    try:
        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30,
        )

    except KeyboardInterrupt:
        print("Bot manually stop kar diya gaya.")

    except Exception as error:
        print("Bot stopped due to error:", error)
