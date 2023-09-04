# BattlemetricsDiscordBot

bot allows the user to create a database to add rust players to and track when they join a specific rust server whose battlemetrics id you supply.<br>

commands:<br>
/add_player<br>
/remove_player<br>
/status<br>
/setup<br>
<br>
Required packages:

pycord <br>
pymongo


.env contains the following:<br>
DISCORD_TOKEN<br>
MONGO_LOGIN<br>
BOT_PREFIX<br>
<br>


Discord account required as well as mongodb.<br>

To use:<br>

have a cluster made with mongodb and a database with the name PlayerTracker<br>

create a discord server and add the bot with bot and applications.commands intents. <br>

add the bot to the server you created with admin priviliges<br>

run the /setup command and give it a rust server id that can be taken from searching the rust servers name on a web engine and selecting the battlemetrics option that comes up. <br>

from there you can run /add_player with the battlemetrics id of the player you want to track.<br>

remove player with /remove_player with the BMID<br>

see everyone that is currently being tracked with /status<br>

/setup again to remove the channels and category related to the bot.

