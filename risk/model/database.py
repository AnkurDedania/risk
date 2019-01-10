from peewee import *

import datetime


__all__ = [
    "Setting", "User", "Score",
    "MatchPlayer", "MatchLobbyPlayer", "MatchLobby", "MatchFormat", "Match",
]


MU = 25
SIGMA = 25/3


class User(Model):
    id = CharField(primary_key=True)
    name = CharField()
    admin = BooleanField(default=False)
    moderator = BooleanField(default=False)
    disabled = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class Setting(Model):
    key = CharField(primary_key=True)
    value = CharField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class MatchFormat(Model):
    id = CharField(primary_key=True)
    team_size = IntegerField()
    min_player = IntegerField()
    max_player = IntegerField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class MatchLobby(Model):
    creator = ForeignKeyField(User)
    format = ForeignKeyField(MatchFormat)
    closed = DateTimeField(null=True)
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class MatchLobbyPlayer(Model):
    lobby = ForeignKeyField(MatchLobby)
    player = ForeignKeyField(User)
    mu = DoubleField(default=MU)
    sigma = DoubleField(default=SIGMA)
    games = IntegerField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class Match(Model):
    creator = ForeignKeyField(User)
    season = IntegerField()
    format = ForeignKeyField(MatchFormat)
    winner = IntegerField(default=-1)
    closed = DateTimeField(null=True)
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)
    updated_by = ForeignKeyField(User, null=True)


class MatchPlayer(Model):
    match = ForeignKeyField(Match)
    team = IntegerField()
    player = ForeignKeyField(User)
    mu = DoubleField(default=MU)
    sigma = DoubleField(default=SIGMA)
    games = IntegerField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)


class Score(Model):
    player = ForeignKeyField(User)
    season = IntegerField()
    format = ForeignKeyField(MatchFormat)
    mu = DoubleField(default=MU)
    sigma = DoubleField(default=SIGMA)
    win = IntegerField(default=0)
    lose = IntegerField(default=0)
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)

    @property
    def games(self):
        return self.win + self.lose
