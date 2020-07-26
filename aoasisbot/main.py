#Main.py
import discord
import json
from dotenv import load_dotenv
from models import *
from mongoengine import *
from requests_futures.sessions import FuturesSession
from parsing import *
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

#Debug for confirm connection to Discord client
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #await channel.send("Hello everyone i'm AOasis bot, i'll be glad if can help you sometime! Type $help for more info about me!")
    getAllUpgradeData()

#Read user message and send a response based on predefined commands
@client.event
async def on_message(message):
    #r_upgrades_message = None
    if message.author == client.user: #Avoid bot auto-response
        return

    #Under Construction
    if message.content.startswith('$help'):
        await message.channel.send("```$treasury - shows all treasury items \n" + 
        "$upgrades - shows all available upgrades\n$select [x] - shows required items for selected upgrade```")

    #Under Construction
    if message.content.startswith('$select'):
        content = message.content.split()
        up_info = Upgrade.objects(up_id = int(content[1])).first()
        if up_info is None:
            await message.channel.send('Upgrade not found!')
        else:
            await message.channel.send(up_info.name)

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
        skip = 0
        limit = 20
        if r_upgrades_message is not None:
            await r_upgrades_message.delete()
        try: 
            type_m = (message.content.split())[1]
            if(type_m != '0' and type_m != '1'):
                await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')
            else:
                descriptions = [] #List of elements with its description
                if (type_m == '0'):
                    upgrades_r = Upgrade.objects(owned=False)[skip:limit]
                    for e in upgrades_r:
                        descriptions.append(str(e.up_id) + ' - ' + e.name)
                elif  (type_m == '1'):
                    print("nada 1")
                else:
                    print("nada")
                r_upgrades = await message.channel.send("``` " + "\n ".join(descriptions) + "```")
                emoji_arrow_r = '\U000027A1'
                emoji_arrow_l = '\U00002B05'
                await r_upgrades.add_reaction(emoji_arrow_l)
                await r_upgrades.add_reaction(emoji_arrow_r)
                r_upgrades_message = r_upgrades
        except:
            await message.channel.send('You should try $upgrades_remaining 0 or $upgrades_remaining 1 !')

#Wait for reactions and edit the upgrades_remaining content based on which reaction was selected
@client.event
async def on_reaction_add(reaction,user):
    global r_upgrades_message
    global skip
    global limit
    descriptions = []
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
        upgrades_r = Upgrade.objects(owned=False)[skip:limit]
        for e in upgrades_r:
            descriptions.append(str(e.up_id) + ' - ' + e.name)
        await r_upgrades_message.edit(content="``` " + "\n ".join(descriptions) + "```")

#Wait for reactions and edit the upgrades_remaining content based on which reaction was selected
@client.event
async def on_reaction_remove(reaction,user):
    global r_upgrades_message
    global skip
    global limit
    descriptions = []
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
        upgrades_r = Upgrade.objects(owned=False)[skip:limit]
        for e in upgrades_r:
            descriptions.append(str(e.up_id) + ' - ' + e.name)
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
            #print(upgrade.name)


client.run(bot_token)