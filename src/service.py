import json

from requests import *

from deadline import Deadline
import logs


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

    def post_deadline(self, deadline: Deadline):
        self._request(post, "deadlines", Service.post_deadline, data=deadline.to_json())

    def delete_deadline(self, id: int, groupId: int):
        self._request(delete, "deadlines", Service.delete_deadline, params={'id': id, 'groupId': groupId})
