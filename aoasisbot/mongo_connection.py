import pymongo
from pymongo import MongoClient

class connection:

    def start_connection():
        c = MongoClient()
        db = c['AOasisBot']
        return db
