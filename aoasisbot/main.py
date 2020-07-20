#Main.py
import discord
import json
import requests
from models import *
from mongoengine import *

client = discord.Client() #Connection do Discord Client

connect('AOasisBot') #Connection to mongoDB database

guild_id = ''
acess_token = ''
bot_token = ''

#Debug for confirm connection to Discord client
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

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
        request = requests.get('https://api.guildwars2.com/v2/guild/upgrades/'+content[1])
        up_info = json.loads(request.text)
        await message.channel.send(up_info['name'])

    #Under Construction
    if message.content.startswith('$upgrades'):
        request = requests.get('https://api.guildwars2.com/v2/guild/'+guild_id+'/upgrades?access_token='+acess_token)
        upgrades = json.loads(request.text)
        descriptions = [] #List of elements with its description
        for e in upgrades:
            e = str(e)
            request = requests.get('https://api.guildwars2.com/v2/guild/upgrades/'+ e)
            e_data = json.loads(request.text)
            e += ' - ' + str(e_data['name'])
            descriptions.append(e)
        await message.channel.send('``` ' + '\n'.join(descriptions) + "```")

    '''if message.content.startswith('$key'):
        content = message.content.split()
        author_name = message.author.name + "#" + str(message.author.discriminator)
        user = Users.objects(name = author_name).first()
        #print(user)
        if user is None:
            user = Users(name = author_name, api_key = content[1])
            user.save()
            await message.channel.send('Api-Key successfully added!')
        else:
            user.api_key = content[1]
            user.save()
            await message.channel.send('Api-Key successfully edited!')
        await message.delete()'''


client.run(bot_token)