import os
import urllib.parse as urlparse
from typing import Optional

import peewee as orm

urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(os.environ['DATABASE_URL'])


DATABASE = {
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port,
}

db = orm.PostgresqlDatabase('postgres', **DATABASE)


class DynamicSchedules(orm.Model):
    message_id = orm.BigIntegerField(primary_key=True)
    chat_id = orm.BigIntegerField(unique=True)

    class Meta:
        database = db


def init():
    with db:
        DynamicSchedules.create_table()


@db.connection_context()
def add_schedule_entry(message_id, chat_id):
    DynamicSchedules.create(message_id=message_id, chat_id=chat_id)


@db.connection_context()
def get_dynamic_schedule_message(chat_id) -> Optional[DynamicSchedules]:
    try:
        return DynamicSchedules.get(DynamicSchedules.chat_id == chat_id)
    except orm.DoesNotExist:
        return
