from datetime import datetime, timedelta

import discord
import time
import json

secrets = json.load(open("secrets.json"))
token = secrets["token"]
filename = secrets["filename"]
channel_id = secrets["channel_id"]


def time_to_string(time):
    return datetime.fromtimestamp(time).strftime("%c")


def timedelta_to_string(td):
    temp = timedelta(seconds=td)

    l = []

    if (a := temp.days) != 0:
        l.append(f"{a} day{'s' if a > 1 else ''}")
    if (a := temp.seconds // 3600) != 0:
        l.append(f"{a} hour{'s' if a > 1 else ''}")
    if (a := (temp.seconds // 60) % 60) != 0:
        l.append(f"{a} minute{'s' if a > 1 else ''}")
    if (a := temp.seconds % 60) != 0:
        l.append(f"{a} second{'s' if a > 1 else ''}")

    if len(l) == 0:
        out = "error"
    elif len(l) == 1:
        out = l[0]
    else:
        out = ", ".join(l[:-1]) + " and " + l[-1]

    return out


# yes i'm lazy but honestly i really could care less
class DB:
    def __init__(self):

        with open("h.txt") as f:
            lines = f.readlines()

            self.total_plays = int(lines[0])
            self.start_time = float(lines[1])
            self.user_db = eval(lines[2])  # unsafe but honestly who tf cares

            print(self.total_plays, self.start_time, self.user_db, sep="\n")

    def create_user(self, user_id):
        self.user_db[user_id] = {  # key is user id
            "join_time": -1,  # time when they joined the VC
            "leave_time": -1,  # time when they left the VC
            "return_time": -1,  # time for them to come back, until it's stopped
            "max_start_time": -1,  # when the longest time they stayed in VC is
            "max_time": -1,  # longest time stayed in vc
            "in_vc": False,  # whether they're currently in VC
            "total_time": 0,  # total time they've spent with luka
        }

    def user_join(self, user_id):
        if user_id not in self.user_db:
            print(f"Creating db for {user_id}")
            self.create_user(user_id)

        self.user_db[user_id]["in_vc"] = True

        if not self.user_db[user_id]["in_vc"] and time.time() > self.user_db[user_id]["return_time"]:

            print(f"User {user_id} joined")

            self.user_db[user_id]["join_time"] = time.time()
        else:
            # fix the added time
            self.user_db[user_id]["total_time"] -= self.user_db[user_id]["leave_time"] - self.user_db[user_id][
                "join_time"]
            print(f"User {user_id} returned")

        self.save()

    def user_leave(self, user_id):

        self.user_db[user_id]["in_vc"] = False

        self.user_db[user_id]["leave_time"] = time.time()
        self.user_db[user_id]["return_time"] = time.time() + 300  # defaults to five minutes

        self.user_db[user_id]["total_time"] += self.user_db[user_id]["leave_time"] - self.user_db[user_id]["join_time"]

        self.update(user_id)

    def update(self, user_id):
        current = self.user_db[user_id]["leave_time"] - self.user_db[user_id]["join_time"]
        if current > self.user_db[user_id]["max_time"]:
            self.user_db[user_id]["max_time"] = current
            self.user_db[user_id]["max_start_time"] = self.user_db[user_id]["join_time"]

        self.save()

    def get_info(self, user_id):
        self.update(user_id)
        return self.user_db[user_id]

    def save(self):
        with open("h.txt", "w") as f:
            f.write(str(self.total_plays))
            f.write("\n")
            f.write(str(self.start_time))
            f.write("\n")
            f.write(str(self.user_db))

        print("saving DB values")


class TheLukaNeverEnds(discord.Client):
    async def on_ready(self):
        print("starting")

        self.db = DB()

        self.channel = self.get_channel(channel_id)
        assert (self.channel is not None)

        await self.start_music()

    async def start_music(self):
        print(self.user.name)

        def repeat(voice, audio):
            self.db.total_plays += 1
            self.db.save()
            voice.play(audio, after=lambda e: repeat(voice, discord.FFmpegPCMAudio(filename)))

        music = discord.FFmpegPCMAudio(filename)
        voice = await self.channel.connect(reconnect=True)
        # voice = asyncio.get_event_loop().(channel.connect(reconnect=True))
        print("connected")

        voice.play(music, after=lambda e: repeat(voice, music))

    """async def on_voice_state_update(self, member, before, after):
        if before.channel == self.channel and after.channel != self.channel:
            self.db.user_leave(member.id)
        elif after.channel == self.channel and before.channel != self.channel:
            self.db.user_join(member.id)"""

    async def on_message(self, message):

        command = message.content.split(" ")

        if command[0] == "tl!info":

            """if len(command) == 1:
                user_id = message.author.id
            elif len(command) == 2:
                try:
                    user_id = message.mentions[0].id
                except IndexError:
                    try:
                        user_id = int(command[1])
                    except ValueError:
                        await message.channel.send(f"Unable to find user {command[1]}.")
                        return
            else:
                await message.channel.send("Too many arguments.")
                return"""

            description = f"I have been running since `{time_to_string(self.db.start_time)}`, or for `{timedelta_to_string(time.time() - self.db.start_time)}`.\n"
            description += f"During this time, I've played Luka's song a total of `{self.db.total_plays}` times and had a total of `{len(self.db.user_db)}` people visit me."

            embed = discord.Embed(description=description, color=0xffaadd)
            embed.set_author(name="Oh? You're interesteed in me?",
                             icon_url="https://cdn.discordapp.com/avatars/832395029481127946/ac668a749d52ebd907d754558ed76c0b.png?size=1024")

            await message.channel.send(embed=embed)

            """
            try:
                data = self.db.get_info(user_id)
            except KeyError:
                await message.channel.send(f"User {command[1]} has never visited me before :(.")
                return

            user = self.get_user(user_id)

            description = f"`{user.name}` is "
            if data["in_vc"]:
                description += "currently enjoying Luka's presence.\n"
                description += f"They have spent `{timedelta_to_string(time.time() - data['join_time'])}` with me so far, "

                if (time.time() - data['join_time']) > data['max_time']:
                    description += "which is the longest time they have ever spent with me.\n"
                else:
                    description += f"but they have spent `{timedelta_to_string(data['max_time'])}` with me before between `{time_to_string(data['max_start_time'])}` and `{time_to_string(data['max_start_time'] + data['max_time'])}`.\n"

            else:
                description += "`currently out of Luka's presence`.\n"
                description += f"The longest time they ever spent with me was `{timedelta_to_string(data['max_time'])}` between `{time_to_string(data['max_start_time'])}` and `{time_to_string(data['max_start_time'] + data['max_time'])}`\n"

            total_time = data['total_time'] + (time.time() - data['join_time'] if data["in_vc"] else 0)
            description += f"They have spent a total of `{timedelta_to_string(total_time)}` with me, of which every moment was cherished."

            embed = discord.Embed(description=description, color=0xffaadd)
            embed.set_author(name=f"{user.name}'s statistics",
                             icon_url=user.avatar_url)
            embed.set_footer(text="All times are in UTC. (I'm lazy)")

            await message.channel.send(embed=embed)

            # print(self.db.total_plays, self.db.start_time, self.db.user_db, sep="\n")
            """


if __name__ == '__main__':
    TheLukaNeverEnds(intents=discord.Intents(guilds=True, voice_states=True, guild_messages=True, members=True)).run(
        token)
