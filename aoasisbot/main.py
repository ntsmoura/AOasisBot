#Main.py
import discord
import json
from dotenv import load_dotenv
from models import *
from mongoengine import *
from requests_futures.sessions import FuturesSession
from parsing import *
from PIL import Image
import requests
import os

load_dotenv()

session = FuturesSession() #Session for future requests to GW2 API

client = discord.Client() #Connection do Discord Client

connect(os.getenv("MONGO_DB")) #Connection to mongoDB database

guild_id = os.getenv("GUILD_ID")
access_token = os.getenv("ACCESS_TOKEN")
bot_token = os.getenv("BOT_TOKEN")

skip = 0 #Global var for determine lower bound of search
limit = 0 #Global var for determine upper bound of search
r_upgrades_message = None #Global var which carries the last upgrades_remaining message object
type_m = '0' #Global var for determine type of search

#Debug for confirm connection to Discord client
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    getAllUpgradeData()
    #await channel.send("Hello everyone i'm AOasis bot, i'll be glad if can help you sometime! Type $help for more info about me!")

#Read user message and send a response based on predefined commands
@client.event
async def on_message(message):
    #r_upgrades_message = None
    if message.author == client.user: #Avoid bot auto-response
        return

    '''#Under Construction
    if message.content.startswith('$teste'):
        objeto = Upgrade.objects(prerequisites__all={58,350}).first()
        print(objeto['name'])'''


    #Under Construction
    if message.content.startswith('$help'):
        await message.channel.send("```$select [x] - Select upgrade and shows needed and remaining materials qty for that one - [x] means upgrade id \n" + 
        "$search [x] - Search for upgrades info using its name - [x] means upgrade's name \n"
        + "$upgrades_update - Update info about owned upgrades in Database \n"
        +"$upgrades_remaining 0 - Shows all remaining upgrades\n"
        + "$upgrades_reamining 1 - Shows all remaining upgrades whith owned prerequisites\n"
        + "$treasury_update - Update info about treasury in Database```")

    #Select upgrade and shows needed materials quantity for that one
    if message.content.startswith('$select'):
        content = message.content.split()
        up_info = None
        try:
            up_info = Upgrade.objects(up_id = int(content[1])).first()
        except IndexError as error:
            await message.channel.send('You should try select [x]!')
        if up_info is None:
            await message.channel.send('Upgrade not found!')
        else:
            costs = up_info.costs
            cost_descriptions = []
            for x in costs:
                if x.item_id != 0 and x.item_id != 70701: #70701 is the 'Guild Favor' Id, we don't want to show that
                    item = Item.objects(item_id = x.item_id).first()
                    if item is None:
                        cost_descriptions.append('0/'+ str(x.count) + ' - ' + x.name)
                    else:
                        cost_descriptions.append(str(item.count) + '/' + str(x.count) + ' - ' + x.name)
            embed_message = discord.Embed(title = up_info.name,colour=3066993,description='\n'.join(cost_descriptions))
            embed_message.set_thumbnail(url=up_info.icon)
            await message.channel.send(embed=embed_message)

    #Search for upgrades infos using its name
    if message.content.startswith('$search'):
        message_content = message.content.split()
        name = ""
        description = [] #List of elements with its description
        for e in message_content:
            if e!= '$search':
                name += e + " "
        name = name.rstrip()
        upgrades = Upgrade.objects(name__icontains=name)
        if upgrades is None:
            await message.channel.send("Upgrade not found!")
        else:
            for x in upgrades:
                description.append(str(x.up_id) + " - " + x.name)
            await message.channel.send("``` " + "\n ".join(description) + "```")

    #Upgrade DB data about earned upgrades
    if message.content.startswith('$upgrades_update'):
        request = session.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/upgrades?access_token='+access_token)
        request_result = request.result()
        upgrades = json.loads(request_result.text)
        for e in upgrades:
            upgrade = Upgrade.objects(up_id = e).first() 
            upgrade.owned = True
            upgrade.save()
        await message.channel.send('Upgrades successfully updated!')

    #Show remaining updates based on selected type (0 - All Remaining Upgrades / 1 - Remaining Upgrades with owned prerequisites)
    if message.content.startswith('$upgrades_remaining'):
        global r_upgrades_message
        global skip
        global limit
        global type_m
        skip = 0
        limit = 20
        descriptions=[]
        if r_upgrades_message is not None:
            await r_upgrades_message.delete()
        try: 
            type_m = (message.content.split())[1]
            if(type_m != '0' and type_m != '1'):
                await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')
            else:
                descriptions = upgrades_filter(type_m)
                r_upgrades = await message.channel.send("``` " + "\n ".join(descriptions) + "```")
                emoji_arrow_r = '\U000027A1'
                emoji_arrow_l = '\U00002B05'
                await r_upgrades.add_reaction(emoji_arrow_l)
                await r_upgrades.add_reaction(emoji_arrow_r)
                r_upgrades_message = r_upgrades
        except:
            await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')

    #Upgrade Treasury data in DB
    if message.content.startswith('$treasury_update'):
        request = session.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/treasury?access_token='+access_token)
        request_result = request.result()
        items = json.loads(request_result.text)
        for e in items:
            item = Item.objects(item_id = e['item_id']).first() 
            if item is None:
                db_item = Item(item_id = e['item_id'],count = e['count'])
                db_item.save()
        await message.channel.send('Treasury successfully updated!')
    #Add events
    if message.content.startswith('$event_add'):
        event_data =  message.content.split(" / ")
        list_participant = []
        count = 0
        class_c = 6
        event_data[0] = (event_data[0].split())[1] #Remove $event_add from string
        spots = int(event_data[3])
        n_classes = int(event_data[5])
        while count < spots: #Fill participants list with required roles and empty spots for replace later
            if count == 0:
               p_roles = ["[Running]"]
               p = Participant(nick = event_data[4], roles = p_roles)
            else:
                if class_c <= n_classes + 5:
                    p_roles = [event_data[class_c]]
                    p = Participant(nick=" ", roles = p_roles)
                    class_c += 1
                else:
                    p_roles = [" "]
                    p = Participant(nick=" ",roles = p_roles)
            list_participant.append(p)
            count += 1
        event = Event(code = event_data[0], name = event_data[1], ddht = event_data[2], 
            spots = spots, message_id = 0, description = event_data[n_classes+6], subscribeds = list_participant)
        descript_roles = []
        list_count = 1
        for x in list_participant:
            descript_roles.append(str(list_count) + " - " + x.nick + " " + x.roles[0]) #Fill participant list for discord message content
            list_count+=1
        msg = await message.channel.send("Code: " + event.code + "\nName: " + event.name + "\nDescription: " + event.description + "\nDDHT: " + event.ddht + "\nSpots: " +
            str(event.spots) + "\nLeader: " + event_data[4] + "\nRoles:\n" + "\n".join(descript_roles))
        event.message_id = msg.id
        event.save()

