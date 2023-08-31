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
                        await ctx.guild.get_channel(chan).delete()
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
        # NOW WE NEED TO CREATE THE CHANNELS.
        # UHH WHAT CHANNELS DO WE NEED
        # 1. CONSTANTLY UPDATING LIST OF PEOPLE THAT ARE BEING TRACKED
        # 2. CHANNEL TO RUN COMMANDS IN? normal ones

        # channel rules
        # SHOULD SHOW WHAT ROLES CAN BE SELECTED HERE
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
async def tracked_server(ctx: discord.ApplicationContext, server_to_be_tracked: int):
    # need to check if a server has already been selected
    doc = db_config.find_one({"_id": "server"})
    if doc["server"] != None:
        # A SERVER HAS ALREADY BEEN CHOSEN !!!!!!
        # just say fuck it and delete previous one.
        # check if server actually exists though on BM
        api_data = requests.get
        pass
    else:
        pass
        # A SERVER HAS NOT BEEN CHOSEN YET!!!!!!!!


@bot.slash_command()
async def add_player(ctx: discord.ApplicationContext):
    pass


@bot.slash_command()
async def remove_player(ctx: discord.ApplicationContext):
    pass


@bot.slash_command()
async def status(ctx: discord.ApplicationContext):
    pass


@bot.event
async def on_ready():
    pass

bot.run(os.getenv("DISCORD_TOKEN"))
