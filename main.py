import discord
import pymongo
import requests
import json
import os


from discord.ext import commands, tasks
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=os.getenv("BOT_PREFIX"), intents=intents)


client = pymongo.MongoClient(
    os.getenv("MONGO_LOGIN"))

db = client.PlayerTracker
db_config = db.config
db_players = db.players


@bot.slash_command()
async def setup(ctx: discord.ApplicationContext, server_id: int = None):
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
        category = await ctx.guild.create_category(name="PlayerTracker")

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(send_messages=True),
        }

        tracking = await category.create_text_channel(name="ActiveTracking", overwrites=overwrites)
        commands = await category.create_text_channel(name="Commands", overwrites=overwrites)
        # need to add cats ids and channel ids to db
        db_config.insert_one(
            {"_id": "category", "category": category.id, "server_id": server_id, "channels": [tracking.id, commands.id]})
        await ctx.respond("Created required channels for PlayerTracker.", ephemeral=True)


@bot.slash_command()
async def add_player(ctx: discord.ApplicationContext, bmid: int):
    data = requests.get(f"https://api.battlemetrics.com/players/{bmid}")
    if data.status_code != 200:
        await ctx.respond(f"Received an error code from Battlemetrics, Error code: {data.status_code}", ephemeral=True)
        print(json.loads(data.content))  # debug ig
    parsed_data = json.loads(data.content)
    name = parsed_data["data"]["attributes"]["name"]

    if db_players.find_one({"_id": bmid}) is not None:
        await ctx.respond(f"A player has already been entered into the database with that BMID.", ephemeral=True)

    seen_data = requests.get(
        f"https://api.battlemetrics.com/players/{bmid}/servers/{db_config.find_one({'_id': 'category'})['server_id']}")
    other_parsed_data = json.loads(seen_data.content)
    if seen_data.status_code != 200:
        await ctx.respond(f"Unable to add player to database due to {seen_data.status_code}. Full error code: {other_parsed_data['errors']}", ephemeral=True)
    status = other_parsed_data["data"]["attributes"]["online"]

    test = {
        "_id": bmid,
        "name": name,
        "status": status,
        "last_seen": other_parsed_data["data"]["attributes"]["lastSeen"]
    }

    db_players.insert_one(test)
    await ctx.respond(f"Player with name {name} and ID {bmid} has been entered into the database.", ephemeral=True)


@bot.slash_command()
async def remove_player(ctx: discord.ApplicationContext, bmid: int):
    if db_players.find_one({"_id": bmid}) is None:
        await ctx.respond("No player with that BMID has been found in the database.", ephemeral=True)
    db_players.delete_one({"_id": bmid})
    await ctx.respond(f"Entry with BMID {bmid} has been removed from the database", ephemeral=True)


@bot.slash_command()
async def status(ctx: discord.ApplicationContext):

    if db_players.count_documents({}) == 0:
        await ctx.respond("No players are currently being tracked", ephemeral=True)
    embed = discord.Embed(
        title="Users currently being tracked.", colour=0x328fc)

    for player in db_players.find({}):
        bmid = player["_id"]
        name = player["name"]
        status = player["status"]
        last_seen = player["last_seen"]
        epoch = round(parser.parse(last_seen).timestamp())
        discord_time = f"<t:{epoch}:R>"
        embed.add_field(
            name=name,
            value=f"Online: ***{status}*** \n Online since: ***{discord_time}***\n [BM link](https://www.battlemetrics.com/players/{bmid})", inline=False)

    await ctx.respond(embed=embed, ephemeral=True)


@tasks.loop(seconds=60)
async def tracker_loop():
    channel = bot.get_channel(db_config.find_one(
        {"_id": "category"})['channels'][0])
    if db_players.count_documents({}) == 0:
        return
    for player in db_players.find({}):
        bmid = player["_id"]
        name = player["name"]
        status = player["status"]
        last_seen = player["last_seen"]

        data = requests.get(
            f"https://api.battlemetrics.com/players/{bmid}/servers/{db_config.find_one({'_id':'category'})['server_id']}")
        parsed_data = json.loads(data.content)

        new_status = parsed_data["data"]["attributes"]["online"]
        if new_status != status:
            seen = parsed_data["data"]["attributes"]["lastSeen"]
            name_data = requests.get(
                f"https://api.battlemetrics.com/players/{bmid}")
            name_parsed_data = json.loads(name_data.content)
            new_name = name_parsed_data["data"]["attributes"]["name"]
            newvals = {"_id": bmid, "name": new_name, "status": new_status,
                       "last_seen": seen}
            db_players.delete_one(player)
            db_players.insert_one(newvals)

            t = f"{new_name} has logged on to the server." if new_status else f"{new_name} has logged off."
            embed = discord.Embed(
                title=t, colour=0x73fc03)
            await channel.send(embed=embed)


@bot.event
async def on_ready():
    tracker_loop.start()
    print("BattleMetricsTracker started!")
bot.run(os.getenv("DISCORD_TOKEN"))
