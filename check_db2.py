from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from pprint import pprint

async def find_stuff():
    client = AsyncIOMotorClient('mongodb+srv://admin:admin123@cluster0.h4kkwo4.mongodb.net/?appName=Cluster0')
    dbs = await client.list_database_names()
    print("Databases:", dbs)
    for d in dbs:
        db = client[d]
        cols = await db.list_collection_names()
        if cols:
            print(f"-- {d} collections:", cols)
            for c in cols:
                count = await db[c].count_documents({})
                print(f"    - {c}: {count} documents")
                if "order" in c.lower() and count > 0:
                    doc = await db[c].find_one()
                    print(f"      Example {c} doc:")
                    pprint(doc)

asyncio.run(find_stuff())
