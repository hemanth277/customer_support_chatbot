from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import db, ecommerce_db
import random
import asyncio
import os
import datetime
import re
from textblob import TextBlob
import nltk

# Ensure NLTK data is available
try:
    nltk.data.find('corpora/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

app = FastAPI()

# Mount frontend files under /static but we'll also serve index at root
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

class MessagePayload(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(payload: MessagePayload):
    user_msg = payload.message.lower()
    
    # Analyze Sentiment
    sentiment_label = "neutral"
    sentiment_score = 0.0
    try:
        analysis = TextBlob(payload.message)
        sentiment_score = analysis.sentiment.polarity
        if sentiment_score < -0.3:
            sentiment_label = "negative"
        elif sentiment_score > 0.3:
            sentiment_label = "positive"
    except Exception as e:
        print(f"Sentiment Analysis Error: {e}")

    # Save user message with sentiment
    await db.messages.insert_one({
        "sender": "user",
        "text": payload.message,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "timestamp": datetime.datetime.utcnow()
    })

    # Simulate a bit of processing delay
    await asyncio.sleep(0.5)

    bot_response = ""
    
    # De-escalation or Appreciation prefix based on sentiment
    tone_prefix = ""
    if sentiment_label == "negative":
        empathy_prefixes = [
            "I'm really sorry for your experience. Let me help you resolve this issue.",
            "I truly understand your frustration and I'm here to solve this for you.",
            "I apologize sincerely for the trouble. Let's work on a solution right away.",
            "I'm sorry to hear you're unhappy with our service. Let me make this right."
        ]
        tone_prefix = random.choice(empathy_prefixes) + " "
    elif sentiment_label == "positive":
        appreciation_prefixes = [
            "Thank you! We're happy to hear that.",
            "That's great to hear! We appreciate your kind words.",
            "We're glad you're happy with our service! How can I assist you further?",
            "Thank you for the positive feedback! It's our pleasure to help."
        ]
        tone_prefix = random.choice(appreciation_prefixes) + " "

    order_match = re.search(r'(ORD\d{4,})', user_msg, re.IGNORECASE)

    if order_match:
        order_id = order_match.group(1).upper()
        # Query MongoDB for the specific order
        order = await ecommerce_db.orders.find_one({"order_id": order_id})
        
        if order:
            status = order.get("order_status", "Processing")
            product = order.get("product", "your item")
            
            bot_response = f"I found your order {order_id} for '{product}'. The current status is **{status}**."
            
            if status.lower() == "delivered":
                bot_response += " I hope you're enjoying your purchase!"
            
            # Check if there was an issue logged for this order
            issue = order.get("issue_type")
            if issue:
                bot_response += f" I also noticed there is a recorded issue regarding '{issue}'. I can guide you through the next steps or connect you to an agent."
        else:
            bot_response = f"I couldn't find order number {order_id} in our records. Please double-check the ID and I'll check again for you!"
            
    elif not user_msg:
        bot_response = "I didn't quite catch that. How can I help you today?"
    elif "hello" in user_msg or "hi" in user_msg:
        bot_response = "Hello! Welcome to ShopEasy Customer Support. Are you inquiring about a recent order?"
    elif "order" in user_msg or "track" in user_msg or "delivery" in user_msg:
        bot_response = "Sure! Please provide your order ID (like ORD5051) and I'll check the status for you."
    elif "return" in user_msg or "refund" in user_msg or "cancel" in user_msg:
        bot_response = "I can certainly help with that. Please provide your order ID so I can guide you through the process."
    elif "payment" in user_msg or "card" in user_msg or "failed" in user_msg:
        bot_response = "If your payment failed, don't worry—no amount was deducted. Please try again or use a different payment method. I'm here if you need more help!"
    elif "human" in user_msg or "agent" in user_msg:
        bot_response = "I'll transfer you to a live ShopEasy representative from our customer care team right away to help you further."
    else:
        fallback_responses = [
            "Could you please share a bit more context about your issue so I can find the best solution?",
            "I'm here to help. Does this pertain to an order you have already placed?",
            "Let me check our policies regarding that. Could you provide some more details?",
            "I want to make sure I understand correctly. How can I best assist you today?",
        ]
        bot_response = random.choice(fallback_responses)
        
    # Apply tone prefix if needed
    full_response = tone_prefix + bot_response

    # Save bot message
    await db.messages.insert_one({
        "sender": "bot",
        "text": full_response,
        "timestamp": datetime.datetime.utcnow()
    })

    return {"response": full_response}

@app.get("/api/history")
async def get_history():
    messages_cursor = db.messages.find().sort("timestamp", 1)
    messages = await messages_cursor.to_list(length=1000)
    return [
        {
            "sender": msg["sender"],
            "text": msg["text"],
            "timestamp": msg.get("timestamp")
        } for msg in messages
    ]

@app.delete("/api/history")
async def clear_history():
    await db.messages.delete_many({})
    return {"status": "cleared"}

@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

app.mount("/", StaticFiles(directory=frontend_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    # On Render, the host must be 0.0.0.0. For local development, 127.0.0.1 is standard.
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"

    uvicorn.run(app, host=host, port=port)
