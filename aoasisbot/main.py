import discord
import requests
from mongo_connection import connection

client = discord.Client()

db = connection.start_connection()
users = db.users
#print(users.find({'name':'Natlox#5854'}))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$help'):
        await message.channel.send("```$treasury - shows all treasury items \n" + 
        "$upgrades - shows all available upgrades\n$select [x] - shows required items for selected upgrade```")

    if message.content.startswith('$select'):
        upgrade = message.content.split()
        print (upgrade[1])
        r = requests.get('https://api.guildwars2.com/v2/guild/upgrades/'+upgrade[1])
        await message.channel.send(r.text)

    #if message.content.startswith('$info'):
        #await message.channel.send(message.author)


client.run('token')