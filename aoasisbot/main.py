#Main.py
import discord
import json
from dotenv import load_dotenv
from models import *
from mongoengine import *
from requests_futures.sessions import FuturesSession
from parsing import *
import requests

load_dotenv()

session = FuturesSession() #Session for future requests to GW2 API

client = discord.Client() #Connection do Discord Client

connect(os.getenv("MONGO_DB")) #Connection to mongoDB database

guild_id = os.getenv("GUILD_ID")
access_token = os.getenv("ACCESS_TOKEN")
bot_token = os.getenv("BOT_TOKEN")

#Debug for confirm connection to Discord client
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    getAllUpgradeData()

#Read user message and send a response based on predefined commands
@client.event
async def on_message(message):
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
        request = session.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/upgrades?access_token='+acess_token)
        request_result = request.result()
        upgrades = json.loads(request_result.text)
        descriptions = [] #List of elements with its description
        for e in upgrades:
            upgrade = Upgrade.objects(up_id = e).first() 
            upgrade.owned = True
            upgrade.save()
        await message.channel.send('Upgrades successfully updated!')

    #Show remaining updates based on selected type (under construction)
    if message.content.startswith('$upgrades_remaining'):
        type_m = (message.content.split())[1]
        descriptions = [] #List of elements with its description
        for e in data:
            search = Upgrade.objects(up_id = e).first()
            if search is None: 
                e = str(e)
                request = session.get('https://api.guildwars2.com/v2/guild/upgrades/'+e)
                request_result = request.result()
                e_data = json.loads(request_result.text)
                descriptions.append(str(e_data['id']) + ' - ' + e_data['name'])

#get all data about Upgrades from GW2 API
def getAllUpgradeData():
    request = session.get('https://api.guildwars2.com/v2/guild/upgrades')
    request_result = request.result()
    data = json.loads(request_result.text)
    descriptions = [] #List of elements with its description
    for e in data:
        search = Upgrade.objects(up_id = e).first()
        if search is None: 
            e = str(e)
            request = session.get('https://api.guildwars2.com/v2/guild/upgrades/'+e)
            request_result = request.result()
            e_data = json.loads(request_result.text)
            descriptions.append(str(e_data['id']) + ' - ' + e_data['name'])
            upgrade = parsingJsonToMongoUpgrade(e_data,False)
            upgrade.save()
            print(upgrade.name)

client.run(bot_token)