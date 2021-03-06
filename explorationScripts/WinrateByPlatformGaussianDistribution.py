import json
from unicodedata import name
import matplotlib.pyplot as plt
import numpy as np

import seaborn as sns

import sqlite3
conn = sqlite3.connect("FH.db")

seasonStartDate = 1655395200
# seasonStartDate = 0
# conn = sqlite3.connect("FH.db")
crsr = conn.cursor()
mode = "Dominion"
sqlMode = f"""select 
	   name,
	   username,
	   platform,
       UTCSeconds,
	   wins,
	   losses,
       reputation
from (
  select 
		 name,
		 username, 
		 platform,
         UTCSeconds,
         max(UTCSeconds) over (partition by username,platform) as max_date,
		 min(UTCSeconds) over (partition by username,platform) as min_date,
		 wins,
		 losses,
         reputation
  from (SELECT mode.name,mode.wins,mode.losses, stat.username, stat.platform, stat.UTCSeconds, stat.reputation FROM mode INNER JOIN stat on mode.playerID = stat.playerID  WHERE mode.name = '{mode}' and stat.UTCSeconds > {seasonStartDate})
)
where UTCSeconds = max_date OR UTCSeconds = min_date
ORDER BY username"""

sqlTotal = f"""select 
	   username,
	   platform,
       UTCSeconds,
	   wins,
	   losses,
	   reputation
from (
  select 
		 
		 username, 
		 platform,
         UTCSeconds,
         max(UTCSeconds) over (partition by username,platform) as max_date,
		 min(UTCSeconds) over (partition by username,platform) as min_date,
		 wins,
		 losses,
		 reputation
  from (SELECT * from stat WHERE UTCSeconds > {seasonStartDate})
)
where UTCSeconds = max_date OR UTCSeconds = min_date
ORDER BY username"""

crsr.execute(sqlMode)

ans = crsr.fetchall()

playersOver80 = {}

activeUsers = {}
counter = 0
for i in range(len(ans)):
    counter += 1
    if counter % 1000 == 0:
        print(f"entries parsed: {counter}")
    mode = ans[i][0]
    user = ans[i][1]
    platform = ans[i][2]
    time = ans[i][3]
    wins = ans[i][4]
    losses = ans[i][5]
    reputation = ans[i][6]
    if user in activeUsers:
        if platform in activeUsers[user]:
            stat = {
                "time" : time,
                "wins" : wins,
                "losses" : losses,
                "mode" : mode,
                "platform" : platform,
                "reputation": reputation
            }          
            activeUsers[user][platform].append(stat)
        else:
            stat = {
                "time" : time,
                "wins" : wins,
                "losses" : losses,
                "mode" : mode,
                "platform" : platform,
                "reputation": reputation
            }          
            activeUsers[user][platform] = [stat]
    else:
        stat = {
                "time" : time,
                "wins" : wins,
                "losses" : losses,
                "mode" : mode,
                "platform" : platform,
                "reputation": reputation
        } 
        activeUsers[user] = {}
        activeUsers[user][platform] = [stat]


PSNstats = []
XboxStats = []
PCstats = []

# file = open("updatedUserStats05-18-2.json","r")
# activeUsers = json.load(file)

totalMatchesPC = 0
totalUsersPC = 0
totalMatchesPSN = 0
totalUsersPSN = 0
totalMatchesXBL = 0
totalUsersXBL = 0

numOver60 = {"xbl" : 0,
                 "psn" : 0,
                 "uplay": 0
                 }

percenters50 = {}

numUsers = 0

for user in activeUsers:
    for platform in activeUsers[user]:
        if len(activeUsers[user][platform]) > 1:
            stats = activeUsers[user][platform]
            newlist = sorted(stats, key=lambda d: d['time'])
            first = newlist[0]
            last = newlist[-1]

            wins = last["wins"] - first["wins"]
            losses = last["losses"] - first["losses"]
            # wins = first["wins"]
            # losses = first["losses"]
            if wins + losses > 30:

                winRate = (wins/(wins + losses)) * 100

                if winRate >= 80:
                    playersOver80[user] = activeUsers[user]

                if(winRate < 101):
                    userTuple = (last["reputation"],winRate)
                    numUsers += 1
                    if last["platform"] == "psn":
                        PSNstats.append(userTuple)
                        totalUsersPSN += 1
                        totalMatchesPSN += wins + losses
                    if last["platform"] == "xbl":
                        XboxStats.append(userTuple)
                        totalUsersXBL += 1
                        totalMatchesXBL += wins + losses
                    if last["platform"] == "uplay":
                        PCstats.append(userTuple)
                        totalUsersPC += 1
                        totalMatchesPC += wins + losses

psnRates =   [i[1] for i in PSNstats]
print(f"psn std deviation: {np.std(psnRates):.2f} \t mean: {np.median(psnRates):.2f}")
xblRates =   [i[1] for i in XboxStats]
print(f"xbl std deviation: {np.std(xblRates):.2f} \t mean: {np.median(xblRates):.2f}")
uplayRates = [i[1] for i in PCstats]
print(f"PC  std deviation: {np.std(uplayRates):.2f} \t mean: {np.median(uplayRates):.2f}")

print(f"PSN:   {len(psnRates)}")
print(f"XBL:   {len(xblRates)}")
print(f"UPLAY: {len(uplayRates)}")

allStats = [psnRates,xblRates,uplayRates]
colours  = ["blue",  "green", "red"]
names    = ["psn",  "xbl", "PC"]
i = 0

# ax = sns.distplot(psnRates,color="blue",hist=True,label="psn")
# ax = sns.distplot(xblRates,color="green",hist=True,label="xbl")
# ax = sns.distplot(uplayRates,color="red",hist=True,label="PC")


for platform in allStats:
    ax = sns.distplot(platform,color=colours[i],hist=False,label=names[i])
    # plt.hist(platform,50,color=colours[i])
    i+=1
plt.title("Distribution of Player Winrates by Platform for Dom")
plt.xlabel("Winrate (%)")
plt.legend()
plt.show()
print(numUsers)
file = open(".\\preComputedDatafiles\\playersOver80.json","w")
file.write(json.dumps(playersOver80,indent=4))