# STAY COMMITED TO THIS YOU PIECE OF SHIT
# ALRIGHT BOT TO DO THE FOLLOWING THINGS:
# 1. HAVE A MONGODB WITH EVERY PLAYER THAT'S BEING TRACKER
# 1. A METHOD TO ADD PEOPLE TO BEING TRACKED
# 1. A METHOD TO REMOVE PEOPLE FROM BEING TRACKED
# 1. A METHOD TO CHECK CURRENT LIST OF PEOPLE BEING TRACKED
# LETS START WITH THOSE.

# IMPORTS
import discord
import pymongo
import requests
import json
import os

from discord.ui import View, Button, Select
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# CONFIG SHIT
config_data = open("config.json")
config = json.load(config_data)

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=config["bot_prefix"], intents=intents)


client = pymongo.MongoClient(
    os.getenv("MONGO_LOGIN"))

db = client.PlayerTracker
db_config = db.config
db_players = db.players


@bot.slash_command()
async def setup(ctx: discord.ApplicationContext):
    if db_config.count_documents({}) != 0:
        class test(discord.ui.View):
            @discord.ui.select(
                placeholder="test",
                min_values=1,
                max_values=1,

                options=[
                    discord.SelectOption(
                        label="Yes",
                        description="Continues with current procedure"),
                    discord.SelectOption(
                        label="No",
                        description="Cancels current procedure.")]
            )
            async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
                if select.values[0].lower() == "yes":
                    t = db_config.find_one({"_id": "category"})
                    chans = t["channels"]
                    a = ctx.guild.get_channel(chans[0])
                    for chan in chans:
                        try:
                            await ctx.guild.get_channel(chan).delete()
                        except Exception as error:
                            print("Unable to delete a channel due to: ", error)
                    await a.category.delete()
                    db_config.delete_one(t)
                    await interaction.response.send_message("Category, channels and entry in DB deleted!", ephemeral=True)
                else:
                    await interaction.response.send_message("Procedure cancelled.", ephemeral=True)
        await ctx.respond("Category & channels already exist, delete current ones?", view=test(), ephemeral=True)
    else:
        # now we need to CREATE the channels where the BOT is going to be used.
        # CREATE the CATEGORY that the CHANNELS GO INTO
        category = await ctx.guild.create_category(name="PlayerTracker")

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(send_messages=True),
        }

        tracking = await category.create_text_channel(name="ActiveTracking", overwrites=overwrites)
        commands = await category.create_text_channel(name="Commands", overwrites=overwrites)
        # need to add cats ids and channel ids to db
        db_config.insert_one(
            {"_id": "category", "category": category.id, "channels": [tracking.id, commands.id]})
        await ctx.respond("Created required channels for PlayerTracker.", ephemeral=True)


@bot.slash_command()
async def tracked_server(ctx: discord.ApplicationContext, bmid: int):
    # lets first see what kinda data we can get based on BMID
    data = requests.get(
        url=f"https://api.battlemetrics.com/players/{bmid}/relationships/sessions")
    if data.status_code != 200:
        await ctx.respond(f"Received an error code from Battlemetrics, Error code: { data.status_code}", ephemeral=True)
    parsed_data = json.loads(data.content)

    for entry in parsed_data['data']:
        # print(entry)
        server_id = entry["relationships"]["server"]["data"]["id"]
        if entry["attributes"]["stop"] is not None:
            # means they ARE NOT playing
            continue

       # alright, now we have server id and the server they're currently on. why did we even want this?.
    # print(parsed_data)


@bot.slash_command()
async def add_player(ctx: discord.ApplicationContext, bmid: int):
    # check if BMID is valid.
    data = requests.get(f"https://api.battlemetrics.com/players/{bmid}")
    if data.status_code != 200:
        await ctx.respond(f"Received an error code from Battlemetrics, Error code: {data.status_code}", ephemeral=True)
        print(json.loads(data.content))  # debug ig
    parsed_data = json.loads(data.content)
    name = parsed_data["data"]["attributes"]["name"]
    test = {
        "_id": bmid,
        "name": name,
    }
    # check if bmid is already in the DB.

    if db_players.find_one({"_id": bmid}) is not None:
        await ctx.respond(f"A player has already been entered into the database with that BMID.", ephemeral=True)
    db_players.insert_one(test)
    await ctx.respond(f"Player with name {parsed_data['data']['attributes']['name']} and ID {bmid} has been entered into the database.", ephemeral=True)


@bot.slash_command()
async def remove_player(ctx: discord.ApplicationContext, bmid: int):
    print(db_players.find_one({"_id": bmid}))
    if db_players.find_one({"_id": bmid}) is None:
        await ctx.respond("No player with that BMID has been found in the database.", ephemeral=True)
    db_players.delete_one({"_id": bmid})
    await ctx.respond(f"Entry with BMID {bmid} has been removed from the database", ephemeral=True)


@bot.slash_command()
async def status(ctx: discord.ApplicationContext):
    # get every player in the database and show them in a nice EMBED format.

    if db_players.count_documents({}) == 0:
        await ctx.respond("No players are currently being tracked", ephemeral=True)
    embed = discord.Embed(
        title="Users currently being tracked.", colour=0x328fc)

    for player in db_players.find({}):

        # check if player is online and what server.
        data = requests.get(
            url=f"https://api.battlemetrics.com/players/{player['_id']}/relationships/sessions")
        if data.status_code != 200:
            value = f"Unable to check player server history due to {data.status_code}."
            embed.add_field(name=player["name"], value=value, inline=True)

        else:
            parsed_data = json.loads(data.content)
            for entry in parsed_data['data']:
                # print(entry)
                server_id = entry["relationships"]["server"]["data"]["id"]
                if entry["attributes"]["stop"] is None:
                    # gets here IF stop is None
                    # get server name from server_id
                    server_data = requests.get(
                        f"https://api.battlemetrics.com/servers/{server_id}")
                    server_name = json.loads(server_data.content)[
                        "data"]["attributes"]["name"]
                    value = f"Online: ***True*** \n Server name: {server_name} \n [BM link](https://www.battlemetrics.com/players/{player['_id']})"
                    embed.add_field(
                        name=player["name"], value=value, inline=True)
                    break
            print("weirds")
    await ctx.respond(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    pass

bot.run(os.getenv("DISCORD_TOKEN"))
