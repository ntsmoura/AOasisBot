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
    owned = mongoengine.BooleanField()
    costs = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Cost))
    prerequisites = mongoengine.ListField(mongoengine.IntField())

class Item(mongoengine.Document):
    item_id = mongoengine.IntField()
    count = mongoengine.IntField()

class Participant(mongoengine.EmbeddedDocument):
    nick = mongoengine.StringField()
    roles = mongoengine.StringField()

class Event(mongoengine.Document):
    code = mongoengine.StringField()
    name = mongoengine.StringField()
    ddht = mongoengine.StringField()
    active = mongoengine.BooleanField()
    spots = mongoengine.IntField()
    message_id = mongoengine.IntField()
    description = mongoengine.StringField()
    subscribeds = mongoengine.ListField(mongoengine.EmbeddedDocumentField(Participant))

class Joke(mongoengine.Document):
    descript = mongoengine.StringField()
