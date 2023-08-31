import pymongo
import os

client = pymongo.MongoClient(
    "mongodb+srv://ADMIN:administrator123@cluster0.cjvxfvy.mongodb.net/")

db = client.PlayerTracker
db_config = db.config
db_players = db.players

data = {
    "_id": "server",
    "server": 123
}
db_config.insert_one(data)
