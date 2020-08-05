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

def parsingEventoToEventMessage(event, descript_roles):
    count = 0
    emoji = ""
    spots_message = ""
    for x in event.subscribeds:
        if x.nick != " ":
            count+=1
    if count < 7:
        emoji = "🟩"
        spots_message = str(int(event.spots) - count) + " left!"
    elif count >= 7 and count < 10:
        emoji = "🟨"
        spots_message = str(int(event.spots) - count) + " left!"
    else:
        emoji = "🟥"
        spots_message = "FULL"
    content = ("CODE: **" + event.code + 
        "**\n<:Mastery:728705436387377213> **" + event.name + "** <:Mastery:728705436387377213> " + event.ddht + " " + emoji +
                            spots_message + emoji + "\n" + event.description + "\nList:\n" + "\n".join(descript_roles))
    return content