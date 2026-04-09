from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from pprint import pprint

async def find_stuff():
    client = AsyncIOMotorClient('mongodb+srv://admin:admin123@cluster0.h4kkwo4.mongodb.net/?appName=Cluster0')
    # List collections
    db = client.chatbot_db
    cols = await db.list_collection_names()
    print("Collections in chatbot_db:", cols)
    if "orders" in cols:
        print("First order:")
        pprint(await db.orders.find_one())
    
    # Try the main database if it's different
    db2 = client.Cluster0
    cols2 = await db2.list_collection_names()
    print("\nCollections in Cluster0:", cols2)
    if "orders" in cols2:
        print("First order in Cluster0:")
        pprint(await db2.orders.find_one())

asyncio.run(find_stuff())
