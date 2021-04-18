import discord
import time

token = "[redacted]"
filename = "luka.mp3"


# yes i'm lazy but honestly i really could care less
class DB:
    def __init__(self):
        self.start_time = time.time()
        self.total_plays = 0

        self.user_db = {}

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

        if not self.user_db[user_id]["in_vc"] and time.time() > self.user_db[user_id]["return_time"]:

            print(f"User {user_id} joined")

            self.user_db[user_id]["join_time"] = time.time()
            self.user_db[user_id]["in_vc"] = True
        else:
            # fix the added time
            self.user_db[user_id]["total_time"] -= self.user_db[user_id]["leave_time"] - self.user_db[user_id][
                "join_time"]
            print(f"User {user_id} returned")

    def user_leave(self, user_id):

        self.user_db[user_id]["in_vc"] = False

        self.user_db[user_id]["leave_time"] = time.time()
        self.user_db[user_id]["return_time"] = time.time() + 300  # defaults to five minutes

        self.user_db[user_id]["total_time"] += self.user_db[user_id]["leave_time"] - self.user_db[user_id]["join_time"]

        self.update(user_id)

    def update(self, user_id):
        current = (time.time() if self.user_db[user_id]["in_vc"] else self.user_db[user_id]["leave_time"]) - \
                  self.user_db[user_id]["join_time"]
        if current > self.user_db[user_id]["max_time"]:
            self.user_db[user_id]["max_time"] = current
            self.user_db[user_id]["max_start_time"] = self.user_db[user_id]["join_time"]

    def get_info(self, user_id):
        self.update(user_id)
        return self.user_db[user_id]


class TheLukaNeverEnds(discord.Client):
    async def on_ready(self):
        print("starting")

        self.db = DB()

        self.channel = self.get_channel(833063357460119572)
        assert (self.channel is not None)

        await self.start_music()

    async def start_music(self):
        print(self.user.name)

        def repeat(voice, audio):
            self.db.total_plays += 1
            voice.play(audio, after=lambda e: repeat(voice, discord.FFmpegPCMAudio(filename)))

        music = discord.FFmpegPCMAudio(filename)
        voice = await self.channel.connect(reconnect=True)
        # voice = asyncio.get_event_loop().(channel.connect(reconnect=True))
        print("connected")

        voice.play(music, after=lambda e: repeat(voice, music))

    async def on_voice_state_update(self, member, before, after):
        if before.channel == self.channel and after.channel != self.channel:
            self.db.user_leave(member.id)
        elif after.channel == self.channel and before.channel != self.channel:
            self.db.user_join(member.id)

    async def on_message(self, message):
        if message.content == "tl!info":
            with open("h.txt", "w") as f:
                f.write(str(self.db.total_plays))
                f.write("\n")
                f.write(str(self.db.start_time))
                f.write("\n")
                f.write(str(self.db.user_db))

            print(self.db.total_plays, self.db.start_time, self.db.user_db, sep="\n")


if __name__ == '__main__':
    TheLukaNeverEnds(intents=discord.Intents(guilds=True, voice_states=True, guild_messages=True)).run(token)
