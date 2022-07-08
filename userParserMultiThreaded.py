import re
import json
import time
import random
import sys
import cloudscraper
import threading
import sqlite3
# import privacypass


mutex = threading.Lock()

arg = 0
if len(sys.argv) < 2:
    arg = 1
else: arg = int(sys.argv[1])

# read in the users csv
userFile = open("C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\compiledUsers-06-27-1.csv","r")
usersFileLines = userFile.readlines()
userFile.close()
users = []
#split the csv into the platform and username of each user
userToResumeAt = "almondofdoom"
resumePointReached = False

# compleatedUsersFile = open("C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\updatedUserStats04-28-2.json","r")
# compleatedUsers = json.load(compleatedUsersFile)

for line in usersFileLines:
    splitLine = line.split(",")
    platform = splitLine[0]
    username = splitLine[1][0:-1]
    splicedUsername = username.split("%20")
    splicedUsername = " ".join(splicedUsername)
    users.append((platform,username))
    # if(splicedUsername == userToResumeAt):
    #     resumePointReached = True

    # if(resumePointReached):
    #     if (not (splicedUsername in compleatedUsers)):
    #         users.append((platform,username))
    #     elif username in compleatedUsers:
    #         if len(compleatedUsers[username][platform]) == 0:
    #             users.append((platform,username))

# shuffle the list for random selection from 250 000 users
random.shuffle(users)


# num = 0
id = 0


nonExistantUsersFile = open("C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\failedUsers.csv","r")
nonExistantUsersList = nonExistantUsersFile.readlines()
failedUsersDict = {}
for user in nonExistantUsersList:
    # realUser = user[:-1]
    failedUsersDict[user] = True