#Wait for reactions and edit the upgrades_remaining content based on which reaction was selected
@client.event
async def on_reaction_add(reaction,user):
    global r_upgrades_message
    global skip
    global limit
    global type_m
    if user!= client.user:
        r_upgrades_message = reaction.message
        if reaction.emoji == '➡':
            skip+=20
            limit+=20
        else:
            if skip>=20:
                skip-=20
            if limit>20:
                limit-=20
        descriptions = upgrades_filter(type_m)
        await r_upgrades_message.edit(content="``` " + "\n ".join(descriptions) + "```")

#Wait for reactions and edit the upgrades_remaining content based on which reaction was selected
@client.event
async def on_reaction_remove(reaction,user):
    global r_upgrades_message
    global skip
    global limit
    global type_m
    if user!= client.user:
        r_upgrades_message = reaction.message
        if reaction.emoji == '➡':
            skip+=20
            limit+=20
        else:
            if skip>=20:
                skip-=20
            if limit>20:
                limit-=20
        descriptions = upgrades_filter(type_m)
        await r_upgrades_message.edit(content="``` " + "\n ".join(descriptions) + "```")

#get all data about Upgrades from GW2 API
def getAllUpgradeData():
    request = session.get('https://api.guildwars2.com/v2/guild/upgrades')
    request_result = request.result()
    data = json.loads(request_result.text)
    for e in data:
        search = Upgrade.objects(up_id = e).first()
        if search is None: 
            e = str(e)
            request = session.get('https://api.guildwars2.com/v2/guild/upgrades/'+e)
            request_result = request.result()
            e_data = json.loads(request_result.text)
            upgrade = parsingJsonToMongoUpgrade(e_data,False)
            upgrade.save()


#Filter type of upgrades query
def upgrades_filter(type_m):
    descriptions = [] #List of elements with its description
    if (type_m == '0'): #If 0 search for all not owned upgrades
        upgrades_r = Upgrade.objects(owned=False)[skip:limit]
        for e in upgrades_r:
            descriptions.append(str(e.up_id) + ' - ' + e.name)
    else: #If 1 search for all not owned upgrades, which guild has the requested prerequisites
        owned_upgrades = Upgrade.objects(owned=True)
        itens = []
        for x in owned_upgrades:
            itens.append(x.up_id)
        upgrades_r = Upgrade.objects(Q(prerequisites__all=itens) | Q(prerequisites=[]) & Q(owned=False))[skip:limit]
        for e in upgrades_r:
            descriptions.append(str(e.up_id) + ' - ' + e.name)
    return descriptions

client.run(bot_token)