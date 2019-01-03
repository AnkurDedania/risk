import click

from risk.util import load_config, load_db, load_async_db
from risk.model.database import *


@click.group()
def main():
    pass


@main.command()
def start():
    import risk.client

    config = load_config("config.yaml")
    db = load_async_db(config)
    risk.client.main(config, db)


@main.command()
def install():
    config = load_config("config.yaml")
    db = load_db(config)
    db.create_tables([User, Setting, Match, MatchFormat, MatchLobby, MatchLobbyPlayer, MatchPlayer, Score])
    try:
        User._schema.create_foreign_key(User.updated_by)
    except:
        pass
    settings = [
        {"key": "match.season", "value": "0"},
        {"key": "discord.game", "value": "wc3risk.com"},
    ]
    with db.atomic():
        Setting.insert(settings).on_conflict_ignore().execute()