def downloadThread(id):
    conn = sqlite3.connect("FH.db")
    crsr = conn.cursor()
    players = {}
    head = {
    "cookie": "__cf_bm=2ka4FwOsnbf0_BVmL5cnwPNpl2Zyx6RfDVAubQrAV6A-1656514882-0-AWC2l5sNPps0UHVWjatanw5KLf%2BiIVqzoF44o2Q%2FKtVTGbbosllZHYGMm04f2Ua7jG9R9I2BD0Yx3coZJ87gptU%3D",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://tracker.gg",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Referer": "https://tracker.gg/",
    "Connection": "keep-alive",
    "Cookie": "cf_clearance=0ypl8bqVQgI.6fopu3u4f.ZVx6eNQbCa0d1s6ozrOlk-1651883599-0-250; _ga=GA1.2.930856034.1651883756; __gads=ID=48b27d6d5b3f82fd:T=1651883761:S=ALNI_Mbs2XuTT0zo-QPmFkvTirS2ll7Jow; __gpi=UID=000004bc42b78fbd:T=1651883761:RT=1651926991:S=ALNI_MbWpZiUXXJUMKt_HRmkH3BLlFoYew; __cflb=02DiuFQAkRrzD1P1mdm8JatZXtAyjoPD1d6jkXqEEyTat; __cf_bm=2eMFXpqSXogz0GKGgjK45qLqEFanqQO3anle.88iTAw-1656514851-0-AQoMY8GGQw64NApxspAvMqqQYphBhJRTNoeHiZpF0W3b9HG3kvZYyqN47lUYz4z1F1RCXrBjZWOsfrXIB1UhFx0=; X-Mapping-Server=s14",
    "TE": "trailers",
    "If-Modified-Since": "Wed, 29 Jun 2022 14:44:05 GMT"
}   
    scraper = cloudscraper.create_scraper(debug=True)
    num = 0
    while len(users) > 0:
        mutex.acquire()
        user = users.pop()
        mutex.release()

        skipUser = False
        timeForUpdate = False
        platform = user[0]
        username = user[1]

        splitUsername = username.split("%20")
        fortmattedUN = " ".join(splitUsername)
        

        sql = f"""SELECT username,platform,UTCSeconds from stat where username='{fortmattedUN}' and platform='{platform}'"""
        crsr.execute(sql)
        ans = crsr.fetchall()
        ans.sort(key=lambda y:y[2])
        if len(ans) > 0:
            if(time.time() - ans[-1][2] > (86400 * 0.5)):
                timeForUpdate = True
            else: timeForUpdate = False
        if len(ans) == 0:
            timeForUpdate = True

        lineString = user[0] + "," + fortmattedUN + "\n"

        url = ""
        html_data = ""
        if lineString not in failedUsersDict and timeForUpdate:
            # catches any errors and skips the user if they gave an error. (this section would throw an error every thousand users or so)
            try:
                url = f'https://tracker.gg/for-honor/profile/{platform}/{username}/pvp'
                html_data = scraper.get(url,timeout=10).text

            except Exception as e:
                print("GET error:\n", e)
                # failedUsersFile = open("failedUsers.csv","a")
                # failedUsersFile.write(platform + "," + username + "," + str(e))
                # failedUsersFile.close()
                skipUser = True
        else:
            skipUser = True
        
        # error handling for going over access limit. will retry every ten seconds
        attempts = 0
        while len(html_data) < 1000 and not skipUser:
            time.sleep(10)
            print("error on " + username)
            url = f'https://tracker.gg/for-honor/profile/{platform}/{username}/pvp'
            html_data = scraper.get(url,timeout=20).text
            attempts += 1
            if attempts >= 5:
                skipUser = True
        


        # the stat tracker replaces spaces in the url with "%20" but the initial state json uses spaces when referencing the username
        # this simply reconstructs the actual username
        splitUsername = username.split("%20")
        username = " ".join(splitUsername)
        # mutex.acquire()
        print(f"ThreadID : {id}\n  count : {str(num+1)} \n  user : {username}") # current user
        # mutex.release()

        # this section would also throw errors occasionally. only happend once in about 5000 attempts though
        try: 
            # strip the initial state JSON from the HTML page
            data = re.search(r"window\.__INITIAL_STATE__=({.*});", html_data).group(1)
            data = json.loads(data)
            # strip the useless stuff from the state
            data = data["stats"]["standardProfiles"]
        except:
            # mutex.acquire()
            if timeForUpdate:
                errorLog = open(f"errorLog.html","a")
                errorLog.write(html_data)
                errorLog.close()
                # mutex.release()
                # failedUsersFile = open("failedUsers.csv","a")
                # failedUsersFile.write(platform + "," + username + "\n")
                # failedUsersFile.close()
                print("group error")
            if len(html_data) < 20 and timeForUpdate and lineString not in failedUsersDict:
                mutex.acquire()
                failedUsersFile = open("failedUsers.csv","a")
                # failedUsersFile.write(platform + "," + username + "\n")
                failedUsersFile.close()
                mutex.release()
            skipUser = True

        # this section catches the issue where the server would respond with 404, 500 and things of that nature that had valid inital states 
        # not the best way to handle it at all but it was the first thing that came to mind
        try:
            lowerCaseUN = username.lower()
            if data[f"for-honor|{platform}|{lowerCaseUN}"]["status"] != 0 and timeForUpdate and lineString not in failedUsersDict: 
                skipUser = True
                mutex.acquire()
                failedUsersFile = open("failedUsers.csv","a")
                # failedUsersFile.write(platform + "," + username + "\n")
                failedUsersFile.close()
                mutex.release()
                print(username + " : status error")
        except:
            ...

        # provided all of the above went well
        if not skipUser:


            # this can be commented out. it exists to help debug the issue when the program crashes
            # file = open("C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\pvp2.json","w")
            # file.write(json.dumps(data, indent=4))
            # file.close()

            lowerCaseUN = username.lower()
            try:
                data = data[f"for-honor|{platform}|{lowerCaseUN}"]
                faction = data["metadata"]["factionKey"]
            except:
                skipUser = True 
            
            if not skipUser:
                # list of heros
                heros = [
                "Aramusha",
                "Berserker",
                "Black Prior",
                "Centurion",
                "Conqueror",
                "Gladiator",
                "Gryphon",
                "Highlander",
                "Hitokiri",
                "Jiang Jun",
                "Jormungandr",
                "Kensei",
                "Kyoshin",
                "Lawbringer",
                "Nobushi",
                "Nuxia",
                "Orochi",
                "Peacekeeper",
                "Pirate",
                "Raider",
                "Shaman",
                "Shaolin",
                "Shinobi",
                "Shugoki",
                "Tiandi",
                "Valkyrie",
                "Warden",
                "Warlord",
                "Warmonger",
                "Zhanhu"
                ]

                modes = ["Dominion","Duel","Breach","Elimination","Skirmish"]
                # player json format
                player = {
                    "id" : 0,
                    "platform" : "",
                    "username" : "",
                    "faction" : "",
                    "reputation" : 0,
                    "kills" : 0,
                    "deaths": 0,
                    "assists" : 0,
                    "wins" : 0,
                    "losses": 0,
                    "time" : 0,
                    "date" : time.time(),

                    "modes" : {
                        "Dominion" : {
                            "wins" : 0,
                            "losses" : 0,
                            "kills" : 0,
                            "deaths": 0,
                            "assists": 0,
                            "time" : 0
                        },
                        "Duel" : {
                            "wins" : 0,
                            "losses" : 0,
                            "kills" : 0,
                            "deaths": 0,
                            "assists": 0,
                            "time" : 0
                        },
                        "Breach" : {
                            "wins" : 0,
                            "losses" : 0,
                            "kills" : 0,
                            "deaths": 0,
                            "assists": 0,
                            "time" : 0
                        },
                        "Elimination" : {
                            "wins" : 0,
                            "losses" : 0,
                            "kills" : 0,
                            "deaths": 0,
                            "assists": 0,
                            "time" : 0
                        },
                        "Skirmish" : {
                            "wins" : 0,
                            "losses" : 0,
                            "kills" : 0,
                            "deaths": 0,
                            "assists": 0,
                            "time" : 0
                        }
                    },
                    "heros" : {
                        "Aramusha" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Berserker" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Black Prior" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Centurion" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Conqueror" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Gladiator" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Gryphon" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Highlander" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Hitokiri" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Jiang Jun" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Jormungandr" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Kensei" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Kyoshin" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Lawbringer" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Nobushi" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Nuxia" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Orochi" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Peacekeeper" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Pirate" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Raider" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Shaman" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Shaolin" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Shinobi" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Shugoki" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Tiandi" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Valkyrie" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Warden" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Warlord" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Warmonger" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                        "Zhanhu" : {
                            "time" : 0,
                            "wins" : 0,
                            "losses":0,
                            
                            "kills": 0,
                            "deaths":0,
                            "assists":0
                        },
                    }

                }
                
                stats = { # each stats has the date (in seconds since epoch) along with the player's rep time played and PVP stats
                # these include total kills, deaths, assists, wins, and losses. As well as kills, deaths, assists, wins, and losses by mode
                # they also include kills, deaths, assists, wins, losses, and time played for each hero. I use time played as a substitute for rep.
                # these stats do not include K/D/A/W/L for each hero per mode. I cannot say for sure that player "A" has a 63% winrate in dominion as Berserker.
                # this kind of stat could be approximated by using players that play almost exclusivly that mode though
                "date" : 0,
                "platform" : "",
                "faction" : "",
                "reputation" : 0,
                "kills" : 0,
                "deaths": 0,
                "assists" : 0,
                "wins" : 0,
                "losses": 0,
                "time" : 0,
                "modes" : {
                    "Dominion" : {
                        "wins" : 0,
                        "losses" : 0,
                        "kills" : 0,
                        "deaths": 0,
                        "assists": 0,
                        "time" : 0
                    },
                    "Duel" : {
                        "wins" : 0,
                        "losses" : 0,
                        "kills" : 0,
                        "deaths": 0,
                        "assists": 0,
                        "time" : 0
                    },
                    "Breach" : {
                        "wins" : 0,
                        "losses" : 0,
                        "kills" : 0,
                        "deaths": 0,
                        "assists": 0,
                        "time" : 0
                    },
                    "Elimination" : {
                        "wins" : 0,
                        "losses" : 0,
                        "kills" : 0,
                        "deaths": 0,
                        "assists": 0,
                        "time" : 0
                    },
                    "Skirmish" : {
                        "wins" : 0,
                        "losses" : 0,
                        "kills" : 0,
                        "deaths": 0,
                        "assists": 0,
                        "time" : 0
                    }
                },
                "heros" : {
                    "Aramusha" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Berserker" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Black Prior" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Centurion" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Conqueror" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Gladiator" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Gryphon" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Highlander" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Hitokiri" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Jiang Jun" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Jormungandr" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Kensei" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Kyoshin" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Lawbringer" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Nobushi" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Nuxia" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Orochi" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Peacekeeper" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Pirate" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Raider" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Shaman" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Shaolin" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Shinobi" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Shugoki" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Tiandi" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Valkyrie" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Warden" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Warlord" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Warmonger" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                    "Zhanhu" : {
                        "time" : 0,
                        "wins" : 0,
                        "losses":0,
                        
                        "kills": 0,
                        "deaths":0,
                        "assists":0
                    },
                }
        }
    
                # player["id"] = id
                # id += 1
                players[username] = {
                "psn" : [],
                "xbl" : [],
                "uplay" : []
                }
                stats["platform"] = platform
                stats["faction"] = faction

                # "segments" is about 1MB of json. it contains all the importand info that I want and a metric ton of data that i don't
                segments = data["segments"]
                for item in segments:
                    # if the current item in segments is a hero and that hero exists. OutlandersH030PirateQueen is the pirate and SamuraiH029Faceless is kyoshin
                    if item["type"] == "hero" and (item["metadata"]["name"] in heros or item["metadata"]["name"] == "OutlandersH030PirateQueen" or item["metadata"]["name"] == "SamuraiH029Faceless"):
                        name = item["metadata"]["name"]
                        if name == "OutlandersH030PirateQueen": name = "Pirate"
                        if name == "SamuraiH029Faceless": name = "Kyoshin"
                        heroStats = item["stats"]
                        stats["heros"][name]["wins"] = heroStats["wins"]["value"]
                        stats["heros"][name]["losses"] = heroStats["losses"]["value"]
                        stats["heros"][name]["kills"] = heroStats["killsP"]["value"]
                        stats["heros"][name]["deaths"] = heroStats["deathsP"]["value"]
                        stats["heros"][name]["assists"] = heroStats["assistsP"]["value"]
                        stats["heros"][name]["time"] = heroStats["timePlayed"]["value"]
                    
                    # this section contains the user's global stats
                    if item["type"] == "gameType":
                        if item["metadata"]["name"] == "Player vs. Player Overview":
                            globalStats = item["stats"]
                            stats["reputation"] = globalStats["reputation"]["value"]
                            stats["kills"] = globalStats["killsP"]["value"]
                            stats["deaths"] = globalStats["deathsP"]["value"]
                            stats["assists"] = globalStats["assistsP"]["value"]
                            stats["wins"] = globalStats["wins"]["value"]
                            stats["losses"] = globalStats["losses"]["value"]
                            stats["time"] = globalStats["timePlayed"]["value"]
                            stats["date"] = time.time()

                    # this section contains the gamemode stats
                    if item["metadata"]["name"] in modes:
                            mode = item["metadata"]["name"]
                            modeStats = item["stats"]
                            stats["modes"][mode]["wins"]   = modeStats["wins"]["value"]
                            stats["modes"][mode]["losses"] = modeStats["losses"]["value"]
                            stats["modes"][mode]["kills"]  = modeStats["killsP"]["value"]
                            stats["modes"][mode]["deaths"] = modeStats["deathsP"]["value"]
                            stats["modes"][mode]["assists"]= modeStats["assistsP"]["value"]
                            stats["modes"][mode]["time"]   = modeStats["timePlayed"]["value"]
                
                num += 1
                
                players[username][platform].append(stats)
                stats = {}
                # every 100 players write them to a file. this was to backup the data incase of a crash. I am not very good at this but it does save memory i think
                # time.sleep(random.random())
                if(num % 100 == 0):
                    dataFile = open(f"C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\datafiles\\data{str(id)}-{str(num)}.json","a")
                    dataFile.write(json.dumps(players))
                    dataFile.close() 
                    players = {}
        time.sleep(600)
    dataFile = open(f"C:\\Users\\Jack Bowman\\Documents\\Programs\\PytScripts\\UserScraper\\datafiles\\dataFinal-{id}.json","a")
    dataFile.write(json.dumps(players))
    dataFile.close()
    players = {}

number = len(users)

threads = []
for n in range(arg):
    t = threading.Thread(target=downloadThread, args=[n])
    t.start()
    threads.append(t)

for item in threads:
    item.join()





