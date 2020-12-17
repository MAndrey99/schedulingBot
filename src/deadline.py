from datetime import datetime
from os import getenv
import json


class Deadline:
    def __init__(self, title=None, dateTime=None, creatorId=None, groupId=None, description=None):
        self.title = title
        self.dateTime = dateTime
        self.creatorId = creatorId
        self.groupId = groupId
        self.description = description

    @staticmethod
    def from_dict(jso: dict) -> 'Deadline':
        res = Deadline()
        for k, v in jso.items():
            if k.endswith('dateTime'):
                res.__setattr__(k, datetime.strptime(v, getenv('SERVICE_DATETIME_FMT')))
            else:
                res.__setattr__(k, v)
        return res

    def to_json(self) -> str:
        return json.dumps(dict(filter(lambda i: i[1] is not None, self.__dict__.items())))  # только поля без None
