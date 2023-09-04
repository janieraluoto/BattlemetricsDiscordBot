# BattlemetricsDiscordBot

Required packages:

pycord
pymongo


.env contains the following:
DISCORD_TOKEN
MONGO_LOGIN
BOT_PREFIX

mongo database formats are:
PlayerTracker ->
  config ->
    _id: "category"
    category: "discord server channel category that is created"
    server_id: "rust server id supplied upon setup
    channels : [
      0: "ActiveTracking channel"
      1: "Commands channel"
    ]
  players ->
    _id: "battlemetrics id"
    name: playername
    status: player status
    last_seen last_seen
