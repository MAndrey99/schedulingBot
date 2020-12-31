from datetime import datetime
from os import getenv
import json
from util import seconds_to_time_str


class Deadline:
    def __init__(self, title=None, dateTime=None, creatorId=None, groupId=None, description=None, **kwargs):
        self.title = title and title.lstrip().rstrip().replace('  ', ' ')
        self.dateTime = dateTime
        self.creatorId = creatorId
        self.groupId = groupId
        self.description = description
        self.leadTime = None
        self.priority = 0
        for k, v in kwargs.items():
            if k.endswith('dateTime'):
                self.__setattr__(k, datetime.strptime(v, getenv('SERVICE_DATETIME_FMT')))
            else:
                self.__setattr__(k, v)

    def to_string(self):
        if self.leadTime is not None:
            lt = f'[{seconds_to_time_str(self.leadTime)}]'
        else:
            lt = ''
        return f'{self.title}: {self.dateTime}{lt}'

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
