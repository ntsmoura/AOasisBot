from models import *

def parsingJsonToMongoUpgrade(data,owned):
    list_of_costs = []
    for e in data['costs']:
        try:
            type_c = e['type']
        except KeyError:
            type_c = 'none'
        try:
            count_c = e['count']
        except KeyError:
            count_c = 0
        try: 
            name_c = e['name']
        except KeyError:
            name_c = 'none'
        try: 
            item_id_c = e['item_id']
        except KeyError:
            item_id_c = 0
        cost_object = Cost(type_doc = type_c ,count = count_c,name= name_c,item_id= item_id_c)
        list_of_costs.append(cost_object)
    upgrade_object = Upgrade(up_id = data['id'], name = data['name'], icon = data['icon'], costs = list_of_costs, owned = owned, prerequisites = data['prerequisites']) 
    return upgrade_object