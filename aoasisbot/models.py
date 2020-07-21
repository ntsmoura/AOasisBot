#Models for Mongo Objects
import mongoengine

class User(mongoengine.Document):
    name = mongoengine.StringField()
    api_key = mongoengine.StringField()

class Cost(mongoengine.EmbeddedDocument):
    type_doc = mongoengine.StringField()
    count = mongoengine.IntField()
    name = mongoengine.StringField()
    item_id = mongoengine.IntField()

class Upgrade(mongoengine.Document):
    up_id = mongoengine.IntField()
    name = mongoengine.StringField()
    icon = mongoengine.StringField()
    costs = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Cost))