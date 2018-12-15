import peewee
import peewee_async

from ruamel.yaml import YAML

from risk.db.model import *


def load_config(file):
    with open(file) as fp:
        yaml = YAML()
        return yaml.load(fp)


def load_db(config):


    if config['database']['driver'] == 'MySQL':
        driver = peewee.MySQLDatabase
    elif config['database']['driver'] == 'Postgresql':
        driver = peewee.PostgresqlDatabase
    else:
        raise Exception("Requires `MySQL` or `Postgresql` as driver")
    db = driver(
        config['database']['schema'],
        user=config['database']['user'],
        password=config['database']['password'],
        host=config['database']['host']
    )
    db.bind([User, Setting, Match, MatchFormat, MatchLobby, MatchLobbyPlayer, MatchPlayer, Score])
    return db


def load_async_db(config):
    if config['database']['driver'] == 'MySQL':
        driver = peewee_async.PooledMySQLDatabase
    elif config['database']['driver'] == 'Postgresql':
        driver = peewee_async.PooledPostgresqlDatabase
    else:
        raise Exception("Requires `MySQL` or `Postgresql` as driver")
    db = driver(
        config['database']['schema'],
        user=config['database']['user'],
        password=config['database']['password'],
        host=config['database']['host']
    )
    db.bind([User, Setting, Match, MatchFormat, MatchLobby, MatchLobbyPlayer, MatchPlayer, Score])
    database = Manager(db)
    db.set_allow_sync(False)
    return database


# async patch
class Manager(peewee_async.Manager):

    async def get_or_none(self, source_, *args, **kwargs):
        try:
            return await self.get(source_, *args, **kwargs)
        except peewee.DoesNotExist:
            pass
