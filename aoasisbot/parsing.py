from models import *

def parsingJsonToMongoUpgrade(data):
    list_of_costs = []
    for e in data['costs']:
        cost_object = Cost(type_doc = e['type'],count = e['count'],name=e['name'],item_id=e['item_id'])
        list_of_costs.append(cost_object)
    upgrade_object = Upgrade(up_id = data['id'], name = data['name'], icon = data['icon'], costs = list_of_costs) 
    return upgrade_object