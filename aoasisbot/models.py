#Models for Mongo Objects
import mongoengine

class Users(mongoengine.Document):
    name = mongoengine.StringField()
    api_key = mongoengine.StringField()