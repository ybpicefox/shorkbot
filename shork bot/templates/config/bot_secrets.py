from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient("mongodb+srv://moderation:Baguette@shorkk.caqwk.mongodb.net/?retryWrites=true&w=majority")
db = cluster["database"]
user_collection = db["users"]
moderation_collection = db["moderation"]
prefix = "-"
cogs = [f"cogs.{z[:-3]}" for z in os.listdir('cogs') if z.endswith(".py")]
token = "OTc4OTM0NDg1MzA1NDAxMzQ0.GLuKRw.46gKUn_Wmh4lAfdiTuUG7NIjx7Evrs6e1bswTk"
