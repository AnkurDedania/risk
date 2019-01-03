import discord
try:
    import cytoolz as toolz
except ImportError:
    import toolz

from risk.model.database import *
from risk.util import Manager

from datetime import datetime
from typing import List

HELP = """```
Commands:
    !help                 - Command list
    !create [MatchFormat] - Create lobby
    !join                 - Join active lobby
    !stats (@Name)        - Stats Player or Self
    !close                - Close active lobby
    !confirm (@Name)      - Confirm winner
    !where                - Current state, in lobby or in game
    !query [MatchNumber]  - Get information on match
    !leave                - Leave active lobby
Commands (Moderator):
    !close                - Close active lobby
    !kick                 - Kick player from active lobby
Commands (Admin):
    !enable @Name         - Enable account
    !disable @Name        - Suspend account
    !void @Name           - Suspend account at stats
```"""


class CommandHelper:

    def __init__(self, client, config, database):
        self.client = client
        self.config = config
        self.database: Manager = database

    async def register_user(self, user: discord.User) -> User:
        return (await self.database.create_or_get(User, id=user.id, name=user.name))[0]

    async def get_season(self):
        return (await self.database.get(Setting, key='match.season')).value

    async def send_invalid_match(self, message):
        results = await self.database.execute(MatchFormat.select(MatchFormat.id))
        formats = ", ".join(f"`{result.id}`" for result in results)
        await message.channel.send(
            f"**Invalid MatchFormat**, use `!create [MatchFormat]`, available MatchFormats: {formats}"
        )

    async def get_active_lobby(self) -> MatchLobby:
        return await self.database.get_or_none(MatchLobby, MatchLobby.closed.is_null())

    async def get_active_lobby_format(self, lobby: MatchLobby=None) -> MatchFormat:
        if not lobby:
            lobby = await self.get_active_lobby()
        return await self.database.get(MatchFormat, id=lobby.format_id)

    async def get_active_lobby_players(self, lobby: MatchLobby=None) -> List[MatchLobbyPlayer]:
        if not lobby:
            lobby = await self.get_active_lobby()
        results = await self.database.execute(MatchLobbyPlayer.select().where(
            MatchLobbyPlayer.lobby == lobby
        ))
        return list(results)

    async def get_score(self, user: User, match_format: MatchFormat):
        score = await self.database.get_or_none(
            Score, Score.player == user and Score.format == match_format
        )
        if not score:
            score = await self.database.create(Score, player=user, format=match_format)
        return score


class Command(CommandHelper):

    async def command_help(self, message: discord.Message):
        await message.channel.send(HELP)

    async def command_spoof(self, message: discord.Message):
        author = await self.register_user(message.author)
        _, spoof, content = message.content.split(" ", 2)
        if author.admin:
            if len(spoof) > 3 and spoof[2:-1].isnumeric():
                user = self.client.get_user(int(spoof[2:-1]))
                if user:
                    message.author = user
                    message.content = content
                    command = message.content.split()[0][1:]
                    if hasattr(self, f"command_{command}"):
                        await getattr(self, f"command_{command}")(message)
                    else:
                        await message.channel.send("command not found")
                else:
                    await message.channel.send("user not found")
            else:
                await message.channel.send("user not found")

    async def command_create(self, message: discord.Message):
        lobby = await self.get_active_lobby()
        if lobby:
            await message.channel.send(f"<@{lobby.creator_id}> has already created a lobby, type `!join` to queue up")
        else:
            command = message.content.split()
            if len(command) == 2:
                match_format = await self.database.get_or_none(MatchFormat, id=command[1])
                if match_format:
                    async with self.database.atomic():
                        user = await self.register_user(message.author)
                        score = await self.get_score(user, match_format)
                        lobby = await self.database.create(MatchLobby, creator=user, format=match_format)
                        await self.database.create(
                            MatchLobbyPlayer,
                            lobby=lobby, player=user, mu=score.mu, sigma=score.sigma, games=score.games
                        )
                    await message.channel.send(
                        f"<@{message.author}> has created a {match_format} lobby, type `!join` to queue up")
                else:
                    await self.send_invalid_match(message)
            else:
                await self.send_invalid_match(message)

    async def command_close(self, message: discord.Message):
        lobby = await self.get_active_lobby()
        if lobby:
            if (message.author.id == int(lobby.creator_id)) or ((datetime.utcnow() - lobby.updated).seconds > 60):
                lobby.closed = datetime.utcnow()
            else:
                user = await self.register_user(message.author)
                if user.moderator or user.admin:
                    lobby.closed = datetime.utcnow()
                else:
                    await message.channel.send(
                        f"<@{lobby.creator_id}> has already created a lobby, can't be closed currently"
                    )
            if lobby.closed:
                await self.database.update(lobby)
                await message.channel.send(
                    f"<@{message.author.id}> closed the lobby"
                )
        else:
            await message.channel.send(f"no lobby active, use `!create [MatchFormat]`")

    async def command_join(self, message: discord.Message):
        lobby = await self.get_active_lobby()
        if lobby:
            match_format = await self.get_active_lobby_format(lobby)
            match_players = await self.get_active_lobby_players(lobby)
            user = await self.register_user(message.author)
            if len(match_players) >= match_format.max_player:
                await message.channel.send(f"lobby is currently full, <@{lobby.creator_id}> `!start`")
            elif not user.disabled:
                if toolz.count(filter(lambda x: x.player_id == user.id, match_players)):
                    await message.channel.send(f"you are already signed up for the current lobby")
                else:
                    lobby.updated = datetime.utcnow()
                    async with self.database.atomic():
                        score = await self.get_score(user, match_format)
                        await self.database.create(
                            MatchLobbyPlayer,
                            lobby=lobby, player=user, mu=score.mu, sigma=score.sigma, games=score.games
                        )
                        await self.database.update(lobby)
                    if len(match_players) + 1 >= match_format.min_player:
                        await message.channel.send(
                            f"<@{user.id}> has joined the lobby ({len(match_players) + 1}/{match_format.max_player}), "
                            f"<@{lobby.creator_id}> can `!start`"
                        )
                    else:
                        await message.channel.send(
                            f"<@{user.id}> has joined the lobby ({len(match_players) + 1}/{match_format.max_player})"
                        )
        else:
            await message.channel.send(f"no lobby active, use `!create [MatchFormat]`")

    async def command_leave(self, message: discord.Message):
        lobby = await self.get_active_lobby()
        if lobby:
            user = await self.register_user(message.author)
            if lobby.creator_id == user.id:
                lobby.closed = datetime.utcnow()
                await self.database.update(lobby)
                await message.channel.send(f"<@{user.id}> closed the lobby")
            else:
                match_format = await self.get_active_lobby_format(lobby)
                match_players = await self.get_active_lobby_players(lobby)
                if toolz.count(filter(lambda x: x.player_id == user.id, match_players)):
                    match_player = toolz.first(filter(lambda x: x.player_id == user.id, match_players))
                    await self.database.delete(match_player)
                    await message.channel.send(
                        f"<@{user.id}> has left the lobby ({len(match_players)-1}/{match_format.max_player})"
                    )
                else:
                    await message.channel.send(f"<@{user.id}> isn't in a lobby")
        else:
            await message.channel.send(f"no lobby active, use `!create [MatchFormat]`")
