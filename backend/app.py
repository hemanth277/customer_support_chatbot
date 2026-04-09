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

app = FastAPI()

# Mount frontend files under /static but we'll also serve index at root
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

class MessagePayload(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(payload: MessagePayload):
    user_msg = payload.message.lower()
    
    # Save user message
    await db.messages.insert_one({
        "sender": "user",
        "text": payload.message,
        "timestamp": datetime.datetime.utcnow()
    })

    # Simulate a bit of processing delay
    await asyncio.sleep(0.5)

    bot_response = ""
    order_match = re.search(r'(ORD\d{4,})', user_msg, re.IGNORECASE)

    if order_match:
        order_id = order_match.group(1).upper()
        # Query MongoDB for the specific order
        order = await ecommerce_db.orders.find_one({"order_id": order_id})
        
        if order:
            status = order.get("order_status", "Processing")
            product = order.get("product", "your item")
            
            bot_response = f"I found your order {order_id} for '{product}'. The current status is **{status}**."
            
            # Check if there was an issue logged for this order
            issue = order.get("issue_type")
            if issue:
                bot_response += f" I also noticed there is an open '{issue}' ticket for this order. I can connect you to an agent if you need further help with that."
        else:
            bot_response = f"I couldn't find order number {order_id} in our records. Please double check the ID and try again!"
            
    elif not user_msg:
        bot_response = "I didn't quite catch that. How can I help you?"
    elif "hello" in user_msg or "hi" in user_msg:
        return {"response": "Hello! Welcome to ShopEasy Customer Support. Are you inquiring about a recent order?"}
    elif "order" in user_msg or "track" in user_msg or "delivery" in user_msg:
        # Don't return here, assign so it gets properly logged
        bot_response = "I can help with that. Could you please provide your order ID? It should look like ORD5051."
    elif "return" in user_msg or "refund" in user_msg or "cancel" in user_msg:
        bot_response = "We offer a 30-day return policy. If you would like to initiate a return or refund for a recent purchase, please give me the Tracking/Order ID."
    elif "payment" in user_msg or "card" in user_msg or "failed" in user_msg:
        bot_response = "If your payment failed during checkout, no amount was deducted. Please try placing the order again or use a different payment method."
    elif "human" in user_msg or "agent" in user_msg:
        bot_response = "I'll transfer you to a live ShopEasy representative from our customer care team right away."
    else:
        fallback_responses = [
            "I'm sorry, I didn't quite catch that. Does this pertain to an order you have already placed?",
            "I understand. Let me check our store policies regarding that.",
            "That's a good question. Can you share a bit more context about your issue?",
            "Can you clarify that so I can find the best solution for your shopping experience?",
        ]
        bot_response = random.choice(fallback_responses)
        
    # Save bot message
    await db.messages.insert_one({
        "sender": "bot",
        "text": bot_response,
        "timestamp": datetime.datetime.utcnow()
    })

    return {"response": bot_response}

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

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(app, host="0.0.0.0", port=port)
