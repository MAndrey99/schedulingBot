import json
from os import getenv
from typing import *

from requests import *

import src.bot.logs as logs
from src.bot.deadline import Deadline


class ApiException(Exception):
    def __init__(self, wtf: str, code: int, service_method):
        super(ApiException, self).__init__(wtf)
        self.code = code
        if code // 100 == 5:
            logs.error(wtf + '\t' + f'метод ' + service_method.__name__)


class Service:
    def __init__(self, url):
        self.url = url

    def _request(self, method, path, method_from, **kwargs):
        response = method(self.url + path, **kwargs)
        if response.status_code != 200:
            raise ApiException("Ошибка сервера: " + str(response.status_code), response.status_code, method_from)
        return json.loads(response.text) if response.text else None

    def get_deadlines(self, group_id: int, relevant=True) -> list[Deadline]:
        data = self._request(get, "deadlines", Service.get_deadlines,
                                 params={'relevant': relevant, 'groupId': group_id})
        if data["deadlines"] is None:
            return []
        return [Deadline.from_dict(it) for it in data["deadlines"]]

    def post_deadline(self, deadline: Deadline) -> Deadline:
        return Deadline.from_dict(self._request(post, "deadlines", Service.post_deadline, data=deadline.to_json()))

    def delete_deadline(self, id: int, groupId: int):
        self._request(delete, f"deadlines/{id}", Service.delete_deadline, params={'groupId': groupId})

    def get_schedule(self, groupId: int, algorithm: str = 'prioritySRTF') -> list[Deadline]:
        data = self._request(get, "schedule", Service.get_schedule, params={'groupId': groupId, 'algorithm': algorithm})
        if data["deadlines"] is None:
            return []
        return [Deadline.from_dict(it) for it in data["deadlines"]]

    def patch_deadline(self, id: int, data: dict) -> Deadline:
        return Deadline.from_dict(self._request(patch, f"deadlines/{id}", Service.patch_deadline, data=str(data)))

    def get_deadline(self, id: int) -> Deadline:
        return Deadline.from_dict(self._request(get, f"deadlines/{id}", Service.get_deadline))


service: Optional[Service] = Service(getenv('API_SERVICE_URL'))
