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
    get_upgrade_data()
    #await channel.send("Hello everyone i'm AOasis bot, i'll be glad if can help you sometime! Type $help for more info about me!")

#Read user message and send a response based on predefined commands
@client.event
async def on_message(message):
    #r_upgrades_message = None
    if message.author == client.user: #Avoid bot auto-response
        return

    '''if message.content.startswith('$teste'):
        roles = message.author.roles
        if role_search(roles):
            print("Found!")
        else:
            print("Not found!")'''

    #Show help about upgrades
    if message.content.startswith('$upgrades_help'):
        await message.channel.send("```$select ID - Select upgrade and shows needed and remaining materials qty for that one\n" 
        + "______________________________________________________________________\n"
        + "$search NAME - Search for upgrades info using its name\n"
        + "______________________________________________________________________\n"
        + "$upgrades_update - Update info about owned upgrades in Database \n"
        + "______________________________________________________________________\n"
        +"$upgrades_remaining 0 - Shows all remaining upgrades\n"
        + "$upgrades_reamining 1 - Shows all remaining upgrades whith owned prerequisites\n"
        + "______________________________________________________________________\n"
        + "$treasury_update - Update info about treasury in Database```")

    #Show help about events
    if message.content.startswith('$event_help'):
        await message.channel.send("```\n"
        + "PS: THE SPACES BETWEEN '/' ARE CRUCIAL, PLEASE TAKE CARE!\n"
        + "______________________________________________________________________\n"
        + "$event_add - Add and open event for signup. \n" 
        + "FORMAT: $event_add CODE / TITLE / DATE TIME / SPOTS / @Leader | INGAME NAME | / QNT OF NEEDED ROLES / NEEDED ROLE 1 / NEEDED ROLE 2 / ... / NEEDED ROLE X / DESCRIPTION \n" 
        + "______________________________________________________________________\n"
        + "$signup - signup user in an event\n" 
        + "FORMAT: $signup CODE / SPOT POSITION / @you | IGN NAME | / ROLES\n" 
        + "EXAMPLE: $signup RD1 / 2 / @AOasis Bot |GoodMan.6207| / [1. HealBrand] [2.Power Banner] \n" 
        + "______________________________________________________________________\n"
        + "$remove_user CODE SPOT  - remove selected user from event list\n" 
        + "$remove_event CODE - remove selected event\n" 
        + "______________________________________________________________________\n"
        + "$edit_event - edit event name, date time or description.\n" 
        + "FORMAT: $edit_event CODE / TYPE / CONTENT\nTYPES : 1 - Name ; 2 - Date Time ; 3 - Description ```")
        
    #Select upgrade and shows needed materials quantity for that one
    if message.content.startswith('$select'):
        if role_search(message.author.roles):
            content = message.content.split()
            up_info = None
            try:
                up_info = Upgrade.objects(up_id = int(content[1])).first()
            except IndexError as error:
                msg = await message.channel.send('You should try select ID!')
                await msg.delete(delay=10)
            if up_info is None:
                msg = await message.channel.send('Upgrade not found!')
                await msg.delete(delay = 10)
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
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)
        await message.delete(delay=10)

    #Search for upgrades infos using its name
    if message.content.startswith('$search'):
        if role_search(message.author.roles):
            message_content = message.content.split()
            name = ""
            description = [] #List of elements with its description
            for e in message_content:
                if e!= '$search':
                    name += e + " "
            name = name.rstrip()
            upgrades = Upgrade.objects(name__icontains=name)
            if upgrades is None:
                msg = await message.channel.send("Upgrade not found!")
                await msg.delete(delay=10)
            else:
                try:
                    for x in upgrades:
                        description.append(str(x.up_id) + " - " + x.name)
                    await message.channel.send("``` " + "\n ".join(description) + "```")
                except:
                    msg = await message.channel.send("A lot of results, please be more precise.")
                    await msg.delete(delay = 10)
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)

    #Upgrade DB data about earned upgrades
    if message.content.startswith('$upgrades_update'):
        if role_search(message.author.roles):
            request = session.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/upgrades?access_token='+access_token)
            request_result = request.result()
            upgrades = json.loads(request_result.text)
            for e in upgrades:
                upgrade = Upgrade.objects(up_id = e).first() 
                upgrade.owned = True
                upgrade.save()
            msg = await message.channel.send('Upgrades successfully updated!')
            await msg.delete(delay=10)
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)
        await message.delete(delay=10)

    #Show remaining updates based on selected type (0 - All Remaining Upgrades / 1 - Remaining Upgrades with owned prerequisites)
    if message.content.startswith('$upgrades_remaining'):
        if role_search(message.author.roles):
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
                    msg = await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')
                    await msg.delete(delay=10)
                else:
                    descriptions = upgrades_filter(type_m)
                    r_upgrades = await message.channel.send("``` " + "\n ".join(descriptions) + "```")
                    emoji_arrow_r = '\U000027A1'
                    emoji_arrow_l = '\U00002B05'
                    await r_upgrades.add_reaction(emoji_arrow_l)
                    await r_upgrades.add_reaction(emoji_arrow_r)
                    r_upgrades_message = r_upgrades
            except:
                msg = await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')
                msg.delete(delay=10)
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)
        await message.delete(delay=10)

    #Upgrade Treasury data in DB
    if message.content.startswith('$treasury_update'):
        if role_search(message.author.roles):
            request = session.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/treasury?access_token='+access_token)
            request_result = request.result()
            items = json.loads(request_result.text)
            for e in items:
                item = Item.objects(item_id = e['item_id']).first() 
                if item is None:
                    db_item = Item(item_id = e['item_id'],count = e['count'])
                    db_item.save()
            msg = await message.channel.send('Treasury successfully updated!')
            await msg.delete(delay=10)
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)
        await message.delete(delay=10)

    #Add events
    if message.content.startswith('$event_add'):
        try:
            if role_search(message.author.roles):
                event_data =  message.content.split(" / ")
                list_participant = []
                count = 0
                class_c = 6
                event_data[0] = (event_data[0].split())[1] #Remove $event_add from string
                if Event.objects(code = event_data[0]).first() is None:
                    spots = int(event_data[3])
                    n_classes = int(event_data[5])
                    while count < spots: #Fill participants list with required roles and empty spots for replace later
                        if count == 0:
                            p_roles = "[Running]"
                            p = Participant(nick = event_data[4], roles = p_roles)
                        else:
                            if class_c <= n_classes + 5:
                                p_roles = event_data[class_c]
                                p = Participant(nick=" ", roles = p_roles)
                                class_c += 1
                            else:
                                p_roles = " "
                                p = Participant(nick=" ",roles = p_roles)
                        list_participant.append(p)
                        count += 1
                    event = Event(code = event_data[0], name = event_data[1], ddht = event_data[2], active = True,
                        spots = spots, message_id = 0, description = event_data[n_classes+6], subscribeds = list_participant)
                    descript_roles = []
                    list_count = 1
                    descript_roles = create_spot_list(event)
                    msg = await message.channel.send(parsingEventToEventMessage(event,descript_roles))
                    event.message_id = msg.id
                    event.save()
                else:
                    msg = await message.channel.send("Event code already used. Try another code!")
                    await msg.delete(delay=10)
            else:
                msg = await message.channel.send("You don't have the required role for this command! Sorry.")
                await msg.delete(delay=10)
        except (IndexError, ValueError, TypeError):
            msg = await message.channel.send("Wrong command format. Type $event_help for help.")
            await msg.delete(delay=10)
        await message.delete(delay = 10) 

    #Signup Guild member in the selected event
    if message.content.startswith('$signup'):
        try:
            msg = message.content.split(" / ")
            code = (msg[0].split())[1] #Remove $signup from string
            event = Event.objects(code=code).first()
            if event is None:
                await message.channel.send("Event not found!")
            else:
                if event.subscribeds[int(msg[1])-1].nick != " ":
                    filled_msg = await message.channel.send(message.author.mention + " Spot Filled!")
                    await filled_msg.delete(delay = 10)
                else:
                    event.subscribeds[int(msg[1])-1].nick = msg[2]
                    event.subscribeds[int(msg[1])-1].roles = msg[3]
                    event.save()
                    success_msg = await message.channel.send(message.author.mention + " Successful subscription: " + event.name + "!")
                event = Event.objects(code=code).first() #Searching for updated event to edit discord message
                descript_roles = create_spot_list(event)
                content = parsingEventToEventMessage(event,descript_roles)
                old_msg = await message.channel.fetch_message(event.message_id)
                await old_msg.edit(content = content)
                try:
                    await success_msg.delete(delay = 10)
                except:
                    pass
        except (IndexError, ValueError, TypeError):
            msg = await message.channel.send(message.author.mention + " Wrong command format. Type $event_help for help.")
            await msg.delete(delay=10)
        await message.delete(delay = 10)  

    #Remove event and delete its Discord message
    if message.content.startswith("$remove_event"):
        if role_search(message.author.roles):
            try:
                code = message.content.split()[1]
            except IndexError:
                code = ""
            event = Event.objects(code=code).first()
            if event is None:
                nfound_msg = await message.channel.send("Event not found!")
                await nfound_msg.delete(delay = 10)
            else:
                msg_id = event.message_id
                event.delete()
                deleted_msg = await message.channel.send("Event deleted!")
                old_msg = await message.channel.fetch_message(event.message_id)
                await old_msg.delete()
                await deleted_msg.delete(delay = 10)
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)  
        await message.delete(delay = 10) 
    
    #Remove user from any event
    if message.content.startswith("$remove_user"):
        if role_search(message.author.roles):
            splited_message = message.content.split()
            try:
                code = splited_message[1]
                position = int(splited_message[2])
                event = Event.objects(code=code).first()
                if event is None:
                    nfound_msg = await message.channel.send("Event not found!")
                    await nfound_msg.delete(delay = 10)
                elif (position > event.spots or position < 1):
                    nfound_msg = await message.channel.send("Position not found!")
                    await nfound_msg.delete(delay = 10)
                else:
                    event.subscribeds[position-1].nick = " "
                    try:
                        event.subscribeds[position-1].roles = splited_message[3]
                    except IndexError:
                        event.subscribeds[position-1].roles = " "
                    event.save()
                    event = Event.objects(code=code).first() #Searching for updated event to edit discord message
                    descript_roles = create_spot_list(event)
                    content = parsingEventToEventMessage(event,descript_roles)
                    old_msg = await message.channel.fetch_message(event.message_id)
                    await old_msg.edit(content = content)
            except (IndexError, ValueError, TypeError):
                msg = await message.channel.send("Wrong command format. Type $event_help for help.")
                await msg.delete(delay=10)  
        else:
            msg = await message.channel.send("You don't have the required role for this command! Sorry.")
            await msg.delete(delay=10)  
        await message.delete(delay = 10)

    #Edit selected content of event (Name, Description, Date/Time)
    if message.content.startswith('$edit_event'):
        try:
            msg = message.content.split(" / ")
            code = (msg[0].split())[1] #Remove $edit_event from string
            edit_type = msg[1].strip()
            edit_content = msg[2]
            event = Event.objects(code=code).first()
            if event is None:
                nfound_msg = await message.channel.send("Event not found!")
                await nfound_msg.delete(delay=10)
            else:
                if edit_type == "1":
                    event.name = edit_content
                elif edit_type == "2":
                    event.ddht = edit_content
                elif edit_type == "3":
                    event.description = edit_content
                else:
                    msg = await message.channel.send("Type not found! Try 1 - Name / 2 - Date|Time / 3 - Description.")
                    await msg.delete(delay=10)
                    return
                event.save() 
                event = Event.objects(code=code).first() #Searching for updated event to edit discord message
                descript_roles = create_spot_list(event)
                content = parsingEventToEventMessage(event,descript_roles)
                old_msg = await message.channel.fetch_message(event.message_id)
                await old_msg.edit(content = content)
                success_msg = await message.channel.send("Event successfully edited!") 
                await success_msg.delete(delay = 10)
        except (IndexError, ValueError, TypeError):
            msg = await message.channel.send("Wrong command format. Type $event_help for help.")
            await msg.delete(delay=10)
        await message.delete(delay = 10) 
        
         

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
def get_upgrade_data():
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

#Search for required roles
def role_search(roles):
    for x in roles:
        if x.name == "Exalted":
            return True
    return False


#Get list of spots from event
def create_spot_list(event):
    list_count = 1
    descript_roles = []
    for x in event.subscribeds:
        descript_roles.append(str(list_count) + " - " + x.nick + " " + x.roles) #Fill participant list for discord message content
        list_count+=1
    return descript_roles

client.run(bot_token)