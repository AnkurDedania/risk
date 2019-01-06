import trueskill

from itertools import combinations
from typing import List, NamedTuple
from random import randint

from risk.model.database import *


class Player(NamedTuple):
    id: str
    mu: float
    sigma: float
    games: int

    def __hash__(self):
        return hash(self.id)


class Team(NamedTuple):
    team: int
    players: List[Player]

    def __hash__(self):
        return hash(self.team)


class MatchCreator:

    def __init__(self, scores: List[MatchLobbyPlayer], match_format: MatchFormat):
        self.match_format = match_format
        self.players: List[Player] = [Player(p.player_id, p.mu, p.sigma, p.games) for p in scores]

    def team_formats(self):
        players = range(len(self.players))
        iterables = combinations(players, self.match_format.team_size)
        groups = map(lambda team: sorted([list(team), list(set(players) - set(team))]), iterables)
        team_formats = []

        for group in groups:
            if group not in team_formats:
                team_formats.append(list(group))

        yield from team_formats

    def quality(self, team_format):
        setup = []
        for n, team in enumerate(team_format):
            setup.append([])
            for m in team:
                player = self.players[m]
                setup[n].append(trueskill.Rating(mu=player.mu, sigma=player.sigma))

        return trueskill.quality(setup)

    def balance(self) -> List[Team]:
        setup = []
        if self.match_format.team_size != 1:
            results = {team_format: self.quality(team_format) for team_format in self.team_formats()}
            results = [(k, results[k]) for k in sorted(results, key=results.get, reverse=True)]
            best_quality = results[0][1]
            results = [(k, v) for k, v in results if v == best_quality]
            result = results[randint(0, len(results)-1)][0]
            for n, team in enumerate(result):
                setup.append(Team(n, []))
                for m in team:
                    setup[n].players.append(self.players[m])
        else:
            for n in range(len(self.players)):
                setup.append(Team(n, [self.players[n]]))

        return setup
