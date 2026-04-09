from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://admin:admin123@cluster0.h4kkwo4.mongodb.net/?appName=Cluster0"
client = AsyncIOMotorClient(MONGO_URI)
db = client.chatbot_db
ecommerce_db = client["e-commerceDB"]
