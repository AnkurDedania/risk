import discord

from risk.model.database import *
from risk.command import Command
from risk.util import Manager


class Client(discord.Client):

    def __init__(self, config, database):
        self.config = config
        self.database: Manager = database
        self.command = Command(self, self.config, self.database)
        super().__init__()

    async def on_ready(self):
        game = await self.database.get(Setting, Setting.key == 'discord.game')
        await self.change_presence(activity=discord.Game(game.value))
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content.startswith('!'):
            command = message.content.split()[0][1:]
            if hasattr(self.command, f"command_{command}"):
                await getattr(self.command, f"command_{command}")(message)


def main(config, db):
    client = Client(config, db)
    client.run(config['token'])
